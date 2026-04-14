from typing import Any, Dict, List

from fastmcp import FastMCP

from .composio_list_apps_tools import _FAKE_APPS


def _find_app(app_name: str) -> Dict[str, Any] | None:
    """
    Trouve une app par id ou nom.
    """
    name = app_name.strip().lower()
    for app in _FAKE_APPS:
        if app["id"].lower() == name or app["name"].lower() == name:
            return app
    return None


def register_composio_connect_app_tools(server: FastMCP):

    @server.tool()
    async def composio_connect_app(app_name: str) -> Dict[str, Any]:
        """
        Prépare la connexion d'une application Composio (Stripe, Paypal, Gumroad, Ko-fi, etc.).

        Cette fonction NE réalise PAS la connexion elle-même, mais renvoie :
          - le type d'auth (oauth / api_key)
          - l'URL de connexion ou la page de clé API
          - un texte clair pour l'utilisateur

        Args:
            app_name: nom ou id de l'app (ex: "stripe", "paypal", "gumroad", "kofi")

        Returns:
            dict avec :
                app: meta de l'app
                status: "already_connected" | "needs_connection" | "not_found"
                message: texte lisible explicatif
        """
        app = _find_app(app_name)
        if not app:
            return {
                "app": None,
                "status": "not_found",
                "message": f"Je ne trouve pas d'app Composio correspondant à '{app_name}'.",
            }

        if app.get("connected"):
            return {
                "app": app,
                "status": "already_connected",
                "message": f"{app['name']} est déjà connecté via Composio. Tu peux l'utiliser immédiatement dans tes workflows.",
            }

        auth_type = app.get("auth_type", "oauth")
        connect_url = app.get("connect_url")
        docs_url = app.get("docs_url")

        if auth_type == "oauth":
            message = (
                f"{app['name']} n'est pas encore connecté.\n\n"
                f"👉 Clique sur ce lien pour autoriser l'app via Composio :\n{connect_url}\n\n"
                "Une fois terminé, reviens ici et dis-moi que c'est fait, je continuerai le workflow."
            )
        else:  # api_key
            message = (
                f"{app['name']} utilise une clé API.\n\n"
                f"1. Va sur cette page pour récupérer ta clé :\n{connect_url}\n"
                "2. Copie la clé API.\n"
                "3. Reviens ici et colle-la dans un message, je t'aiderai à la stocker proprement via Composio."
            )
            if docs_url:
                message += f"\n\nDocs : {docs_url}"

        return {
            "app": app,
            "status": "needs_connection",
            "message": message,
            "auth_type": auth_type,
            "connect_url": connect_url,
            "docs_url": docs_url,
        }
