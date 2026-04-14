from typing import Any, Dict

from fastmcp import FastMCP


def register_profile_ai_tools(server: FastMCP):

    @server.tool()
    def profile_update(event: Dict[str, Any]):
        """
        Prépare un événement de profil utilisateur/système à stocker.
        """
        return {
            "event": event,
        }

    @server.tool()
    def profile_get_plan():
        """
        Plan de récupération du profil courant.
        Le stockage réel se fait dans la vector DB ou des fichiers.
        """
        return {
            "action": "get_profile",
        }

    @server.tool()
    def profile_reset_plan():
        """
        Plan pour reset le profil.
        """
        return {
            "action": "reset_profile",
        }
