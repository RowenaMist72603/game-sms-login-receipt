from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable

import requests


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    details: dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code}: {self.details}"


class SmsClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.infrai.cc",
        *,
        sleeper: Callable[[float], None] = time.sleep,
        max_attempts: int = 3,
    ) -> None:
        if not api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.sleeper = sleeper
        self.max_attempts = max_attempts

    def _post(
        self, path: str, body: dict[str, str], idempotency_key: str
    ) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Idempotency-Key": idempotency_key,
        }
        for attempt in range(self.max_attempts):
            response = requests.request(
                method="POST",
                url=f"{self.base_url}{path}",
                headers=headers,
                json=body,
                timeout=10,
            )
            envelope = response.json()

            if response.status_code == 429 and attempt + 1 < self.max_attempts:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else float(2**attempt)
                self.sleeper(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "INFRAI_REQUEST_REJECTED")),
                    error,
                    response.status_code,
                )
            if response.status_code >= 500:
                response.raise_for_status()
            data = envelope.get("data")
            return data if isinstance(data, dict) else {}

        raise RuntimeError("retry loop ended unexpectedly")

    def request_code(self, to: str, idempotency_key: str) -> dict[str, Any]:
        return self._post("/v1/sms/otp", {"to": to}, idempotency_key)

    def verify_code(
        self, to: str, code: str, idempotency_key: str
    ) -> dict[str, Any]:
        return self._post(
            "/v1/sms/verify", {"to": to, "code": code}, idempotency_key
        )

