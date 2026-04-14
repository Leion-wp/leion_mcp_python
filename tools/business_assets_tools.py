from typing import Any, Dict

from fastmcp import FastMCP


def register_business_assets_tools(server: FastMCP):

    @server.tool()
    def business_assets_plan(name: str, offer: str, tone: str = "pro"):
        """
        Décrit tous les assets à produire pour un business donné.

        Le modèle peut ensuite générer chaque asset individuellement (landing, emails, ads...).
        """
        assets: Dict[str, Any] = {
            "landing_page": {
                "description": "Page de vente principale avec structure sections, CTA, FAQ, preuves sociales.",
                "status": "pending",
            },
            "email_sequence": {
                "description": "Séquence email (welcome, nurture, pitch, relance).",
                "status": "pending",
            },
            "ads": {
                "description": "Variantes de pubs pour réseaux sociaux / search.",
                "status": "pending",
            },
            "social_content": {
                "description": "Calendrier éditorial et exemples de posts.",
                "status": "pending",
            },
            "scripts": {
                "description": "Scripts pour appels, DM, vidéos, démos.",
                "status": "pending",
            },
        }

        return {
            "name": name,
            "offer": offer,
            "tone": tone,
            "assets": assets,
        }
