import asyncio

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.brokers.stub import StubBroker

from app.core.config import get_settings
from app.workers.runtime import run_argument, run_postprocess

settings = get_settings()

if settings.redis_url:
    dramatiq.set_broker(RedisBroker(url=settings.redis_url))
else:
    dramatiq.set_broker(StubBroker())


@dramatiq.actor(queue_name="debate_run", max_retries=3, min_backoff=3000)
def run_argument_actor(argument_id: str) -> None:
    asyncio.run(run_argument(argument_id))
    postprocess_actor.send(argument_id)


@dramatiq.actor(queue_name="postprocess", max_retries=2, min_backoff=3000)
def postprocess_actor(argument_id: str) -> None:
    asyncio.run(run_postprocess(argument_id))


@dramatiq.actor(queue_name="media", max_retries=1)
def media_actor(argument_id: str) -> None:
    # Placeholder for OG/share-card rendering worker.
    _ = argument_id


@dramatiq.actor(queue_name="notifications", max_retries=1)
def notifications_actor(argument_id: str) -> None:
    # Placeholder for outbound webhook notifications.
    _ = argument_id


@dramatiq.actor(queue_name="dead_letter", max_retries=0)
def dead_letter_actor(payload: str) -> None:
    # Placeholder sink for failed payload inspection workflows.
    _ = payload
