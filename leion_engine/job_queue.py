from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from queue import Queue, Empty
from typing import Any, Dict, Optional


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Job:
    goal_id: str
    step_index: int
    payload: Dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: JobStatus = field(default=JobStatus.PENDING)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "goal_id": self.goal_id,
            "step_index": self.step_index,
            "payload": self.payload,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error": self.error,
        }


class JobQueue:
    """Simple in-memory job queue for the orchestrator.

    This is intentionally minimal for now. If you want durability later,
    you can swap this implementation for Redis / DB while gardant la même API.
    """

    def __init__(self) -> None:
        self._queue: Queue[Job] = Queue()
        self._jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()

    def put(self, job: Job) -> Job:
        with self._lock:
            self._jobs[job.id] = job
        self._queue.put(job)
        return job

    def create_job(self, goal_id: str, step_index: int, payload: Dict[str, Any]) -> Job:
        job = Job(goal_id=goal_id, step_index=step_index, payload=payload)
        return self.put(job)

    def get(self, timeout: Optional[float] = None) -> Optional[Job]:
        try:
            job = self._queue.get(timeout=timeout)
        except Empty:
            return None
        with self._lock:
            job.status = JobStatus.RUNNING
            job.updated_at = time.time()
        return job

    def mark_done(self, job: Job) -> None:
        with self._lock:
            job.status = JobStatus.DONE
            job.updated_at = time.time()
            self._jobs[job.id] = job

    def mark_failed(self, job: Job, error: str) -> None:
        with self._lock:
            job.status = JobStatus.FAILED
            job.error = error
            job.updated_at = time.time()
            self._jobs[job.id] = job

    def get_job(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def list_jobs(self, goal_id: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            if goal_id is None:
                return {jid: job.to_dict() for jid, job in self._jobs.items()}
            return {
                jid: job.to_dict()
                for jid, job in self._jobs.items()
                if job.goal_id == goal_id
            }
