from conftest import CUSTOMER_PASSWORD


# Successful login returns the customer's own record and starts a session
def test_login_success_returns_own_record_and_sets_session(client, customer):
    respond = client.post("/api/auth/login", json={"email": "ada@example.com", "password": CUSTOMER_PASSWORD})
    assert respond.status_code == 200
    body = respond.get_json()
    assert body["first_name"] == "Ada"
    assert body["last_name"] == "Lovelace"
    assert "email" in body
    assert "password_hash" not in body

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.get_json()["id"] == body["id"]

# Wrong password is rejected
def test_login_wrong_password_fails(client, customer):
    respond = client.post("/api/auth/login", json={"email": "ada@example.com", "password": "wrong"})
    assert respond.status_code == 401

# Unknown email is rejected
def test_login_unknown_email_fails(client, customer):
    respond = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": CUSTOMER_PASSWORD})
    assert respond.status_code == 401

# Missing email/password fields are rejected
def test_login_missing_fields_fails(client):
    assert client.post("/api/auth/login", json={}).status_code == 400
    assert client.post("/api/auth/login", json={"email": "ada@example.com"}).status_code == 400
    assert client.post("/api/auth/login", json={"password": CUSTOMER_PASSWORD}).status_code == 400

# Email matching is case-insensitive
def test_login_email_is_case_insensitive(client, customer):
    respond = client.post("/api/auth/login", json={"email": "ADA@EXAMPLE.COM", "password": CUSTOMER_PASSWORD})
    assert respond.status_code == 200

# Password matching is case-sensitive
def test_login_password_is_case_sensitive(client, customer):
    respond = client.post("/api/auth/login", json={"email": "ada@example.com", "password": CUSTOMER_PASSWORD.upper()})
    assert respond.status_code == 401

# Logging out clears the session
def test_logout_clears_session(client, customer):
    client.post("/api/auth/login", json={"email": "ada@example.com", "password": CUSTOMER_PASSWORD})
    respond = client.post("/api/auth/logout")
    assert respond.status_code == 204
    assert client.get("/api/auth/me").status_code == 401

# /api/auth/me with no session is unauthorized
def test_me_without_session_is_401(client):
    assert client.get("/api/auth/me").status_code == 401

# Registering creates a customer and immediately starts a session
def test_register_creates_customer_and_auto_logs_in(client):
    respond = client.post("/api/auth/register", json={
        "first_name": "Grace", "last_name": "Hopper",
        "email": "grace@example.com", "password": "password123",
    })
    assert respond.status_code == 201
    assert respond.get_json()["email"] == "grace@example.com"
    assert client.get("/api/auth/me").status_code == 200

# Registering with an email that's already taken fails
def test_register_duplicate_email_fails_with_409(client, customer):
    respond = client.post("/api/auth/register", json={
        "first_name": "Someone", "last_name": "Else",
        "email": "ada@example.com", "password": "password123",
    })
    assert respond.status_code == 409

# Missing fields are rejected
def test_register_missing_fields_fails(client):
    assert client.post("/api/auth/register", json={}).status_code == 400

# A too-short password is rejected
def test_register_short_password_fails(client):
    respond = client.post("/api/auth/register", json={
        "first_name": "Grace", "last_name": "Hopper",
        "email": "grace@example.com", "password": "short",
    })
    assert respond.status_code == 400
