from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import APIRequestContext, APIResponse


@dataclass
class ResponseWrapper:
    response: "APIResponse"

    @property
    def status_code(self) -> int:
        return self.response.status

    @property
    def ok(self) -> bool:
        return self.response.ok

    def json(self) -> Any:
        return self.response.json()

    def text(self) -> str:
        return self.response.text()


class APIClient:
    def __init__(self, request_context: "APIRequestContext") -> None:
        self.request_context = request_context

    def _request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> ResponseWrapper:
        headers: dict[str, str] = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        response = self.request_context.fetch(
            path,
            method=method,
            headers=headers,
            data=data,
            params=params,
            fail_on_status_code=False,
        )
        return ResponseWrapper(response=response)

    def get(self, path: str, *, token: str | None = None, params: dict[str, Any] | None = None) -> ResponseWrapper:
        return self._request("GET", path, token=token, params=params)

    def post(self, path: str, *, token: str | None = None, data: dict[str, Any] | None = None) -> ResponseWrapper:
        return self._request("POST", path, token=token, data=data)

    def signup_customer(self, payload: dict[str, Any]) -> ResponseWrapper:
        return self.post("/api/auth/signup/customer", data=payload)

    def login_customer(self, username_or_email: str, password: str) -> ResponseWrapper:
        return self.post(
            "/api/auth/login/customer",
            data={
                "username_or_email": username_or_email,
                "password": password,
            },
        )

    def login_owner(self, username_or_email: str, password: str) -> ResponseWrapper:
        return self.post(
            "/api/auth/login/owner",
            data={
                "username_or_email": username_or_email,
                "password": password,
            },
        )

    def get_current_user(self, token: str) -> ResponseWrapper:
        return self.get("/api/auth/me", token=token)

    def create_service(self, payload: dict[str, Any]) -> ResponseWrapper:
        return self.post("/api/services", data=payload)

    def get_services(self) -> ResponseWrapper:
        return self.get("/api/services")

    def book_appointment(self, token: str, payload: dict[str, Any]) -> ResponseWrapper:
        return self.post("/api/appointments/me", token=token, data=payload)

    def get_my_appointments(self, token: str) -> ResponseWrapper:
        return self.get("/api/appointments/me/list", token=token)

    def get_owner_appointments(self, token: str) -> ResponseWrapper:
        return self.get("/api/appointments/owner/all", token=token)

    def update_appointment_status(self, token: str, appointment_id: int, status: str) -> ResponseWrapper:
        return self._request(
            "PATCH",
            f"/api/appointments/owner/{appointment_id}/status",
            token=token,
            data={"status": status},
        )
