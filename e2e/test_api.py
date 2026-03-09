from __future__ import annotations

import requests

from e2e.utils import api_url, cleanup_by_email_and_service, future_iso, unique_marker


def test_api_create_and_overlap_conflict():
    marker = unique_marker("api")
    service_name = f"E2E Service {marker}"
    email_a = f"qa+{marker}-a@example.com"
    email_b = f"qa+{marker}-b@example.com"

    try:
        service_res = requests.post(
            f"{api_url()}/api/services",
            json={"name": service_name, "price_cents": 4500, "duration_minutes": 45},
            timeout=10,
        )
        assert service_res.status_code == 200
        service = service_res.json()

        payload = {
            "customer_name": f"API User {marker}",
            "customer_email": email_a,
            "service_id": service["id"],
            "start_time": future_iso(240),
            "notes": f"api-booking-{marker}",
        }

        create_res = requests.post(f"{api_url()}/api/appointments", json=payload, timeout=10)
        assert create_res.status_code == 200
        created = create_res.json()
        assert created["customer_email"] == email_a

        overlap_payload = {
            **payload,
            "customer_name": f"API User 2 {marker}",
            "customer_email": email_b,
        }
        overlap_res = requests.post(
            f"{api_url()}/api/appointments", json=overlap_payload, timeout=10
        )
        assert overlap_res.status_code == 409

        list_res = requests.get(f"{api_url()}/api/appointments", timeout=10)
        assert list_res.status_code == 200
        appointments = list_res.json()
        assert any(a["id"] == created["id"] for a in appointments)
    finally:
        cleanup_by_email_and_service(email=email_a, service_name=service_name)
        cleanup_by_email_and_service(email=email_b)
