"""POST /api/auth/login — password check and JWT issuance."""

from __future__ import annotations

from typing import Any

from auth import login_response


def handler(event: dict[str, Any], _context: object) -> dict[str, Any]:
    return login_response(event.get("body", ""))
