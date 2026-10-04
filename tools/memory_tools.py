import os
from typing import Any, Dict

from fastmcp import FastMCP

from .local_memory_store import workspace_root

# Racine du workspace mémoire (fichiers + vector store)
# Par défaut, on reste dans un dossier local au repo pour éviter tout chemin absolu machine-spécifique.
WORKSPACE_ROOT = str(workspace_root())

MEMORY_BANK = os.path.join(WORKSPACE_ROOT, "memory_bank")
VECTOR_STORE_ROOT = os.path.join(WORKSPACE_ROOT, "vector_store")
RULES_PATH = os.path.join(WORKSPACE_ROOT, "rules_memory.txt")


def _memory_paths_dict() -> Dict[str, str]:
    """
    Helper interne pour retourner les chemins de base de la mémoire.
    Utilisé à la fois par les tools et évite d'appeler un tool depuis un autre.
    """
    return {
        "workspace_root": WORKSPACE_ROOT,
        "rules_path": RULES_PATH,
        "short_term": os.path.join(MEMORY_BANK, "short_term", "index.txt"),
        "work_memory": os.path.join(MEMORY_BANK, "work_memory", "index.txt"),
        "long_term": os.path.join(MEMORY_BANK, "long_term"),
        "local_namespace_store": os.path.join(VECTOR_STORE_ROOT, "namespaces"),
        "namespaces_dir": os.path.join(VECTOR_STORE_ROOT, "namespaces"),
    }


def register_memory_tools(server: FastMCP):

    @server.tool()
    def memory_status_paths() -> Dict[str, str]:
        """
        Retourne les chemins de base utilisés par le sous-système mémoire.

        Utile pour les workflows et pour que le modèle sache où lire/écrire.
        """
        return _memory_paths_dict()

    @server.tool()
    def memory_sweep_plan() -> Dict[str, Any]:
        """
        Prépare un plan structuré pour un "memory sweep" périodique.

        Le but est de :
        - relire les règles
        - analyser short_term et work_memory
        - promouvoir ce qui doit aller en long_term
        - synchroniser avec le vector store via vector_store_add
        - nettoyer/archiver short_term si nécessaire
        """
        return {
            "type": "memory_sweep_plan",
            "paths": _memory_paths_dict(),
            "steps": [
                "Lire rules_memory.txt pour appliquer les règles de constitution de la mémoire.",
                "Lire memory_bank/short_term/index.txt et identifier les tâches accomplies ou obsolètes.",
                "Lire memory_bank/work_memory/index.txt pour voir l'état de la mission actuelle.",
                "Pour chaque entrée significative, décider si elle doit être promue en long_term (connaissance, décision, architecture).",
                "Écrire les éléments promus dans memory_bank/long_term sous forme de fichiers ou d'entrées structurées.",
                "Appeler vector_store_add sur le namespace approprié (short_term, work_memory, long_term) pour indexer les nouvelles informations importantes.",
                "Mettre à jour les statuts dans short_term/work_memory (planifié -> en cours -> accompli/échec).",
                "Nettoyer ou compacter short_term pour ne garder que les tâches réellement actives.",
            ],
            "suggested_trigger": {
                "frequency": "periodic",
                "interval_minutes": 30
            },
        }

    @server.tool()
    def memory_supervisor_plan(event_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Propose un plan de mise à jour de la mémoire en réponse à un événement.

        event_type peut être par exemple :
        - "workflow_end"
        - "agent_plan_completed"
        - "manual_note"
        - "error"
        """
        base: Dict[str, Any] = {
            "type": "memory_supervisor_plan",
            "event_type": event_type,
            "paths": _memory_paths_dict(),
            "context": context,
        }

        if event_type == "workflow_end":
            base["recommended_actions"] = [
                "Analyser le résumé du workflow (succès/échec, décisions, artefacts).",
                "Ajouter un résumé synthétique en long_term (journal de mission).",
                "Indexer le résumé dans le namespace long_term via vector_store_add.",
                "Mettre à jour work_memory pour refléter l'état de la mission (accomplie ou persistante).",
            ]
        elif event_type == "agent_plan_completed":
            base["recommended_actions"] = [
                "Prendre le plan final et les résultats clés, les résumer et les stocker en long_term.",
                "Indexer les résumés dans long_term pour permettre à l'OS de les retrouver plus tard.",
            ]
        elif event_type == "manual_note":
            base["recommended_actions"] = [
                "Ajouter la note textuelle en long_term avec un timestamp et une source=manual.",
                "Indexer la note dans long_term si elle est jugée utile.",
            ]
        else:
            base["recommended_actions"] = [
                "Journaliser l'événement en long_term, sous un sous-dossier ou une catégorie adaptée.",
            ]

        return base

    @server.tool()
    def memory_scheduler_plan() -> Dict[str, Any]:
        """
        Décrit comment brancher un scheduler externe (cron, job queue, etc.)
        pour appeler régulièrement memory_sweep_plan et appliquer les actions.
        """
        return {
            "type": "memory_scheduler_plan",
            "suggested_calls": [
                {
                    "tool": "memory_sweep_plan",
                    "frequency": "periodic",
                    "interval_minutes": 30,
                    "note": "Le modèle doit ensuite exécuter les actions en utilisant fs_* et vector_store_* selon le plan.",
                }
            ],
            "paths": _memory_paths_dict(),
        }
