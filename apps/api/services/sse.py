"""In-memory SSE event bus using asyncio queues (no Redis required)."""
import asyncio
import json
import logging
from typing import AsyncGenerator
from collections import defaultdict

logger = logging.getLogger(__name__)

# Global registry: pipeline_id -> list of subscriber queues
_subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)


def subscribe(pipeline_id: str) -> asyncio.Queue:
    """Register a new SSE subscriber for a pipeline and return its queue."""
    q: asyncio.Queue = asyncio.Queue()
    _subscribers[pipeline_id].append(q)
    logger.debug(f"SSE subscriber added for pipeline {pipeline_id}")
    return q


def unsubscribe(pipeline_id: str, q: asyncio.Queue) -> None:
    """Remove a subscriber queue when the client disconnects."""
    if pipeline_id in _subscribers:
        try:
            _subscribers[pipeline_id].remove(q)
        except ValueError:
            pass
        if not _subscribers[pipeline_id]:
            del _subscribers[pipeline_id]


async def publish(pipeline_id: str, event_type: str, payload: dict) -> None:
    """Publish an event to all subscribers of a pipeline."""
    event = {"type": event_type, "pipelineId": pipeline_id, "payload": payload}
    dead = []
    for q in _subscribers.get(pipeline_id, []):
        try:
            await q.put(event)
        except Exception as e:
            logger.warning(f"Failed to put event in queue: {e}")
            dead.append(q)
    for q in dead:
        unsubscribe(pipeline_id, q)


async def event_stream(pipeline_id: str) -> AsyncGenerator[str, None]:
    """
    Async generator that yields SSE-formatted strings for a given pipeline.
    Sends a heartbeat every 15 seconds to keep the connection alive.
    """
    q = subscribe(pipeline_id)
    try:
        while True:
            try:
                event = await asyncio.wait_for(q.get(), timeout=15.0)
                data = json.dumps(event)
                yield f"data: {data}\n\n"
                # Stop streaming when pipeline is terminal
                if event.get("type") in ("pipeline_complete", "pipeline_failed"):
                    break
            except asyncio.TimeoutError:
                # Heartbeat to prevent proxy/browser timeout
                yield ": heartbeat\n\n"
    finally:
        unsubscribe(pipeline_id, q)
