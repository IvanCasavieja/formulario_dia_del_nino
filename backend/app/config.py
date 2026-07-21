from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = "development"

    # Postgres
    DATABASE_URL: str

    # Redis (RQ queue + rate limiting)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Cloudflare R2 (S3-compatible)
    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    R2_ENDPOINT_URL: str
    R2_BUCKET_NAME: str

    # AWS Rekognition
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "us-east-1"

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

    # Moderation thresholds
    MODERATION_REJECT_CATEGORIES: str = "Explicit Nudity,Violence,Visually Disturbing,Drugs,Hate Symbols"
    MODERATION_REJECT_CONFIDENCE: float = 90.0
    MODERATION_REVIEW_CONFIDENCE: float = 50.0
    MODERATION_MIN_CONFIDENCE_FLOOR: float = 40.0  # passed to Rekognition as MinConfidence
    MODERATION_FRAME_COUNT: int = 5

    # What to do when ffprobe/server-side validation itself fails unexpectedly
    # (corrupt file vs. tool crash are hard to fully distinguish) - default errs safe (reject),
    # can be relaxed to "needs_review" if false positives from flaky ffprobe show up in practice.
    SERVER_VALIDATION_FAILURE_STATUS: str = "rejected"

    # Stale pending_upload cleanup (Render cron)
    PENDING_UPLOAD_EXPIRY_SECONDS: int = 2 * 1800  # 2x upload token TTL

    # Salesforce Marketing Cloud sync (best-effort, fires once per submission right
    # after upload is confirmed - see routers/submissions.py). Off by default and all
    # fields optional: real credentials don't exist yet, and nothing here should break
    # Settings() for anyone who hasn't set this up. Flip SFMC_ENABLED once configured.
    SFMC_ENABLED: bool = False
    SFMC_SUBDOMAIN: str | None = None  # the "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" tenant subdomain
    SFMC_CLIENT_ID: str | None = None  # from the Installed Package (server-to-server / API Integration component)
    SFMC_CLIENT_SECRET: str | None = None
    SFMC_ACCOUNT_ID: str | None = None  # MID of the target Business Unit, if the package spans multiple BUs
    SFMC_DATA_EXTENSION_KEY: str | None = None  # External Key of the target Data Extension
    SFMC_SYNC_RETRY_MAX: int = 3
    SFMC_REQUEST_TIMEOUT_SECONDS: float = 15.0

    @property
    def moderation_reject_categories_list(self) -> list[str]:
        return [c.strip() for c in self.MODERATION_REJECT_CATEGORIES.split(",") if c.strip()]

    @property
    def cors_allow_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ALLOW_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
