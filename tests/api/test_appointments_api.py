from __future__ import annotations


def test_book_appointment(
    api_client,
    cleanup_registry,
    authenticated_customer,
    random_service_payload,
    future_booking_time,
):
    service_payload = random_service_payload()

    cleanup_registry.track_service(service_name=service_payload["name"])

    service_response = api_client.create_service(service_payload)
    service = service_response.json()

    booking_response = api_client.book_appointment(
        authenticated_customer["token"],
        {
            "service_id": service["id"],
            "start_time": future_booking_time(hour=11, minute=0),
            "notes": "API appointment booking test",
        },
    )

    assert booking_response.status_code == 200
    body = booking_response.json()
    assert body["service_id"] == service["id"]
    assert body["service_name"] == service_payload["name"]
    assert body["customer_email"] == authenticated_customer["email"]
    assert body["customer_name"] == authenticated_customer["full_name"]
    assert body["status"] == "pending"
    assert body["notes"] == "API appointment booking test"
    assert "id" in body


def test_get_my_appointments(
    api_client,
    cleanup_registry,
    authenticated_customer,
    random_service_payload,
    future_booking_time,
):
    service_payload = random_service_payload()

    cleanup_registry.track_service(service_name=service_payload["name"])

    service_response = api_client.create_service(service_payload)
    service = service_response.json()

    create_response = api_client.book_appointment(
        authenticated_customer["token"],
        {
            "service_id": service["id"],
            "start_time": future_booking_time(hour=12, minute=0),
            "notes": "API appointment list test",
        },
    )
    appointment = create_response.json()

    response = api_client.get_my_appointments(authenticated_customer["token"])

    assert response.status_code == 200
    appointments = response.json()
    assert isinstance(appointments, list)
    assert any(item["id"] == appointment["id"] for item in appointments)

    matched_appointment = next(item for item in appointments if item["id"] == appointment["id"])
    assert matched_appointment["customer_email"] == authenticated_customer["email"]
    assert matched_appointment["service_id"] == service["id"]
    assert matched_appointment["service_name"] == service_payload["name"]
    assert matched_appointment["status"] == "pending"


def test_book_appointment_with_unknown_service(api_client, authenticated_customer, future_booking_time):
    response = api_client.book_appointment(
        authenticated_customer["token"],
        {
            "service_id": 99999999,
            "start_time": future_booking_time(hour=11, minute=30),
            "notes": "Unknown service negative test",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Service not found"


def test_book_appointment_in_the_past(api_client, cleanup_registry, authenticated_customer, random_service_payload):
    service_payload = random_service_payload()
    cleanup_registry.track_service(service_name=service_payload["name"])
    service = api_client.create_service(service_payload).json()

    response = api_client.book_appointment(
        authenticated_customer["token"],
        {
            "service_id": service["id"],
            "start_time": "2000-01-01T10:00:00",
            "notes": "Past booking negative test",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot book in the past"


def test_book_overlapping_appointment_returns_conflict(
    api_client,
    cleanup_registry,
    authenticated_customer,
    authenticated_customer_two,
    random_service_payload,
    future_booking_time,
):
    service_payload = random_service_payload()
    cleanup_registry.track_service(service_name=service_payload["name"])

    service = api_client.create_service(service_payload).json()
    start_time = future_booking_time(hour=13, minute=0)

    first_booking = api_client.book_appointment(
        authenticated_customer["token"],
        {
            "service_id": service["id"],
            "start_time": start_time,
            "notes": "First appointment",
        },
    )
    assert first_booking.status_code == 200

    overlapping_booking = api_client.book_appointment(
        authenticated_customer_two["token"],
        {
            "service_id": service["id"],
            "start_time": start_time,
            "notes": "Overlapping appointment",
        },
    )

    assert overlapping_booking.status_code == 409
    assert overlapping_booking.json()["detail"] == "Time slot already booked"


def test_get_my_appointments_requires_authentication(api_client):
    response = api_client.get_my_appointments(token="")

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_customer_cannot_view_owner_appointments(
    api_client,
    authenticated_customer,
):
    response = api_client.get_owner_appointments(authenticated_customer["token"])

    assert response.status_code == 403
    assert response.json()["detail"] == "Only owners can view all appointments"


def test_owner_can_view_all_appointments(
    api_client,
    cleanup_registry,
    authenticated_customer,
    random_service_payload,
    future_booking_time,
    authenticated_owner,
):
    service_payload = random_service_payload()

    cleanup_registry.track_service(service_name=service_payload["name"])

    service = api_client.create_service(service_payload).json()
    created_appointment = api_client.book_appointment(
        authenticated_customer["token"],
        {
            "service_id": service["id"],
            "start_time": future_booking_time(hour=14, minute=0),
            "notes": "Owner visibility test",
        },
    ).json()

    response = api_client.get_owner_appointments(authenticated_owner["token"])

    assert response.status_code == 200
    appointments = response.json()
    assert isinstance(appointments, list)
    assert any(item["id"] == created_appointment["id"] for item in appointments)
