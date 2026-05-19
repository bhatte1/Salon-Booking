from __future__ import annotations

import re


BCRYPT_HASH_PATTERN = re.compile(r"^\$2[aby]\$\d{2}\$.{53}$")


def test_customer_signup_persists_in_database(
    api_client,
    db_client,
    cleanup_registry,
    random_customer_payload,
):
    payload = random_customer_payload()
    cleanup_registry.track_user(email=payload["email"], username=payload["username"])

    signup_response = api_client.signup_customer(payload)

    assert signup_response.status_code == 200
    created_user = db_client.get_user_by_username(payload["username"])

    assert created_user is not None
    assert created_user["full_name"] == payload["full_name"]
    assert created_user["username"] == payload["username"]
    assert created_user["email"] == payload["email"]
    assert created_user["role"] == "customer"
    assert created_user["is_active"] is True
    assert created_user["hashed_password"] != payload["password"]
    assert BCRYPT_HASH_PATTERN.match(created_user["hashed_password"])


def test_book_appointment_persists_correct_relationships(
    api_client,
    db_client,
    cleanup_registry,
    random_customer_payload,
    random_service_payload,
    future_booking_time,
    create_customer_and_login,
):
    customer_payload = random_customer_payload()
    service_payload = random_service_payload()

    cleanup_registry.track_service(service_name=service_payload["name"])
    customer = create_customer_and_login(customer_payload)

    create_service_response = api_client.create_service(service_payload)
    assert create_service_response.status_code == 200

    service = db_client.get_service_by_name(service_payload["name"])
    assert service is not None

    booking_response = api_client.book_appointment(
        customer["token"],
        {
            "service_id": service["id"],
            "start_time": future_booking_time(hour=15, minute=0),
            "notes": "Database persistence validation",
        },
    )

    assert booking_response.status_code == 200
    appointment_id = booking_response.json()["id"]
    appointment = db_client.get_appointment_by_id(appointment_id)
    latest_joined = db_client.get_appointment_with_user_and_service_join_by_id(appointment_id)
    customer_row = db_client.get_user_by_username(customer_payload["username"])

    assert appointment is not None
    assert latest_joined is not None
    assert customer_row is not None

    assert appointment["user_id"] == customer_row["id"]
    assert appointment["service_id"] == service["id"]
    assert appointment["customer_name"] == customer_payload["full_name"]
    assert appointment["customer_email"] == customer_payload["email"]
    assert appointment["status"] == "pending"
    assert appointment["notes"] == "Database persistence validation"

    assert latest_joined["appointment_id"] == appointment["id"]
    assert latest_joined["appointment_user_id"] == customer_row["id"]
    assert latest_joined["appointment_service_id"] == service["id"]
    assert latest_joined["user_id"] == customer_row["id"]
    assert latest_joined["username"] == customer_payload["username"]
    assert latest_joined["full_name"] == customer_payload["full_name"]
    assert latest_joined["user_email"] == customer_payload["email"]
    assert latest_joined["role"] == "customer"
    assert latest_joined["is_active"] is True
    assert latest_joined["customer_name"] == customer_payload["full_name"]
    assert latest_joined["customer_email"] == customer_payload["email"]
    assert latest_joined["service_id"] == service["id"]
    assert latest_joined["service_name"] == service_payload["name"]
    assert latest_joined["status"] == "pending"
    assert latest_joined["notes"] == "Database persistence validation"
    assert int(latest_joined["appointment_duration_minutes"]) == service["duration_minutes"]


def test_owner_status_update_persists_in_database(
    api_client,
    db_client,
    cleanup_registry,
    random_customer_payload,
    random_service_payload,
    future_booking_time,
    create_customer_and_login,
    create_owner_and_login,
):
    customer_payload = random_customer_payload()
    service_payload = random_service_payload()

    cleanup_registry.track_service(service_name=service_payload["name"])

    customer = create_customer_and_login(customer_payload)
    owner = create_owner_and_login()

    create_service_response = api_client.create_service(service_payload)
    assert create_service_response.status_code == 200

    service = db_client.get_service_by_name(service_payload["name"])
    assert service is not None

    booking_response = api_client.book_appointment(
        customer["token"],
        {
            "service_id": service["id"],
            "start_time": future_booking_time(hour=16, minute=0),
            "notes": "Owner status update validation",
        },
    )
    assert booking_response.status_code == 200
    appointment_id = booking_response.json()["id"]

    update_response = api_client.update_appointment_status(
        owner["token"],
        appointment_id,
        "completed",
    )
    assert update_response.status_code == 200

    appointment = db_client.get_appointment_by_id(appointment_id)
    joined_appointment = db_client.get_appointment_with_user_and_service_join_by_id(appointment_id)

    assert appointment is not None
    assert joined_appointment is not None
    assert appointment["status"] == "completed"
    assert joined_appointment["status"] == "completed"
    assert joined_appointment["username"] == customer_payload["username"]
    assert joined_appointment["service_name"] == service_payload["name"]
