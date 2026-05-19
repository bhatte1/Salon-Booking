from __future__ import annotations

from typing import Any

from tests.db import queries


class DBClient:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def _fetchone(self, query: str, params: tuple[Any, ...]) -> dict[str, Any] | None:
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(self.database_url, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchone()

    def _fetchall(self, query: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(self.database_url, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return list(cur.fetchall())

    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        return self._fetchone(queries.GET_USER_BY_USERNAME, (username,))

    def get_service_by_name(self, service_name: str) -> dict[str, Any] | None:
        return self._fetchone(queries.GET_SERVICE_BY_NAME, (service_name,))

    def get_appointment_by_customer_username(self, username: str) -> dict[str, Any] | None:
        return self._fetchone(queries.GET_APPOINTMENT_BY_CUSTOMER_USERNAME, (username,))

    def get_appointment_by_id(self, appointment_id: int) -> dict[str, Any] | None:
        return self._fetchone(queries.GET_APPOINTMENT_BY_ID, (appointment_id,))

    def get_appointments_with_user_and_service_join(self, username: str) -> list[dict[str, Any]]:
        return self._fetchall(queries.GET_APPOINTMENTS_WITH_USER_AND_SERVICE_JOIN, (username,))

    def get_appointment_with_user_and_service_join_by_id(
        self,
        appointment_id: int,
    ) -> dict[str, Any] | None:
        return self._fetchone(queries.GET_APPOINTMENT_WITH_USER_AND_SERVICE_JOIN_BY_ID, (appointment_id,))
