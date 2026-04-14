from typing import Any, Dict

from fastmcp import FastMCP


def register_auto_tester_tools(server: FastMCP):

    @server.tool()
    def test_generate_plan(path: str):
        """
        Plan pour générer des tests sur un projet.
        """
        return {
            "project_path": path,
            "steps": [
                "Identifier les points critiques à tester.",
                "Lister les fonctions/endpoints principaux.",
                "Générer des tests unitaires et/ou d'intégration.",
            ],
        }

    @server.tool()
    def test_run_plan(path: str):
        """
        Plan pour exécuter la suite de tests.
        """
        return {
            "project_path": path,
            "commands": ["pytest", "npm test"],
        }

    @server.tool()
    def test_report_plan(path: str):
        """
        Plan pour agréger les résultats de tests.
        """
        return {
            "project_path": path,
            "artifacts": ["coverage.xml", "junit.xml"],
        }
