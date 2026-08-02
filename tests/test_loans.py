def setup_book_and_customer(client, total_copies=1):
    category = client.post("/api/categories", json={"name": "Fiction"}).get_json()
    book = client.post(
        "/api/books",
        json={
            "title": "Dune",
            "author": "Frank Herbert",
            "isbn": "9780441013593",
            "category_id": category["id"],
            "total_copies": total_copies,
        },
    ).get_json()
    customer = client.post(
        "/api/customers",
        json={"first_name": "Ada", "last_name": "Lovelace", "email": "ada@example.com"},
    ).get_json()
    return book, customer


def test_checkout_book_decrements_available_copies(client):
    book, customer = setup_book_and_customer(client, total_copies=3)

    resp = client.post("/loans", json={"book_id": book["id"], "customer_id": customer["id"]})
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["status"] == "active"
    assert body["return_date"] is None
    assert body["due_date"]

    updated_book = client.get(f"/api/books/{book['id']}").get_json()
    assert updated_book["available_copies"] == 2


def test_checkout_missing_fields(client):
    resp = client.post("/loans", json={})
    assert resp.status_code == 400


def test_checkout_unknown_book(client):
    _, customer = setup_book_and_customer(client)
    resp = client.post("/loans", json={"book_id": 999, "customer_id": customer["id"]})
    assert resp.status_code == 404


def test_checkout_unknown_customer(client):
    book, _ = setup_book_and_customer(client)
    resp = client.post("/loans", json={"book_id": book["id"], "customer_id": 999})
    assert resp.status_code == 404


def test_checkout_no_available_copies(client):
    book, customer = setup_book_and_customer(client, total_copies=1)
    client.post("/loans", json={"book_id": book["id"], "customer_id": customer["id"]})

    other_customer = client.post(
        "/api/customers",
        json={"first_name": "Charles", "last_name": "Babbage", "email": "babbage@example.com"},
    ).get_json()
    resp = client.post("/loans", json={"book_id": book["id"], "customer_id": other_customer["id"]})
    assert resp.status_code == 409


def test_return_book_increments_available_copies(client):
    book, customer = setup_book_and_customer(client, total_copies=1)
    loan = client.post("/loans", json={"book_id": book["id"], "customer_id": customer["id"]}).get_json()

    resp = client.post(f"/loans/{loan['id']}/return")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "returned"
    assert body["return_date"]

    updated_book = client.get(f"/api/books/{book['id']}").get_json()
    assert updated_book["available_copies"] == 1


def test_return_loan_not_found(client):
    resp = client.post("/loans/999/return")
    assert resp.status_code == 404


def test_return_already_returned_loan(client):
    book, customer = setup_book_and_customer(client)
    loan = client.post("/loans", json={"book_id": book["id"], "customer_id": customer["id"]}).get_json()
    client.post(f"/loans/{loan['id']}/return")

    resp = client.post(f"/loans/{loan['id']}/return")
    assert resp.status_code == 409


def test_list_loans_filter_by_customer_id(client):
    book, customer = setup_book_and_customer(client, total_copies=2)
    other_customer = client.post(
        "/api/customers",
        json={"first_name": "Charles", "last_name": "Babbage", "email": "babbage@example.com"},
    ).get_json()
    client.post("/loans", json={"book_id": book["id"], "customer_id": customer["id"]})
    client.post("/loans", json={"book_id": book["id"], "customer_id": other_customer["id"]})

    resp = client.get(f"/loans?customer_id={customer['id']}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert len(body) == 1
    assert body[0]["customer_id"] == customer["id"]


def test_list_loans_filter_by_status(client):
    book, customer = setup_book_and_customer(client, total_copies=1)
    loan = client.post("/loans", json={"book_id": book["id"], "customer_id": customer["id"]}).get_json()
    client.post(f"/loans/{loan['id']}/return")

    active = client.get("/loans?status=active").get_json()
    returned = client.get("/loans?status=returned").get_json()
    assert active == []
    assert len(returned) == 1
    assert returned[0]["id"] == loan["id"]


def test_get_loan_by_id(client):
    book, customer = setup_book_and_customer(client)
    loan = client.post("/loans", json={"book_id": book["id"], "customer_id": customer["id"]}).get_json()

    resp = client.get(f"/loans/{loan['id']}")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == loan["id"]


def test_get_loan_not_found(client):
    resp = client.get("/loans/999")
    assert resp.status_code == 404
