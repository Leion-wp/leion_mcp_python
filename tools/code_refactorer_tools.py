from fastmcp import FastMCP


def register_code_refactorer_tools(server: FastMCP):

    @server.tool()
    def code_analysis_plan(path: str):
        """
        Donne un plan d'analyse de code pour un dossier/fichier donné.

        Le modèle doit ensuite lire les fichiers avec fs_tools et appliquer les refactors.
        """
        return {
            "target": path,
            "checks": [
                "style_consistency",
                "dead_code",
                "complexity",
                "duplication",
                "security_smells",
            ],
        }

    @server.tool()
    def code_refactor_plan(path: str, goals: str):
        """
        Décrit une stratégie de refactorisation pour un chemin donné.
        """
        return {
            "target": path,
            "goals": goals,
            "steps": [
                "Cartographier les fichiers concernés.",
                "Identifier les fonctions/classes principales.",
                "Proposer une nouvelle structure.",
                "Appliquer les modifications fichier par fichier.",
            ],
        }

    @server.tool()
    def code_patch_plan(path: str, description: str):
        """
        Prépare un plan de patch pour une modification ciblée.

        Le modèle doit ensuite générer les diff et utiliser fs_tools pour appliquer.
        """
        return {
            "target": path,
            "description": description,
        }
