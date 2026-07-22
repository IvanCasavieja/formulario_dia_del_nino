"""Salesforce Marketing Cloud REST API client: OAuth2 client-credentials auth against
an Installed Package, then a row insert into a Data Extension by External Key.

Endpoint and payload shape verified live against the real tenant (Formulario_Nino
package, Formulario_Video_Nino DE) - see backend/scripts/test_salesforce_sync.py.
Two things that aren't obvious from Salesforce's docs and cost real trial and error:

- The row-insert endpoint is the *async* one (`/data/v1/async/dataextensions/key:...`).
  There's no working synchronous equivalent for this API generation - `.../data/v1/
  dataextensions/key:.../rows` (without "async") 404s, and the older `/data/v1/
  customobjectdata/key/.../rowset` only supports GET, not POST.
- Each item in "items" is the field values directly (`{"ColumnName": value, ...}`) -
  no "values" or "keys" wrapper. Wrapping it (as a first attempt did) fails with a
  JSON deserialization error at exactly that key.

Because it's async, a 202 only means "queued", not "inserted" - see the NULL
Link_Video rejection below, which returned 202 and only surfaced as an error on the
results endpoint. insert_data_extension_row polls status/results so a rejected row
surfaces as a real SalesforceSyncError instead of a false-positive salesforce_synced_at.
"""
import time

import httpx

from app.config import get_settings

settings = get_settings()

_POLL_ATTEMPTS = 10
_POLL_INTERVAL_SECONDS = 1.0

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


def _poll_request_result(request_id: str, headers: dict) -> None:
    """Polls the async request until it's Complete, then raises if the row was
    rejected. completionDateTime landed ~0.5-2s after callDateTime in testing, so
    _POLL_ATTEMPTS/_POLL_INTERVAL_SECONDS leaves comfortable headroom under the
    job's 60s RQ timeout without hammering the API.

    Right after the POST, the status record often isn't indexed yet - the endpoint
    returns 200 with an "AsyncRequestStatusNotFound" resultMessage instead of a
    "status" key, not an error. That's treated the same as "not ready, keep polling".
    """
    status_url = f"{_rest_base_url()}/data/v1/async/{request_id}/status"

    for _ in range(_POLL_ATTEMPTS):
        response = httpx.get(status_url, headers=headers, timeout=settings.SFMC_REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        body = response.json()
        status = body.get("status")
        if status is not None and status["requestStatus"] == "Complete":
            if not status["hasErrors"]:
                return
            results_url = f"{_rest_base_url()}/data/v1/async/{request_id}/results"
            results = httpx.get(results_url, headers=headers, timeout=settings.SFMC_REQUEST_TIMEOUT_SECONDS)
            results.raise_for_status()
            messages = [item.get("message") for item in results.json().get("items", []) if item.get("status") == "Error"]
            raise SalesforceSyncError(f"row insert rejected: {'; '.join(messages) or results.text}")
        time.sleep(_POLL_INTERVAL_SECONDS)

    raise SalesforceSyncError(f"row insert timed out waiting for async result (requestId={request_id})")


def insert_data_extension_row(fields: dict) -> None:
    """Inserts one row into the configured Data Extension.

    `fields` keys must match the Data Extension's column names exactly - SFMC doesn't
    fuzzy-match. See worker/salesforce_tasks.py for the submission -> fields mapping,
    which is the one place to adjust if the target Data Extension's schema differs.
    """
    if not settings.SFMC_ENABLED:
        raise SalesforceSyncError("SFMC_ENABLED is false - refusing to call a possibly-unconfigured integration")

    token = _get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{_rest_base_url()}/data/v1/async/dataextensions/key:{settings.SFMC_DATA_EXTENSION_KEY}/rows"

    try:
        response = httpx.post(
            url,
            json={"items": [fields]},
            headers=headers,
            timeout=settings.SFMC_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.HTTPError as e:
        detail = e.response.text if isinstance(e, httpx.HTTPStatusError) else str(e)
        raise SalesforceSyncError(f"row insert request failed: {detail}") from e

    request_id = response.json()["requestId"]
    _poll_request_result(request_id, headers)
