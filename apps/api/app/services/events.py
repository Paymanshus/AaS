import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator
from contextlib import suppress
from datetime import UTC, datetime

import orjson
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import TurnEvent

settings = get_settings()


class EventBus:
    def __init__(self, redis_url: str | None) -> None:
        self.redis_url = redis_url
        self.redis: Redis | None = None
        self._queues: dict[str, set[asyncio.Queue[dict]]] = defaultdict(set)

    async def connect(self) -> None:
        if self.redis_url:
            self.redis = Redis.from_url(self.redis_url, decode_responses=False)

    async def _ensure_redis(self) -> None:
        if self.redis_url and self.redis is None:
            self.redis = Redis.from_url(self.redis_url, decode_responses=False)

    async def close(self) -> None:
        if self.redis:
            await self.redis.aclose()

    def _channel(self, argument_id: str) -> str:
        return f"argument:{argument_id}:events"

    async def publish(self, argument_id: str, payload: dict) -> None:
        await self._ensure_redis()
        if self.redis:
            try:
                await self.redis.publish(self._channel(argument_id), orjson.dumps(payload))
                return
            except Exception:
                # Fall back to in-process fanout when Redis is unavailable.
                with suppress(Exception):
                    await self.redis.aclose()
                self.redis = None
        for queue in self._queues[argument_id]:
            await queue.put(payload)

    async def subscribe(self, argument_id: str) -> AsyncIterator[dict]:
        await self._ensure_redis()
        if self.redis:
            try:
                assert self.redis is not None
                pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
                await pubsub.subscribe(self._channel(argument_id))
                try:
                    async for raw_msg in pubsub.listen():
                        data = raw_msg.get("data")
                        if not data:
                            continue
                        if isinstance(data, bytes):
                            yield orjson.loads(data)
                        elif isinstance(data, str):
                            yield orjson.loads(data.encode("utf-8"))
                finally:
                    with suppress(Exception):
                        await pubsub.unsubscribe(self._channel(argument_id))
                    await pubsub.aclose()
                return
            except Exception:
                # Fall back to in-process subscription when Redis is unavailable.
                with suppress(Exception):
                    await self.redis.aclose()
                self.redis = None

        queue: asyncio.Queue[dict] = asyncio.Queue()
        self._queues[argument_id].add(queue)
        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            self._queues[argument_id].discard(queue)


_event_bus: EventBus | None = None


def set_event_bus(event_bus: EventBus) -> None:
    global _event_bus
    _event_bus = event_bus


def get_event_bus() -> EventBus:
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus(settings.redis_url)
    return _event_bus


async def persist_event(
    session: AsyncSession,
    *,
    argument_id: str,
    event_type: str,
    payload: dict,
    turn_index: int | None = None,
) -> TurnEvent:
    event = TurnEvent(
        argument_id=argument_id,
        event_type=event_type,
        payload=payload,
        turn_index=turn_index,
        created_at=datetime.now(UTC),
    )
    session.add(event)
    await session.flush()

    wire_payload = {
        "id": event.id,
        "argument_id": argument_id,
        "event_type": event_type,
        "payload": payload,
        "turn_index": turn_index,
        "created_at": event.created_at.isoformat(),
    }
    await get_event_bus().publish(argument_id, wire_payload)
    return event
