from typing import Any, Dict, List

from fastmcp import FastMCP


def register_fs_monitor_pro_tools(server: FastMCP):

    @server.tool()
    def fs_monitor_plan(path: str, last_snapshot: Dict[str, Any] | None = None):
        """
        Prépare un plan de surveillance de fichier avancé.

        La collecte réelle (hash, timestamps) est à faire via fs_tools.
        """
        return {
            "path": path,
            "last_snapshot": last_snapshot or {},
            "note": "Le modèle doit comparer l'état actuel des fichiers avec last_snapshot en utilisant fs_list_directory + fs_read_file.",
        }
