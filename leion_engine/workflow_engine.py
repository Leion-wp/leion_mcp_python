from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .job_queue import JobQueue
from .parser import Plan, parse_llm_plan_response
from .executor import PlanExecutor, ToolRunner
from .worker_pool import WorkerPool


@dataclass
class GoalState:
    id: str
    goal: str
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    current_step: int = 0
    plan: Optional[Plan] = None
    last_result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "current_step": self.current_step,
            "has_plan": self.plan is not None,
        }


class OrchestratorEngine:
    """Noyau de l'orchestrateur IA pour Leion OS.

    Rôle :
      - stocker les objectifs (goals)
      - recevoir un plan structure (via LLM) et le parser en `Plan`
      - exécuter les étapes du plan via les tools MCP
      - exposer une API simple que tu pourras mapper sur des tools MCP :
        - orchestrator_create_goal
        - orchestrator_set_plan
        - orchestrator_run_next_step
        - orchestrator_get_state
    """

    def __init__(self, runner: ToolRunner, num_workers: int = 2) -> None:
        self._goals: Dict[str, GoalState] = {}
        self._goals_lock = threading.Lock()

        self.queue = JobQueue()
        self.executor = PlanExecutor(runner=runner)
        self.worker_pool = WorkerPool(self.queue, handler=self._handle_job, num_workers=num_workers)
        self.worker_pool.start()

    # ------------------------- goals -------------------------

    def create_goal(self, goal: str) -> GoalState:
        goal_id = str(uuid.uuid4())
        state = GoalState(id=goal_id, goal=goal)
        with self._goals_lock:
            self._goals[goal_id] = state
        return state

    def get_goal(self, goal_id: str) -> Optional[GoalState]:
        with self._goals_lock:
            return self._goals.get(goal_id)

    def list_goals(self) -> List[Dict[str, Any]]:
        with self._goals_lock:
            return [g.to_dict() for g in self._goals.values()]

    # ------------------------- plan management -------------------------

    def set_plan_from_llm(self, goal_id: str, llm_structured_plan: Any) -> GoalState:
        state = self.get_goal(goal_id)
        if not state:
            raise ValueError(f"Unknown goal_id {goal_id}")

        plan = parse_llm_plan_response(goal_id=goal_id, goal=state.goal, data=llm_structured_plan)
        state.plan = plan
        state.current_step = 0
        state.updated_at = time.time()
        return state

    # ------------------------- execution -------------------------

    def enqueue_next_step(self, goal_id: str) -> str:
        state = self.get_goal(goal_id)
        if not state or not state.plan:
            raise ValueError("Goal has no plan yet")

        if state.current_step >= len(state.plan.steps):
            raise ValueError("All steps already executed")

        step = state.plan.steps[state.current_step]
        job = self.queue.create_job(
            goal_id=goal_id,
            step_index=step.index,
            payload={"goal_id": goal_id, "step_index": step.index},
        )
        return job.id

    def _handle_job(self, job):
        state = self.get_goal(job.goal_id)
        if not state or not state.plan:
            raise ValueError("Goal/plan disappeared while running job")

        step = state.plan.steps[job.step_index]
        result = self.executor.execute_step(step)
        state.last_result = result
        state.current_step = job.step_index + 1
        state.updated_at = time.time()
        # la JobQueue se charge de marquer le job done

    # ------------------------- public helpers (à mapper en tools MCP) -------------------------

    def api_create_goal(self, goal: str) -> Dict[str, Any]:
        state = self.create_goal(goal)
        return state.to_dict()

    def api_set_plan(self, goal_id: str, llm_structured_plan: Any) -> Dict[str, Any]:
        state = self.set_plan_from_llm(goal_id, llm_structured_plan)
        return {
            "goal": state.to_dict(),
            "plan": [s.__dict__ for s in (state.plan.steps if state.plan else [])],
        }

    def api_run_next_step(self, goal_id: str) -> Dict[str, Any]:
        job_id = self.enqueue_next_step(goal_id)
        return {
            "job_id": job_id,
            "goal_id": goal_id,
        }

    def api_get_goal_state(self, goal_id: str) -> Dict[str, Any]:
        state = self.get_goal(goal_id)
        if not state:
            raise ValueError(f"Unknown goal_id {goal_id}")
        return {
            "goal": state.to_dict(),
            "last_result": state.last_result,
        }

    def api_list_goals(self) -> List[Dict[str, Any]]:
        return self.list_goals()

