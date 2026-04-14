from typing import Dict

from fastmcp import FastMCP


def register_ui_component_generator_tools(server: FastMCP):

    @server.tool()
    def ui_component_plan(component_type: str, name: str, description: str):
        """
        Décrit un composant UI à générer (React, HTML, etc.).
        """
        return {
            "type": component_type,
            "name": name,
            "description": description,
        }

    @server.tool()
    def ui_layout_plan(page_name: str, sections: Dict[str, str]):
        """
        Plan d'une page avec sections nommées.
        """
        return {
            "page_name": page_name,
            "sections": sections,
        }
