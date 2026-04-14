from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from .leion_cc_common_tools import make_output
from .leion_ai_intelligence_tools import _detect_intent


STATE_DIR_NAME = "state/ai_workflows"


def _get_state_dir() -> Path:
    """Retourne le dossier où sont stockés les états de workflows IA.

    On reste en local dans le repo MCP pour l'instant (simple, robuste).
    Tu pourras plus tard le mapper vers D:/claude_code/leion_workspace si tu veux
    déplacer la mémoire.
    """
    root = Path(__file__).resolve().parents[1]
    state_dir = root / STATE_DIR_NAME
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


def _workflow_path(workflow_id: str) -> Path:
    return _get_state_dir() / f"{workflow_id}.json"


def _load_json(path: Path) -> Dict[str, Any]:
    import json

    if not path.exists():
        raise FileNotFoundError(f"Workflow state not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Dict[str, Any]) -> None:
    import json

    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _build_monetization_steps(goal: str) -> List[Dict[str, Any]]:
    """Plan de base pour un workflow de monétisation.

    V0 : fixe, mais structuré pour être enrichi ensuite (7+ agents, etc.).
    """
    return [
        {
            "id": "1",
            "kind": "connect_integrations",
            "title": "Connecter au moins un provider de paiement",
            "description": (
                "Choisir et connecter au moins une plateforme (Stripe, Paypal, Gumroad, Ko-fi, "
                "Paddle). Je peux te proposer les meilleurs choix selon ton business."
            ),
        },
        {
            "id": "2",
            "kind": "design_offer",
            "title": "Définir l'offre à monétiser",
            "description": (
                "Clarifier ce que tu vends : produit, service, formation, abonnement, bundle, etc."
            ),
        },
        {
            "id": "3",
            "kind": "pricing",
            "title": "Construire la stratégie de pricing",
            "description": (
                "Fixer un prix, un modèle (one-shot, abonnement, tiers) et des conditions (garantie, essais)."
            ),
        },
        {
            "id": "4",
            "kind": "funnel",
            "title": "Dessiner le funnel de conversion",
            "description": (
                "Comment les gens arrivent, ce qu'ils voient, comment ils payent, ce qu'ils reçoivent."
            ),
        },
        {
            "id": "5",
            "kind": "automation",
            "title": "Automatiser les opérations clés",
            "description": (
                "Notifications, emails, accès au contenu, sync CRM, compta de base, etc."
            ),
        },
        {
            "id": "6",
            "kind": "launch",
            "title": "Préparer le lancement",
            "description": (
                "Checklist de lancement : messages, séquences, tests, plan des 7 premiers jours."
            ),
        },
        {
            "id": "7",
            "kind": "optimize",
            "title": "Mesurer et optimiser",
            "description": (
                "Suivre les premiers résultats, identifier les points de friction et proposer des iterations."
            ),
        },
    ]


def _build_generic_steps(goal: str) -> List[Dict[str, Any]]:
    return [
        {
            "id": "1",
            "kind": "clarify",
            "title": "Clarifier l'objectif",
            "description": "Clarifier ce que tu veux vraiment obtenir en une ou deux phrases.",
        },
        {
            "id": "2",
            "kind": "plan",
            "title": "Construire un plan d'actions",
            "description": "Lister les étapes clés pour atteindre ton objectif.",
        },
        {
            "id": "3",
            "kind": "execute",
            "title": "Exécuter les premières actions concrètes",
            "description": "Choisir 1 à 3 actions immédiates à lancer.",
        },
    ]


def _new_workflow(goal: str) -> Dict[str, Any]:
    import time

    intent = _detect_intent(goal)
    ts = int(time.time())
    workflow_id = f"wf_{intent}_{ts}"

    if intent == "payments":
        steps = _build_monetization_steps(goal)
    else:
        steps = _build_generic_steps(goal)

    wf = {
        "id": workflow_id,
        "intent": intent,
        "goal": goal,
        "status": "in_progress",
        "current_step_index": 0,
        "steps": steps,
        "history": [],
        "context": {},
    }

    _save_json(_workflow_path(workflow_id), wf)
    return wf


def _advance_workflow(wf: Dict[str, Any], feedback: Optional[str] = None) -> Dict[str, Any]:
    idx = wf.get("current_step_index", 0)
    steps = wf.get("steps", [])

    if feedback:
        wf.setdefault("history", []).append({"step_index": idx, "feedback": feedback})

    if idx + 1 >= len(steps):
        wf["status"] = "completed"
        wf["current_step_index"] = len(steps) - 1
    else:
        wf["current_step_index"] = idx + 1

    _save_json(_workflow_path(wf["id"]), wf)
    return wf


def _summarize_workflow(wf: Dict[str, Any]) -> str:
    intent = wf.get("intent")
    goal = wf.get("goal")
    status = wf.get("status")
    steps = wf.get("steps", [])
    idx = wf.get("current_step_index", 0)

    lines: List[str] = []
    lines.append(f"🧠 Workflow IA Leion – objectif : {goal}")

    if intent == "payments":
        lines.append("→ Type : MONÉTISATION / REVENUS.")
    else:
        lines.append(f"→ Type : {intent}.")

    lines.append(f"→ Statut : {status}.")

    if steps:
        current = steps[idx]
        lines.append("Étape actuelle :")
        lines.append(f"[{current['id']}] {current['title']}")
        lines.append(current["description"])

    if status != "completed":
        lines.append("Quand tu as avancé sur cette étape, dis-moi ce que tu as fait ou ce qui bloque,")
        lines.append("et je passerai à l'étape suivante en gardant le fil.")

    return "".join(lines)


def register_leion_ai_workflow_engine_tools(server: FastMCP):

    @server.tool()
    async def leion_ai_start_workflow(goal: str) -> Dict[str, Any]:
        """Crée un nouveau workflow IA autour d'un goal (ex: 'je veux gagner de l'argent').

        - Détecte une intention (paiements, générique, etc.)
        - Construit un plan structuré en étapes
        - Stocke l'état sur disque pour le poursuivre plus tard
        """
        wf = _new_workflow(goal)
        structured = {
            "type": "leion_ai_workflow",
            "workflow": wf,
        }
        summary = _summarize_workflow(wf)
        return make_output(summary, structured, with_widget=False)

    @server.tool()
    async def leion_ai_next_step(
        workflow_id: str,
        feedback: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Avance un workflow IA existant d'une étape, en prenant en compte le feedback.

        - recharge l'état depuis le disque
        - ajoute éventuellement le feedback à l'historique
        - avance l'index d'étape
        - renvoie le nouvel état et un résumé humain
        """
        wf = _load_json(_workflow_path(workflow_id))
        wf = _advance_workflow(wf, feedback)
        structured = {
            "type": "leion_ai_workflow",
            "workflow": wf,
        }
        summary = _summarize_workflow(wf)
        return make_output(summary, structured, with_widget=False)
