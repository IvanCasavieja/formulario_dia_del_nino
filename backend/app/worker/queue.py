from redis import Redis
from rq import Callback, Queue, Retry

from app.config import get_settings

settings = get_settings()

redis_conn = Redis.from_url(settings.REDIS_URL)
moderation_queue = Queue("moderation", connection=redis_conn)


def enqueue_submission_processing(submission_id: str) -> None:
    """Enqueues by dotted string path (not a direct import) so the web process doesn't
    need to pull in the worker's heavier deps (ffmpeg calls, Rekognition client) just to
    hand off a job."""
    moderation_queue.enqueue(
        "app.worker.tasks.process_submission_video",
        submission_id,
        retry=Retry(max=2, interval=[30, 120]),
        on_failure=Callback("app.worker.tasks.on_submission_failure"),
        job_timeout=300,
    )


def enqueue_salesforce_sync(submission_id: str) -> None:
    """Same queue/worker as moderation - RQ doesn't care what a job's function is, and
    a second queue (plus a second worker service listening to it) isn't earning its
    keep at this volume for what's a best-effort, never-blocking side sync."""
    settings = get_settings()
    moderation_queue.enqueue(
        "app.worker.salesforce_tasks.sync_submission_to_salesforce",
        submission_id,
        retry=Retry(max=settings.SFMC_SYNC_RETRY_MAX, interval=[30, 120, 300]),
        on_failure=Callback("app.worker.salesforce_tasks.on_salesforce_sync_failure"),
        job_timeout=60,
    )
