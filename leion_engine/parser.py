from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class Step:
    index: int
    description: str
    tool_name: str | None = None
    tool_args: Dict[str, Any] | None = None


@dataclass
class Plan:
    goal_id: str
    goal: str
    steps: List[Step]


def parse_llm_plan_response(goal_id: str, goal: str, data: Any) -> Plan:
    """Transforme une réponse LLM structurée en Plan.

    On suppose ici que `data` est déjà un JSON du type :
    {
      "steps": [
        {"description": "...", "tool_name": "...", "tool_args": {...}},
        ...
      ]
    }

    Cette fonction est volontairement tolérante : si les champs manquent,
    on fabrique un plan minimaliste, que l'IA pourra affiner au prochain tour.
    """

    raw_steps = []
    if isinstance(data, dict):
        raw_steps = data.get("steps") or []
    elif isinstance(data, list):
        raw_steps = data

    steps: List[Step] = []
    for idx, item in enumerate(raw_steps):
        if not isinstance(item, dict):
            steps.append(Step(index=idx, description=str(item)))
            continue
        steps.append(
            Step(
                index=idx,
                description=str(item.get("description", f"Step {idx}")),
                tool_name=item.get("tool_name"),
                tool_args=item.get("tool_args") or {},
            )
        )

    if not steps:
        steps = [Step(index=0, description=goal)]

    return Plan(goal_id=goal_id, goal=goal, steps=steps)
