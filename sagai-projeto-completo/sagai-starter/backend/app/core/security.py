from __future__ import annotations

import secrets

from fastapi import Header, HTTPException, status

from app.config.settings import get_settings


def validate_admin_key(x_admin_key: str | None = Header(default=None)) -> None:
    settings = get_settings()

    if not x_admin_key or not secrets.compare_digest(x_admin_key, settings.admin_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Admin-Key",
        )
