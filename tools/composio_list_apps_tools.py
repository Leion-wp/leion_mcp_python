from typing import Any, Dict, List
from fastmcp import FastMCP

from .leion_cc_common_tools import make_output


# Fake dataset enrichi (en attendant le vrai client Composio)
_FAKE_APPS: List[Dict[str, Any]] = [
    {
        "id": "stripe",
        "name": "Stripe",
        "category": "payments",
        "connected": False,
        "auth_type": "oauth",
        "connect_url": "https://dashboard.composio.dev/connect/stripe",
        "docs_url": "https://stripe.com/docs/api",
        "actions_count": 64,
    },
    {
        "id": "paypal",
        "name": "PayPal",
        "category": "payments",
        "connected": False,
        "auth_type": "api_key",
        "connect_url": "https://developer.paypal.com/api/rest/",
        "docs_url": "https://developer.paypal.com/docs/api/overview/",
        "actions_count": 21,
    },
    {
        "id": "gumroad",
        "name": "Gumroad",
        "category": "payments",
        "connected": False,
        "auth_type": "api_key",
        "connect_url": "https://gumroad.com/settings/advanced",
        "docs_url": "https://gumroad.com/api",
        "actions_count": 8,
    },
    {
        "id": "kofi",
        "name": "Ko-fi",
        "category": "payments",
        "connected": False,
        "auth_type": "api_key",
        "connect_url": "https://ko-fi.com/manage/settings/api",
        "docs_url": "https://ko-fi.com/manage/help",
        "actions_count": 5,
    },
    {
        "id": "zapier",
        "name": "Zapier",
        "category": "automation",
        "connected": False,
        "auth_type": "oauth",
        "connect_url": "https://zapier.com/app/connections",
        "docs_url": "https://platform.zapier.com/docs",
        "actions_count": 110,
    },
    {
        "id": "notion",
        "name": "Notion",
        "category": "knowledge",
        "connected": True,
        "auth_type": "oauth",
        "connect_url": "https://dashboard.composio.dev/connect/notion",
        "docs_url": "https://developers.notion.com/docs",
        "actions_count": 34,
    },
    {
        "id": "slack",
        "name": "Slack",
        "category": "communication",
        "connected": True,
        "auth_type": "oauth",
        "connect_url": "https://dashboard.composio.dev/connect/slack",
        "docs_url": "https://api.slack.com/",
        "actions_count": 42,
    },
]


async def _fake_composio_list_apps() -> List[Dict[str, Any]]:
    """
    Enrich fake dataset.
    TODO: remplacer totalement par le vrai SDK/API Composio.
    """
    return _FAKE_APPS


def register_composio_list_apps_tools(server: FastMCP):

    @server.tool()
    async def composio_list_apps(category: str | None = None) -> Dict[str, Any]:
        """
        Liste les apps Composio disponibles + état de connexion + metadata utile.

        Args:
            category: optionnel, filtre (payments / automation / email / knowledge ...)
        """
        apps = await _fake_composio_list_apps()

        if category:
            apps = [a for a in apps if a["category"] == category.lower()]

        total = len(apps)
        connected = sum(1 for a in apps if a["connected"])
        categories: Dict[str, int] = {}
        for a in apps:
            categories[a["category"]] = categories.get(a["category"], 0) + 1

        structured = {
            "type": "composio_apps",
            "apps": apps,
            "summary": {
                "total": total,
                "connected": connected,
                "categories": categories,
            },
        }

        return make_output(
            "Liste des apps Composio",
            structured,
            with_widget=False,
        )
