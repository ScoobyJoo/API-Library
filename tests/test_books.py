def create_category(client, name="Fiction"):
    return client.post("/api/categories", json={"name": name}).get_json()


def create_book(client, category_id, **overrides):
    payload = {
        "title": "Dune",
        "author": "Frank Herbert",
        "isbn": "9780441013593",
        "category_id": category_id,
        "total_copies": 3,
        "available_copies": 3,
        "published_year": 1965,
    }
    payload.update(overrides)
    return client.post("/api/books", json=payload)


def test_get_books_empty(client):
    resp = client.get("/api/books")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_create_book(client):
    category = create_category(client)
    resp = create_book(client, category["id"])
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["title"] == "Dune"
    assert body["available_copies"] == 3

# Not working
def test_create_book_defaults_available_copies_to_total(client):
    category = create_category(client)
    resp = create_book(client, category["id"], total_copies=5)
    resp_body = resp.get_json()
    assert resp.status_code == 201
    assert resp_body["available_copies"] == 5


def test_create_book_missing_required_fields(client):
    category = create_category(client)
    resp = client.post("/api/books", json={"title": "No Author", "category_id": category["id"]})
    assert resp.status_code == 400


def test_create_book_unknown_category(client):
    resp = create_book(client, category_id=999)
    assert resp.status_code == 404


def test_create_book_available_exceeds_total(client):
    category = create_category(client)
    resp = create_book(client, category["id"], total_copies=1, available_copies=2)
    assert resp.status_code == 400


def test_create_book_negative_copies(client):
    category = create_category(client)
    resp = create_book(client, category["id"], total_copies=-1, available_copies=0)
    assert resp.status_code == 400


def test_create_book_duplicate_isbn(client):
    category = create_category(client)
    create_book(client, category["id"])
    resp = create_book(client, category["id"], title="Dune Messiah")
    assert resp.status_code == 409


def test_get_book_by_id(client):
    category = create_category(client)
    created = create_book(client, category["id"]).get_json()
    resp = client.get(f"/api/books/{created['id']}")
    assert resp.status_code == 200
    assert resp.get_json()["isbn"] == "9780441013593"


def test_get_book_not_found(client):
    assert client.get("/api/books/999").status_code == 404


def test_update_book(client):
    category = create_category(client)
    created = create_book(client, category["id"]).get_json()
    resp = client.patch(f"/api/books/{created['id']}", json={"total_copies": 5, "available_copies": 5})
    assert resp.status_code == 200
    assert resp.get_json()["total_copies"] == 5


def test_update_book_available_exceeds_total(client):
    category = create_category(client)
    created = create_book(client, category["id"]).get_json()
    resp = client.patch(f"/api/books/{created['id']}", json={"available_copies": 99})
    assert resp.status_code == 400


def test_update_book_unknown_category(client):
    category = create_category(client)
    created = create_book(client, category["id"]).get_json()
    resp = client.patch(f"/api/books/{created['id']}", json={"category_id": 999})
    assert resp.status_code == 404


def test_update_book_not_found(client):
    resp = client.patch("/api/books/999", json={"title": "Whatever"})
    assert resp.status_code == 404


def test_delete_book(client):
    category = create_category(client)
    created = create_book(client, category["id"]).get_json()
    resp = client.delete(f"/api/books/{created['id']}")
    assert resp.status_code == 204
    assert client.get(f"/api/books/{created['id']}").status_code == 404


def test_delete_book_not_found(client):
    assert client.delete("/api/books/999").status_code == 404

# Not working 
def test_delete_book_with_active_loan_is_blocked(client):
    category = create_category(client)
    book = create_book(client, category["id"]).get_json()
    customer = client.post(
        "/api/customers",
        json={"first_name": "Ada", "last_name": "Lovelace", "email": "ada@example.com"},
    ).get_json()
    client.post("/api/loans", json={"book_id": book["id"], "customer_id": customer["id"]})

    resp = client.delete(f"/api/books/{book['id']}")
    assert resp.status_code == 409
