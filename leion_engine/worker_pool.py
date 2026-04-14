from __future__ import annotations

import threading
from typing import Callable, Optional

from .job_queue import JobQueue, Job, JobStatus


class WorkerPool:
    """Very small worker pool to execute orchestrator jobs in background.

    This is intentionally simple: a few threads that keep polling the queue.
    The actual logic of *what* to execute is injected via `handler`.
    """

    def __init__(
        self,
        queue: JobQueue,
        handler: Callable[[Job], None],
        num_workers: int = 2,
    ) -> None:
        self.queue = queue
        self.handler = handler
        self.num_workers = max(1, num_workers)
        self._threads: list[threading.Thread] = []
        self._stop_event = threading.Event()

    def start(self) -> None:
        if self._threads:
            return
        for i in range(self.num_workers):
            t = threading.Thread(target=self._worker_loop, name=f"leion-worker-{i}", daemon=True)
            t.start()
            self._threads.append(t)

    def stop(self) -> None:
        self._stop_event.set()
        for t in self._threads:
            t.join(timeout=1)
        self._threads.clear()

    def _worker_loop(self) -> None:
        while not self._stop_event.is_set():
            job = self.queue.get(timeout=0.5)
            if job is None:
                continue
            try:
                self.handler(job)
                # si le handler ne change pas le statut, on le marque done
                if job.status == JobStatus.RUNNING:
                    self.queue.mark_done(job)
            except Exception as e:  # pragma: no cover - simple logging placeholder
                self.queue.mark_failed(job, error=str(e))

