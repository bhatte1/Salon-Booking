from __future__ import annotations


def test_customer_signup(api_client, cleanup_registry, random_customer_payload):
    payload = random_customer_payload()
    cleanup_registry.track_user(email=payload["email"], username=payload["username"])

    response = api_client.signup_customer(payload)

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == payload["email"]
    assert body["username"] == payload["username"]
    assert body["full_name"] == payload["full_name"]
    assert body["role"] == "customer"
    assert body["is_active"] is True
    assert "id" in body


def test_customer_login(api_client, cleanup_registry, random_customer_payload):
    payload = random_customer_payload()
    cleanup_registry.track_user(email=payload["email"], username=payload["username"])
    api_client.signup_customer(payload)

    response = api_client.login_customer(payload["username"], payload["password"])

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == payload["email"]
    assert body["user"]["username"] == payload["username"]
    assert body["user"]["role"] == "customer"


def test_invalid_login(api_client):
    response = api_client.login_customer("missing-user@example.com", "WrongPass123!")

    assert response.status_code == 401
    body = response.json()
    assert body["detail"] == "Invalid credentials"


def test_get_current_user_with_jwt_token(api_client, authenticated_customer):
    response = api_client.get_current_user(authenticated_customer["token"])

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == authenticated_customer["email"]
    assert body["username"] == authenticated_customer["username"]
    assert body["role"] == "customer"


def test_owner_login(api_client, seed_owner_user):
    owner = seed_owner_user()

    response = api_client.login_owner(owner["username"], owner["password"])

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == owner["email"]
    assert body["user"]["username"] == owner["username"]
    assert body["user"]["role"] == "owner"
