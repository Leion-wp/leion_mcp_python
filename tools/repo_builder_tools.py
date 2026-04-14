from pathlib import Path
from fastmcp import FastMCP


def register_repo_builder_tools(server: FastMCP):

    @server.tool()
    def repo_scaffold_plan(path: str, project_type: str, stack: str = "python"):
        """
        Génère un plan de structure de projet sans écrire de fichiers.

        Le modèle peut ensuite utiliser fs_tools pour créer les fichiers.
        """
        root = Path(path)

        if project_type == "backend_api":
            layout = [
                "app/__init__.py",
                "app/main.py",
                "app/routes/__init__.py",
                "tests/__init__.py",
                "tests/test_smoke.py",
                "pyproject.toml",
                "README.md",
            ]
        elif project_type == "frontend_spa":
            layout = [
                "src/index.tsx",
                "src/App.tsx",
                "public/index.html",
                "package.json",
                "README.md",
            ]
        else:
            layout = ["README.md"]

        files = [str(root / rel) for rel in layout]

        return {
            "root": str(root),
            "project_type": project_type,
            "stack": stack,
            "files": files,
        }

    @server.tool()
    def repo_autodoc_plan(path: str):
        """
        Décrit un plan de documentation à générer pour un repo existant.
        """
        return {
            "repo_path": path,
            "docs": [
                "README.md",
                "ARCHITECTURE.md",
                "CONTRIBUTING.md",
                "CHANGELOG.md",
            ],
        }

    @server.tool()
    def repo_hardening_plan(path: str):
        """
        Plan de durcissement du projet : lint, tests, CI, sécurité.
        
        """
        return {
            "repo_path": path,
            "steps": [
                "Ajouter configuration de lint (ruff/eslint).",
                "Ajouter tests unitaires de base.",
                "Ajouter workflow CI (lint + tests).",
                "Configurer dépendances et mises à jour.",
            ],
        }
