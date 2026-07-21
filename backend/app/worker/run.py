"""RQ worker entrypoint. Started as its own Render service (same Docker image as the
web service, different startCommand): `python -m app.worker.run`."""
import logging

from rq import Worker

from app.worker.queue import moderation_queue, redis_conn

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    worker = Worker([moderation_queue], connection=redis_conn)
    worker.work()
