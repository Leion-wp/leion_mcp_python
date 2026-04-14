from typing import List
from fastmcp import FastMCP


def register_llm_router_tools(server: FastMCP):

    @server.tool()
    def llm_route(goal: str, priority: str = "default"):
        """
        Propose quel fournisseur de LLM utiliser pour un objectif donné.

        Ceci NE FAIT PAS d'appel réseau.
        Ça renvoie juste une recommandation structurée que le modèle peut suivre.
        """
        priority = priority.lower()

        if priority == "low_cost":
            candidates = ["mistral", "groq", "openrouter"]
        elif priority == "speed":
            candidates = ["groq", "mistral", "openai"]
        elif priority == "quality":
            candidates = ["openai", "anthropic", "mistral"]
        else:
            candidates = ["openai", "anthropic", "mistral", "groq", "openrouter", "ollama"]

        return {
            "goal": goal,
            "priority": priority,
            "recommended_providers": candidates,
            "note": "Le modèle doit choisir explicitement un provider et appeler l'API correspondante via les tools appropriés.",
        }

    @server.tool()
    def llm_batch_plan(task_description: str, items: List[str]):
        """
        Crée un plan de batch pour traiter une liste d'éléments avec un LLM.

        Exemple : générer des descriptions produits, emails, posts, etc.
        """
        batch = []
        for idx, item in enumerate(items, start=1):
            batch.append({
                "id": f"item-{idx}",
                "input": item,
                "status": "pending",
            })

        return {
            "task": task_description,
            "items": batch,
        }

    @server.tool()
    def llm_evaluation_plan(criteria: str, samples: List[str]):
        """
        Plan d'évaluation de textes selon des critères donnés.

        Utilisé pour que le modèle génère ensuite les évaluations lui-même.
        """
        return {
            "criteria": criteria,
            "samples": samples,
        }
