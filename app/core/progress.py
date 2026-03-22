"""
ProgressManager — In-memory SSE state for real-time job progress.
Tier 1: Simple in-memory store. Cleared on server restart (acceptable for MVP).
"""

import asyncio
import json
from collections import defaultdict
from datetime import datetime, timezone
from typing import AsyncIterator


class ProgressManager:
    """
    In-memory store for SSE job progress events.
    Holds job state and distributes events to all connected clients via SSE.
    """
    
    def __init__(self):
        # job_id → list of asyncio.Queue (one per connected SSE client)
        self._queues: dict[str, list[asyncio.Queue]] = defaultdict(list)
        # job_id → latest progress snapshot (used to show state to new clients)
        self._state: dict[str, dict] = {}
    
    def _now(self) -> str:
        """Return current UTC timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()
    
    async def emit(self, job_id: str, event_type: str,
                   stage: str = "", progress: int = 0,
                   message: str = "") -> None:
        """
        Push an event to all clients watching this job.
        
        Args:
            job_id: Unique job identifier
            event_type: "progress" | "stage_changed" | "partial_log" | "completed" | "failed"
            stage: Current agent/stage (e.g. "researcher", "analyst", "writer")
            progress: 0-100 completion percentage
            message: Human-readable status message
        """
        payload = json.dumps({
            "type": event_type,
            "job_id": job_id,
            "stage": stage,
            "progress": progress,
            "message": message,
            "timestamp": self._now()
        })
        
        # Store latest state
        self._state[job_id] = payload
        
        # Broadcast to all connected clients
        for q in self._queues[job_id]:
            try:
                await q.put(payload)
            except Exception:
                pass  # Client disconnected
    
    async def subscribe(self, job_id: str) -> AsyncIterator[str]:
        """
        Subscribe to a job's progress stream. Yields events as they occur.
        Used by the SSE endpoint to stream updates to Streamlit UI.
        
        Yields:
            JSON-formatted progress event strings
        """
        q: asyncio.Queue = asyncio.Queue()
        self._queues[job_id].append(q)
        
        try:
            # Send last known state immediately (so UI isn't blank on reconnect)
            if job_id in self._state:
                yield self._state[job_id]
            
            # Stream new events
            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=30)
                    yield event

                    # Stop streaming after job completes or fails
                    if json.loads(event)["type"] in ("completed", "failed"):
                        break
                except asyncio.TimeoutError:
                    # Keep the SSE connection alive by re-sending the last state.
                    if job_id in self._state:
                        yield self._state[job_id]
                    else:
                        yield json.dumps({
                            "type": "ping",
                            "job_id": job_id,
                            "stage": "",
                            "progress": 0,
                            "message": "",
                            "timestamp": self._now()
                        })
                    continue
        
        finally:
            # Clean up subscription
            if q in self._queues[job_id]:
                self._queues[job_id].remove(q)


# Singleton instance — import this everywhere to emit events
progress_manager = ProgressManager()
