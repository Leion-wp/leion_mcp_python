
from fastmcp import FastMCP


def register_asset_creator_tools(server: FastMCP):

    @server.tool()
    def asset_brandkit_plan(name: str, vibe: str = "modern"):
        """
        Plan de création d'une identité visuelle (brandkit) pour une marque.
        """
        return {
            "name": name,
            "vibe": vibe,
            "elements": [
                "palette_couleurs",
                "typo",
                "logo_variantes",
                "bannières",
            ],
        }

    @server.tool()
    def asset_logo_brief(name: str, slogan: str = ""):
        """
        Prépare un brief de logo utilisable avec un générateur d'images.
        """
        return {
            "name": name,
            "slogan": slogan,
        }

    @server.tool()
    def asset_banner_brief(text: str, format: str = "16:9"):
        """
        Prépare un brief de bannière.
        """
        return {
            "text": text,
            "format": format,
        }
