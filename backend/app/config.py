from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = "development"

    # Cloudflare R2 (S3-compatible)
    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    R2_ENDPOINT_URL: str
    R2_BUCKET_NAME: str

    # Upload token (short-lived JWT authorizing the confirm-upload call)
    UPLOAD_TOKEN_SECRET: str
    UPLOAD_TOKEN_TTL_SECONDS: int = 1800  # 30 min
    PRESIGNED_PUT_TTL_SECONDS: int = 1800 + 300  # token TTL + buffer for slow uploads
    PRESIGNED_GET_TTL_SECONDS: int = 300  # admin video-preview links

    # Admin auth
    ADMIN_JWT_SECRET: str
    ADMIN_SESSION_TTL_SECONDS: int = 8 * 60 * 60  # 8h
    ADMIN_PASSWORD_HASH: str  # bcrypt hash, generate via scripts/generate_admin_password_hash.py

    # CORS
    CORS_ALLOW_ORIGINS: str = "http://localhost:3000"
    CORS_ALLOW_ORIGIN_REGEX: str | None = r"https://.*\.vercel\.app"

    # Rate limiting
    RATE_LIMIT_SUBMIT: str = "5/hour"
    RATE_LIMIT_CONFIRM_UPLOAD: str = "20/hour"
    RATE_LIMIT_ADMIN_LOGIN: str = "5/minute"
    RATE_LIMIT_VOTE: str = "10/hour"

    # Etapa 2 (votación pública): tope duro de submissions marcadas a la vez como
    # candidatas votables (ver app/salesforce.py / routers/admin.py). No es un secreto,
    # no necesita variable en Render.
    VOTE_CANDIDATES_LIMIT: int = 4

    # What to do when ffprobe/server-side validation itself fails unexpectedly
    # (corrupt file vs. tool crash are hard to fully distinguish) - default errs safe (reject),
    # can be relaxed to "needs_review" if false positives from flaky ffprobe show up in practice.
    SERVER_VALIDATION_FAILURE_STATUS: str = "rejected"

    # Salesforce Marketing Cloud - the only persistent store for this project (see
    # app/salesforce.py). Required for the app to do anything useful, but still
    # defaults to disabled/optional so Settings() doesn't break for anyone who hasn't
    # configured it yet (e.g. running the test suite). Flip SFMC_ENABLED once set up.
    SFMC_ENABLED: bool = False
    SFMC_SUBDOMAIN: str | None = None  # the "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" tenant subdomain
    SFMC_CLIENT_ID: str | None = None  # from the Installed Package (server-to-server / API Integration component)
    SFMC_CLIENT_SECRET: str | None = None
    SFMC_ACCOUNT_ID: str | None = None  # MID of the target Business Unit, if the package spans multiple BUs
    SFMC_DATA_EXTENSION_KEY: str | None = None  # External Key of the Formulario_Video_Nino DE
    SFMC_ADULTS_DATA_EXTENSION_KEY: str | None = None  # External Key of the sendable adults/voting DE
    SFMC_REQUEST_TIMEOUT_SECONDS: float = 15.0

    @property
    def cors_allow_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ALLOW_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
