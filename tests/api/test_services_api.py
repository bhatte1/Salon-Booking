from __future__ import annotations


def test_get_services(api_client, cleanup_registry, random_service_payload):
    payload = random_service_payload()
    cleanup_registry.track_service(service_name=payload["name"])
    create_response = api_client.create_service(payload)

    assert create_response.status_code == 200
    created_service = create_response.json()
    assert created_service["name"] == payload["name"]
    assert created_service["price_cents"] == payload["price_cents"]
    assert created_service["duration_minutes"] == payload["duration_minutes"]

    response = api_client.get_services()

    assert response.status_code == 200
    services = response.json()
    assert isinstance(services, list)
    assert any(service["id"] == created_service["id"] for service in services)

    matched_service = next(service for service in services if service["id"] == created_service["id"])
    assert matched_service["name"] == payload["name"]
    assert matched_service["price_cents"] == payload["price_cents"]
    assert matched_service["duration_minutes"] == payload["duration_minutes"]
