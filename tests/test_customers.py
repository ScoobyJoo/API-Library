# Create dummy customer
def create_customer(client, **overrides):
    payload = {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada@example.com",
        "phone": "555-1234",
    }
    payload.update(overrides)
    return client.post("/api/customers", json=payload)

# Confirms empty list returns 200
def test_get_customers_empty(client):
    resp = client.get("/api/customers")
    assert resp.status_code == 200
    assert resp.get_json() == []

# Confirms creating a customer returns 201
def test_create_customer(client):
    resp = create_customer(client)
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["email"] == "ada@example.com"
    assert body["membership_date"]

# Blocks creating a customer with missing fields
def test_create_customer_missing_fields(client):
    resp = client.post("/api/customers", json={"first_name": "Ada"})
    assert resp.status_code == 400

# Blocks creating a customer with duplicate email
def test_create_customer_duplicate_email(client):
    create_customer(client)
    resp = create_customer(client, first_name="Charles", last_name="Babbage")
    assert resp.status_code == 409

# Blocks invalid date format for membership_date
def test_create_customer_bad_membership_date(client):
    resp = create_customer(client, membership_date="not-a-date")
    assert resp.status_code == 400

# Test creating a customer with an explicit membership date
def test_create_customer_explicit_membership_date(client):
    resp = create_customer(client, membership_date="2020-01-15")
    assert resp.status_code == 201
    assert resp.get_json()["membership_date"] == "2020-01-15"

# Create a customer and fetch it by ID
def test_get_customer_by_id(client):
    created = create_customer(client).get_json()
    resp = client.get(f"/api/customers/{created['id']}")
    assert resp.status_code == 200
    assert resp.get_json()["last_name"] == "Lovelace"

# Test fetching a customer that does not exist returns 404
def test_get_customer_not_found(client):
    assert client.get("/api/customers/999").status_code == 404

# Update cusomter phone number
def test_update_customer(client):
    created = create_customer(client).get_json()
    resp = client.patch(f"/api/customers/{created['id']}", json={"phone": "555-9999"})
    assert resp.status_code == 200
    assert resp.get_json()["phone"] == "555-9999"

# Creates a customer with a duplicate email and checks that the update is blocked
def test_update_customer_duplicate_email(client):
    create_customer(client)
    other = create_customer(client, email="babbage@example.com", first_name="Charles", last_name="Babbage").get_json()
    resp = client.patch(f"/api/customers/{other['id']}", json={"email": "ada@example.com"})
    assert resp.status_code == 409

# Test that updating a customer that does not exist returns a 404
def test_update_customer_not_found(client):
    resp = client.patch("/api/customers/999", json={"phone": "555-0000"})
    assert resp.status_code == 404

# Delete a customer
def test_delete_customer(client):
    created = create_customer(client).get_json()
    resp = client.delete(f"/api/customers/{created['id']}")
    assert resp.status_code == 204
    assert client.get(f"/api/customers/{created['id']}").status_code == 404

# Delete a customer that does not exist
def test_delete_customer_not_found(client):
    assert client.delete("/api/customers/999").status_code == 404

# Test that deleting a customer with an active loan is blocked
def test_delete_customer_with_active_loan_is_blocked(client):
    category = client.post("/api/categories", json={"name": "Fiction"}).get_json()
    book = client.post(
        "/api/books",
        json={
            "title": "Dune",
            "author": "Frank Herbert",
            "isbn": "9780441013593",
            "category_id": category["id"],
            "total_copies": 1,
        },
    ).get_json()
    customer = create_customer(client).get_json()
    client.post("/loans", json={"book_id": book["id"], "customer_id": customer["id"]})

    resp = client.delete(f"/api/customers/{customer['id']}")
    assert resp.status_code == 409
