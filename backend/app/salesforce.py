"""Salesforce Marketing Cloud REST API client: OAuth2 client-credentials auth against
an Installed Package, then row operations against a Data Extension by External Key.

This Data Extension (Formulario_Video_Nino) is the ONLY persistent store for this
project - there is no database. Personal data (name, cedula, email, phone) must never
be written anywhere else. Cedula_Nino is the DE's primary key (one entry per child,
not per adult - the same parent can have two kids each entering separately), so every
row operation here is keyed by it.

Endpoint/payload shapes verified live against the real tenant - see
backend/scripts/test_salesforce_sync.py. Notes that aren't obvious from Salesforce's
docs and cost real trial and error:

- Row insert/update goes through the *async* endpoint
  (`/data/v1/async/dataextensions/key:.../rows`). There's no working synchronous
  equivalent for this API generation - the same path without "async" 404s, and the
  older `/data/v1/customobjectdata/key/.../rowset` only supports GET, not POST/PUT.
- Each item in "items" is the field values directly (`{"ColumnName": value, ...}`) -
  no "values"/"keys" wrapper; wrapping it fails with a JSON deserialization error.
- POST inserts (fails if Cedula_Nino already exists); PUT upserts (updates the row
  matching the primary key, inserts if none matches) - but PUT silently returns an
  *async result* error (not an HTTP error) if the DE has no primary key defined at
  all: "This Data Extension does not have any primary keys defined."
- Retrieve (`GET .../rowset`) returns lowercase field names in `values`, and supports
  `$filter` on any column (not only the primary key) even though this DE is not
  "sendable".
- Because writes are async, a `202` only means "queued". insert/upsert here poll
  status/results so a rejected row raises SalesforceSyncError instead of silently
  vanishing (this is exactly how the NULL Link_Video rejection surfaced originally).
"""
import time
from urllib.parse import quote

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


def _rows_url() -> str:
    return f"{_rest_base_url()}/data/v1/async/dataextensions/key:{settings.SFMC_DATA_EXTENSION_KEY}/rows"


def _rowset_url() -> str:
    return f"{_rest_base_url()}/data/v1/customobjectdata/key/{settings.SFMC_DATA_EXTENSION_KEY}/rowset"


def _build_rowset_url(filter_expr: str | None = None, page_size: int | None = None) -> str:
    """Appends $filter/$pageSize as a manually-built, pre-encoded query string instead
    of passing them through httpx's `params=` dict. Mashery (SFMC's API gateway)
    rejects a `+`-encoded space in $filter outright - "request parameter $filter could
    not be resolved" (errorcode 10003) - it only accepts %20, but httpx's dict-based
    params encode spaces as `+`. quote() (not quote_plus()) defaults to %20."""
    query_parts = []
    if filter_expr:
        query_parts.append(f"$filter={quote(filter_expr, safe='')}")
    if page_size:
        query_parts.append(f"$pageSize={page_size}")
    query = "&".join(query_parts)
    return f"{_rowset_url()}?{query}" if query else _rowset_url()


def _require_enabled() -> None:
    if not settings.SFMC_ENABLED:
        raise SalesforceSyncError("SFMC_ENABLED is false - refusing to call a possibly-unconfigured integration")


def _get_access_token() -> str:
    """Client-credentials grant. Tokens are cached in-process and reused until ~30s
    before expiry (SFMC tokens are typically valid ~20 minutes)."""
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
    """Polls the async request until it's Complete, then raises if the row write was
    rejected. Right after the POST/PUT, the status record often isn't indexed yet -
    the endpoint returns 200 with an "AsyncRequestStatusNotFound" resultMessage
    instead of a "status" key, not an error - that's treated as "not ready, retry"."""
    status_url = f"{_rest_base_url()}/data/v1/async/{request_id}/status"

    for _ in range(_POLL_ATTEMPTS):
        response = httpx.get(status_url, headers=headers, timeout=settings.SFMC_REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        req_status = response.json().get("status") or {}
        if req_status.get("requestStatus") == "Complete":
            if not req_status.get("hasErrors"):
                return
            results_url = f"{_rest_base_url()}/data/v1/async/{request_id}/results"
            results = httpx.get(results_url, headers=headers, timeout=settings.SFMC_REQUEST_TIMEOUT_SECONDS)
            results.raise_for_status()
            messages = [
                item.get("message") for item in results.json().get("items", []) if item.get("status") == "Error"
            ]
            raise SalesforceSyncError(f"row write rejected: {'; '.join(messages) or results.text}")
        time.sleep(_POLL_INTERVAL_SECONDS)

    raise SalesforceSyncError(f"row write timed out waiting for async result (requestId={request_id})")


def insert_row(fields: dict) -> None:
    """Inserts a new row. Fails if Cedula_Nino (the primary key) already exists."""
    _require_enabled()
    token = _get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = httpx.post(
            _rows_url(), json={"items": [fields]}, headers=headers, timeout=settings.SFMC_REQUEST_TIMEOUT_SECONDS
        )
        response.raise_for_status()
    except httpx.HTTPError as e:
        detail = e.response.text if isinstance(e, httpx.HTTPStatusError) else str(e)
        raise SalesforceSyncError(f"row insert request failed: {detail}") from e
    _poll_request_result(response.json()["requestId"], headers)


def upsert_row(fields: dict) -> None:
    """Inserts or updates a row, matched by Cedula_Nino (the DE's primary key).
    `fields` must include Cedula_Nino."""
    _require_enabled()
    token = _get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = httpx.put(
            _rows_url(), json={"items": [fields]}, headers=headers, timeout=settings.SFMC_REQUEST_TIMEOUT_SECONDS
        )
        response.raise_for_status()
    except httpx.HTTPError as e:
        detail = e.response.text if isinstance(e, httpx.HTTPStatusError) else str(e)
        raise SalesforceSyncError(f"row upsert request failed: {detail}") from e
    _poll_request_result(response.json()["requestId"], headers)


def get_row_by_cedula_nino(cedula_nino: str) -> dict | None:
    """Looks up a single row by the child's cedula. Returns the row's values
    (lowercase field names, as SFMC returns them) or None if it doesn't exist."""
    _require_enabled()
    token = _get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = _build_rowset_url(filter_expr=f"cedula_nino eq '{cedula_nino}'")
    try:
        response = httpx.get(url, headers=headers, timeout=settings.SFMC_REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except httpx.HTTPError as e:
        detail = e.response.text if isinstance(e, httpx.HTTPStatusError) else str(e)
        raise SalesforceSyncError(f"row lookup failed: {detail}") from e
    items = response.json().get("items", [])
    return items[0]["values"] if items else None


def list_rows(status: str | None = None, limit: int = 200) -> list[dict]:
    """Lists rows, optionally filtered by Status. This DE is the only store the admin
    panel has to query. Non-sendable DEs cap out around 200 rows per call - fine at
    this volume, would need real pagination past that."""
    _require_enabled()
    token = _get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    filter_expr = f"status eq '{status}'" if status else None
    url = _build_rowset_url(filter_expr=filter_expr, page_size=limit)
    try:
        response = httpx.get(url, headers=headers, timeout=settings.SFMC_REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except httpx.HTTPError as e:
        detail = e.response.text if isinstance(e, httpx.HTTPStatusError) else str(e)
        raise SalesforceSyncError(f"row list failed: {detail}") from e
    return [item["values"] for item in response.json().get("items", [])]


def build_row_fields(
    *,
    parent_first_name: str,
    parent_last_name: str,
    parent_cedula: str,
    parent_email: str,
    parent_phone: str,
    child_first_name: str,
    child_last_name: str,
    child_cedula: str,
    terms_accepted: bool,
) -> dict:
    """Maps our internal field names to the DE's actual column names. The one place
    to edit if the DE's schema changes - SFMC doesn't fuzzy-match column names."""
    return {
        "Nombre_Adulto": parent_first_name,
        "Apellido_Adulto": parent_last_name,
        "Cedula": parent_cedula,
        "EmailAddress": parent_email,
        "Celular": parent_phone,
        "Nombre_nino": child_first_name,
        "Apellido_nino": child_last_name,
        "Cedula_Nino": child_cedula,
        "Term_Cond": terms_accepted,
    }
