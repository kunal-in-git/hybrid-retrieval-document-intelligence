import json
import os

import redis


REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://redis:6379/0",
)

redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True,
)


QUEUE_NAME = "document_ingestion"


def enqueue_ingestion_job(job_id: str) -> None:
    message = json.dumps({
        "job_id": job_id,
    })

    redis_client.rpush(
        QUEUE_NAME,
        message,
    )