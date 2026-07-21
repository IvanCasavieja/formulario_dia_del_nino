"""Salesforce Marketing Cloud REST API client: OAuth2 client-credentials auth against
an Installed Package, then a row insert into a Data Extension by External Key.

Endpoint/payload shape verified against Salesforce's published "Data Extension Rows
(Synchronous)" REST API and standard SFMC OAuth2 docs, but was never exercised against
a real tenant (no credentials existed at the time this was written) - double check
against your own package/API version before relying on it in production.
"""
import time

import httpx

from app.config import get_settings

settings = get_settings()

_token_cache: dict[str, float | str | None] = {"access_token": None, "expires_at": 0.0}


class SalesforceSyncError(Exception):
    pass


def _auth_base_url() -> str:
    return f"https://{settings.SFMC_SUBDOMAIN}.auth.marketingcloudapis.com"


def _rest_base_url() -> str:
    return f"https://{settings.SFMC_SUBDOMAIN}.rest.marketingcloudapis.com"


def _get_access_token() -> str:
    """Client-credentials grant. Tokens are cached in-process and reused until ~30s
    before expiry (SFMC tokens are typically valid ~20 minutes) - fine for a worker
    process handling one submission at a time; a shared cache across processes isn't
    worth the complexity at this volume."""
    now = time.monotonic()
    cached_token = _token_cache["access_token"]
    cached_expiry = _token_cache["expires_at"]
    if cached_token and isinstance(cached_expiry, (int, float)) and cached_expiry > now + 30:
        return str(cached_token)

    payload = {
        "grant_type": "client_credentials",
        "client_id": settings.SFMC_CLIENT_ID,
        "client_secret": settings.SFMC_CLIENT_SECRET,
    }
    if settings.SFMC_ACCOUNT_ID:
        payload["account_id"] = settings.SFMC_ACCOUNT_ID

    try:
        response = httpx.post(
            f"{_auth_base_url()}/v2/token",
            json=payload,
            timeout=settings.SFMC_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise SalesforceSyncError(f"token request failed: {e}") from e

    data = response.json()
    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = now + float(data["expires_in"])
    return str(data["access_token"])


def insert_data_extension_row(fields: dict) -> None:
    """Inserts one row into the configured Data Extension.

    `fields` keys must match the Data Extension's column names exactly - SFMC doesn't
    fuzzy-match. See worker/salesforce_tasks.py for the submission -> fields mapping,
    which is the one place to adjust if the target Data Extension's schema differs.
    """
    if not settings.SFMC_ENABLED:
        raise SalesforceSyncError("SFMC_ENABLED is false - refusing to call a possibly-unconfigured integration")

    token = _get_access_token()
    url = f"{_rest_base_url()}/data/v1/customobjectdata/key/{settings.SFMC_DATA_EXTENSION_KEY}/rowset"

    try:
        response = httpx.post(
            url,
            json=[{"values": fields}],
            headers={"Authorization": f"Bearer {token}"},
            timeout=settings.SFMC_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.HTTPError as e:
        detail = e.response.text if isinstance(e, httpx.HTTPStatusError) else str(e)
        raise SalesforceSyncError(f"row insert failed: {detail}") from e
