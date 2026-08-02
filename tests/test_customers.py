def create_customer(client, **overrides):
    payload = {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada@example.com",
        "phone": "555-1234",
    }
    payload.update(overrides)
    return client.post("/api/customers", json=payload)


def test_get_customers_empty(client):
    resp = client.get("/api/customers")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_create_customer(client):
    resp = create_customer(client)
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["email"] == "ada@example.com"
    assert body["membership_date"]


def test_create_customer_missing_fields(client):
    resp = client.post("/api/customers", json={"first_name": "Ada"})
    assert resp.status_code == 400


def test_create_customer_duplicate_email(client):
    create_customer(client)
    resp = create_customer(client, first_name="Charles", last_name="Babbage")
    assert resp.status_code == 409


def test_create_customer_bad_membership_date(client):
    resp = create_customer(client, membership_date="not-a-date")
    assert resp.status_code == 400


def test_create_customer_explicit_membership_date(client):
    resp = create_customer(client, membership_date="2020-01-15")
    assert resp.status_code == 201
    assert resp.get_json()["membership_date"] == "2020-01-15"


def test_get_customer_by_id(client):
    created = create_customer(client).get_json()
    resp = client.get(f"/api/customers/{created['id']}")
    assert resp.status_code == 200
    assert resp.get_json()["last_name"] == "Lovelace"


def test_get_customer_not_found(client):
    assert client.get("/api/customers/999").status_code == 404


def test_update_customer(client):
    created = create_customer(client).get_json()
    resp = client.patch(f"/api/customers/{created['id']}", json={"phone": "555-9999"})
    assert resp.status_code == 200
    assert resp.get_json()["phone"] == "555-9999"


def test_update_customer_duplicate_email(client):
    create_customer(client)
    other = create_customer(client, email="babbage@example.com", first_name="Charles", last_name="Babbage").get_json()
    resp = client.patch(f"/api/customers/{other['id']}", json={"email": "ada@example.com"})
    assert resp.status_code == 409


def test_update_customer_not_found(client):
    resp = client.patch("/api/customers/999", json={"phone": "555-0000"})
    assert resp.status_code == 404


def test_delete_customer(client):
    created = create_customer(client).get_json()
    resp = client.delete(f"/api/customers/{created['id']}")
    assert resp.status_code == 204
    assert client.get(f"/api/customers/{created['id']}").status_code == 404


def test_delete_customer_not_found(client):
    assert client.delete("/api/customers/999").status_code == 404

# Not working
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
    client.post("/api/loans", json={"book_id": book["id"], "customer_id": customer["id"]})

    resp = client.delete(f"/api/customers/{customer['id']}")
    assert resp.status_code == 409
