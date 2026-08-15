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

# Checking out a book creates an active loan and decrements available_copies
def test_checkout_book_decrements_available_copies(client):
    book, customer = setup_book_and_customer(client, total_copies=3)

    respond = client.post("/api/loans", json={"book_id": book["id"], "customer_id": customer["id"]})
    assert respond.status_code == 201
    body = respond.get_json()
    assert body["status"] == "active"
    assert body["return_date"] is None
    assert body["due_date"]

    updated_book = client.get(f"/api/books/{book['id']}").get_json()
    assert updated_book["available_copies"] == 2

# Blocks checking out without book_id/customer_id
def test_checkout_missing_fields(client):
    respond = client.post("/api/loans", json={})
    assert respond.status_code == 400

# Blocks checking out a book that doesn't exist
def test_checkout_unknown_book(client):
    _, customer = setup_book_and_customer(client)
    respond = client.post("/api/loans", json={"book_id": 999, "customer_id": customer["id"]})
    assert respond.status_code == 404

# Blocks checking out to a customer that doesn't exist
def test_checkout_unknown_customer(client):
    book, _ = setup_book_and_customer(client)
    respond = client.post("/api/loans", json={"book_id": book["id"], "customer_id": 999})
    assert respond.status_code == 404

# Blocks checkout when no copies are available
def test_checkout_no_available_copies(client):
    book, customer = setup_book_and_customer(client, total_copies=1)
    client.post("/api/loans", json={"book_id": book["id"], "customer_id": customer["id"]})

    other_customer = client.post(
        "/api/customers",
        json={"first_name": "Charles", "last_name": "Babbage", "email": "babbage@example.com"},
    ).get_json()
    respond = client.post("/api/loans", json={"book_id": book["id"], "customer_id": other_customer["id"]})
    assert respond.status_code == 409

# Returning a book marks the loan returned and increments available_copies
def test_return_book_increments_available_copies(client):
    book, customer = setup_book_and_customer(client, total_copies=1)
    loan = client.post("/api/loans", json={"book_id": book["id"], "customer_id": customer["id"]}).get_json()

    respond = client.post(f"/api/loans/{loan['id']}/return")
    assert respond.status_code == 200
    body = respond.get_json()
    assert body["status"] == "returned"
    assert body["return_date"]

    updated_book = client.get(f"/api/books/{book['id']}").get_json()
    assert updated_book["available_copies"] == 1

# Test that returning a loan that does not exist returns a 404
def test_return_loan_not_found(client):
    respond = client.post("/api/loans/999/return")
    assert respond.status_code == 404

# Blocks returning a loan that's already been returned
def test_return_already_returned_loan(client):
    book, customer = setup_book_and_customer(client)
    loan = client.post("/api/loans", json={"book_id": book["id"], "customer_id": customer["id"]}).get_json()
    client.post(f"/api/loans/{loan['id']}/return")

    respond = client.post(f"/api/loans/{loan['id']}/return")
    assert respond.status_code == 409

# Filters the loan list down to a single customer's loans
def test_list_loans_filter_by_customer_id(client):
    book, customer = setup_book_and_customer(client, total_copies=2)
    other_customer = client.post(
        "/api/customers",
        json={"first_name": "Charles", "last_name": "Babbage", "email": "babbage@example.com"},
    ).get_json()
    client.post("/api/loans", json={"book_id": book["id"], "customer_id": customer["id"]})
    client.post("/api/loans", json={"book_id": book["id"], "customer_id": other_customer["id"]})

    respond = client.get(f"/api/loans?customer_id={customer['id']}")
    assert respond.status_code == 200
    body = respond.get_json()
    assert len(body) == 1
    assert body[0]["customer_id"] == customer["id"]

# Filters the loan list down to active or returned loans
def test_list_loans_filter_by_status(client):
    book, customer = setup_book_and_customer(client, total_copies=1)
    loan = client.post("/api/loans", json={"book_id": book["id"], "customer_id": customer["id"]}).get_json()
    client.post(f"/api/loans/{loan['id']}/return")

    active = client.get("/api/loans?status=active").get_json()
    returned = client.get("/api/loans?status=returned").get_json()
    assert active == []
    assert len(returned) == 1
    assert returned[0]["id"] == loan["id"]

# Create a loan and fetch it by ID
def test_get_loan_by_id(client):
    book, customer = setup_book_and_customer(client)
    loan = client.post("/api/loans", json={"book_id": book["id"], "customer_id": customer["id"]}).get_json()

    respond = client.get(f"/api/loans/{loan['id']}")
    assert respond.status_code == 200
    assert respond.get_json()["id"] == loan["id"]

# Test fetching a loan that does not exist returns 404
def test_get_loan_not_found(client):
    respond = client.get("/api/loans/999")
    assert respond.status_code == 404

def register_customer(client, first_name="Grace", last_name="Hopper", email="grace@example.com"):
    return client.post("/api/auth/register", json={
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password": "password123",
    }).get_json()

# A logged-in customer can't check a book out for someone else by spoofing customer_id
def test_checkout_ignores_client_supplied_customer_id_when_logged_in(client):
    book, other_customer = setup_book_and_customer(client, total_copies=2)

    logged_in_customer = register_customer(client)

    respond = client.post("/api/loans", json={"book_id": book["id"], "customer_id": other_customer["id"]})
    assert respond.status_code == 201
    assert respond.get_json()["customer_id"] == logged_in_customer["id"]

# A logged-in customer can't return another customer's loan
def test_return_another_customers_loan_is_forbidden_when_logged_in(client):
    book, customer = setup_book_and_customer(client, total_copies=1)
    loan = client.post("/api/loans", json={"book_id": book["id"], "customer_id": customer["id"]}).get_json()

    register_customer(client)

    respond = client.post(f"/api/loans/{loan['id']}/return")
    assert respond.status_code == 403

# A logged-in customer can't list another customer's loans
def test_list_loans_for_another_customer_is_forbidden_when_logged_in(client):
    book, other_customer = setup_book_and_customer(client, total_copies=1)

    register_customer(client)

    respond = client.get(f"/api/loans?customer_id={other_customer['id']}")
    assert respond.status_code == 403

# With no session at all (the admin/staff flow), an explicit customer_id still works
def test_checkout_without_session_still_honors_explicit_customer_id(client):
    book, customer = setup_book_and_customer(client, total_copies=1)
    respond = client.post("/api/loans", json={"book_id": book["id"], "customer_id": customer["id"]})
    assert respond.status_code == 201
    assert respond.get_json()["customer_id"] == customer["id"]
