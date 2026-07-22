from slowapi import Limiter
from slowapi.util import get_remote_address

# TEMP (free tier, no Redis available - revert once on a paid plan): storage_uri
# defaults to in-memory, which only works correctly with a single instance. Fine for
# the free-tier Web Service (never scales beyond one), wrong the moment there's more
# than one web instance - pass storage_uri=settings.REDIS_URL back then.
limiter = Limiter(key_func=get_remote_address)
