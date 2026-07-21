FROM python:3.12-slim

# ffmpeg/ffprobe are required by the moderation pipeline (frame extraction + duration/
# format checks). Render's plain Python buildpack doesn't include them, which is why
# this project deploys via Docker rather than a native buildpack.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY shared/ /shared/

RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Overridden per-service by render.yaml's startCommand (web vs worker vs cron).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
