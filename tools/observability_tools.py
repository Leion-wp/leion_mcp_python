import os
from typing import Any, Dict

from fastmcp import FastMCP


def register_observability_tools(server: FastMCP):

    @server.tool()
    def os_health_check():
        """
        Retourne un snapshot statique de la config connue par l'OS.
        """
        return {
            "services": {
                "flowise": os.getenv("FLOWISE_BASE_URL", ""),
                "composio": os.getenv("COMPOSIO_BASE_URL", ""),
                "vector_store": os.getenv("VECTOR_STORE_BASE_URL", ""),
            },
            "llm_providers": {
                "openai": bool(os.getenv("OPENAI_API_KEY")),
                "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
                "mistral": bool(os.getenv("MISTRAL_API_KEY")),
                "groq": bool(os.getenv("GROQ_API_KEY")),
                "openrouter": bool(os.getenv("OPENROUTER_API_KEY")),
                "ollama": os.getenv("OLLAMA_BASE_URL", ""),
            },
        }

    @server.tool()
    def os_log_event(source: str, event_type: str, payload: Dict[str, Any]):
        """
        Prépare un log structuré (à écrire ensuite dans un fichier ou une base).
        """
        return {
            "source": source,
            "type": event_type,
            "payload": payload,
        }

    @server.tool()
    def os_log_query_plan(filters: Dict[str, Any]):
        """
        Plan de requête de logs. Le stockage réel est à implémenter ailleurs.
        """
        return {
            "filters": filters,
        }
