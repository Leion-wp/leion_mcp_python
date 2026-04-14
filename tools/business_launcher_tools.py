from typing import Any, Dict, List

from fastmcp import FastMCP


def register_business_launcher_tools(server: FastMCP):

    @server.tool()
    def business_launch_plan(niche: str, objective: str, constraints: str = ""):
        """
        Génère un plan structuré pour lancer un business dans une niche donnée.

        IMPORTANT :
        - Ce tool ne déploie rien directement.
        - Il fournit un plan que le modèle peut suivre en appelant d'autres tools.
        """
        steps: List[Dict[str, Any]] = [
            {
                "id": "research",
                "label": "Recherche marché et positionnement",
                "description": "Analyser la niche, les concurrents, le public cible et les offres existantes.",
            },
            {
                "id": "offer",
                "label": "Définir l'offre",
                "description": "Clarifier la promesse, la transformation, le pricing et le modèle économique.",
            },
            {
                "id": "assets",
                "label": "Créer les assets principaux",
                "description": "Landing page, emails, scripts de vente, contenus de présentation.",
            },
            {
                "id": "infrastructure",
                "label": "Mettre en place l'infrastructure technique",
                "description": "Repo, base de données, intégrations, automatisations essentielles.",
            },
            {
                "id": "acquisition",
                "label": "Stratégie d'acquisition",
                "description": "Définir canaux d'acquisition (contenu, ads, partenariats, outreach).",
            },
            {
                "id": "ops",
                "label": "Opérations et suivi",
                "description": "Mise en place du suivi des KPIs, support et amélioration continue.",
            },
        ]

        return {
            "niche": niche,
            "objective": objective,
            "constraints": constraints,
            "steps": steps,
        }
