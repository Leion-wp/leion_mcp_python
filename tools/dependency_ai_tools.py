from fastmcp import FastMCP


def register_dependency_ai_tools(server: FastMCP):

    @server.tool()
    def project_dependencies_scan_plan(path: str):
        """
        Plan pour scanner les dépendances d'un projet (Python, JS, etc.).
        """
        return {
            "project_path": path,
            "files_to_check": [
                "requirements.txt",
                "pyproject.toml",
                "package.json",
                "package-lock.json",
                "pnpm-lock.yaml",
            ],
        }

    @server.tool()
    def project_dependencies_upgrade_plan(path: str):
        """
        Plan pour mettre à jour les dépendances d'un projet.
        """
        return {
            "project_path": path,
            "steps": [
                "Lister les dépendances actuelles.",
                "Identifier les versions obsolètes.",
                "Proposer des mises à jour compatibles.",
                "Mettre à jour les fichiers de dépendances.",
                "Lancer les tests.",
            ],
        }
