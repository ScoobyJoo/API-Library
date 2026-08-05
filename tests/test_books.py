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

# Confirms empty list returns 200
def test_get_books_empty(client):
    respond = client.get("/api/books")
    assert respond.status_code == 200
    assert respond.get_json() == []

# Confirms creating a book returns 201
def test_create_book(client):
    category = create_category(client)
    respond = create_book(client, category["id"])
    assert respond.status_code == 201
    body = respond.get_json()
    assert body["title"] == "Dune"
    assert body["available_copies"] == 3

# Confirms available_copies defaults to total_copies when omitted
def test_create_book_defaults_available_copies_to_total(client):
    category = create_category(client)
    respond = client.post("/api/books", json={
        "title": "Dune",
        "author": "Frank Herbert",
        "isbn": "9780441013593",
        "category_id": category["id"],
        "total_copies": 5,
    })
    respond_body = respond.get_json()
    assert respond.status_code == 201
    assert respond_body["available_copies"] == 5

# Blocks creating a book missing required fields
def test_create_book_missing_required_fields(client):
    category = create_category(client)
    respond = client.post("/api/books", json={"title": "No Author", "category_id": category["id"]})
    assert respond.status_code == 400

# Blocks creating a book with a category that doesn't exist
def test_create_book_unknown_category(client):
    respond = create_book(client, category_id=999)
    assert respond.status_code == 404

# Blocks available_copies exceeding total_copies
def test_create_book_available_exceeds_total(client):
    category = create_category(client)
    respond = create_book(client, category["id"], total_copies=1, available_copies=2)
    assert respond.status_code == 400

# Blocks negative copy counts
def test_create_book_negative_copies(client):
    category = create_category(client)
    respond = create_book(client, category["id"], total_copies=-1, available_copies=0)
    assert respond.status_code == 400

# Blocks creating a book with a duplicate ISBN
def test_create_book_duplicate_isbn(client):
    category = create_category(client)
    create_book(client, category["id"])
    respond = create_book(client, category["id"], title="Dune Messiah")
    assert respond.status_code == 409

# Create a book and fetch it by ID
def test_get_book_by_id(client):
    category = create_category(client)
    created = create_book(client, category["id"]).get_json()
    respond = client.get(f"/api/books/{created['id']}")
    assert respond.status_code == 200
    assert respond.get_json()["isbn"] == "9780441013593"

# Test fetching a book that does not exist returns 404
def test_get_book_not_found(client):
    assert client.get("/api/books/999").status_code == 404

# Update a book's copy counts
def test_update_book(client):
    category = create_category(client)
    created = create_book(client, category["id"]).get_json()
    respond = client.patch(f"/api/books/{created['id']}", json={"total_copies": 5, "available_copies": 5})
    assert respond.status_code == 200
    assert respond.get_json()["total_copies"] == 5

# Blocks updating available_copies above total_copies
def test_update_book_available_exceeds_total(client):
    category = create_category(client)
    created = create_book(client, category["id"]).get_json()
    respond = client.patch(f"/api/books/{created['id']}", json={"available_copies": 99})
    assert respond.status_code == 400

# Blocks updating a book to a category that doesn't exist
def test_update_book_unknown_category(client):
    category = create_category(client)
    created = create_book(client, category["id"]).get_json()
    respond = client.patch(f"/api/books/{created['id']}", json={"category_id": 999})
    assert respond.status_code == 404

# Test that updating a book that does not exist returns a 404
def test_update_book_not_found(client):
    respond = client.patch("/api/books/999", json={"title": "Whatever"})
    assert respond.status_code == 404

# Delete a book
def test_delete_book(client):
    category = create_category(client)
    created = create_book(client, category["id"]).get_json()
    respond = client.delete(f"/api/books/{created['id']}")
    assert respond.status_code == 204
    assert client.get(f"/api/books/{created['id']}").status_code == 404

# Delete a book that does not exist
def test_delete_book_not_found(client):
    assert client.delete("/api/books/999").status_code == 404

# Test that deleting a book with an active loan is blocked
def test_delete_book_with_active_loan_is_blocked(client):
    category = create_category(client)
    book = create_book(client, category["id"]).get_json()
    customer = client.post(
        "/api/customers",
        json={"first_name": "Ada", "last_name": "Lovelace", "email": "ada@example.com"},
    ).get_json()
    client.post("/loans", json={"book_id": book["id"], "customer_id": customer["id"]})

    respond = client.delete(f"/api/books/{book['id']}")
    assert respond.status_code == 409
