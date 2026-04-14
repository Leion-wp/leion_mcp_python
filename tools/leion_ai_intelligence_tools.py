from typing import Any, Dict, List, Literal, Optional

from fastmcp import FastMCP

from .leion_cc_common_tools import make_output

IntentType = Literal["payments", "ecommerce", "email", "automation", "content", "analytics", "unknown"]


# ---- Catalogues statiques v0 (à affiner dynamiquement ensuite) ----

PAYMENT_APPS = [
    {"id": "stripe", "label": "Stripe", "auth_type": "oauth", "docs": "https://stripe.com/docs"},
    {"id": "paypal", "label": "PayPal", "auth_type": "oauth", "docs": "https://developer.paypal.com/api/rest/"},
    {"id": "gumroad", "label": "Gumroad", "auth_type": "api_key", "docs": "https://gumroad.com/settings/advanced"},
    {"id": "ko_fi", "label": "Ko-fi", "auth_type": "api_key", "docs": "https://ko-fi.com/manage/settings/api"},
    {"id": "paddle", "label": "Paddle", "auth_type": "oauth", "docs": "https://developer.paddle.com/"},
]

EMAIL_APPS = [
    {"id": "gmail", "label": "Gmail", "auth_type": "oauth", "docs": "https://developers.google.com/gmail/api"},
    {"id": "resend", "label": "Resend", "auth_type": "api_key", "docs": "https://resend.com/docs"},
    {"id": "sendgrid", "label": "SendGrid", "auth_type": "api_key", "docs": "https://docs.sendgrid.com"},
    {"id": "zapier_email", "label": "Zapier Email", "auth_type": "oauth", "docs": "https://zapier.com/apps/email/integrations"},
]

AUTOMATION_APPS = [
    {"id": "zapier", "label": "Zapier", "auth_type": "oauth", "docs": "https://zapier.com/apps"},
    {"id": "make", "label": "Make (Integromat)", "auth_type": "oauth", "docs": "https://www.make.com/en/integrations"},
    {"id": "n8n", "label": "n8n", "auth_type": "none", "docs": "https://n8n.io/integrations"},
]

ECOMMERCE_APPS = [
    {"id": "shopify", "label": "Shopify", "auth_type": "oauth", "docs": "https://shopify.dev"},
    {"id": "woocommerce", "label": "WooCommerce", "auth_type": "api_key", "docs": "https://woocommerce.com/document/woocommerce-rest-api/"},
    {"id": "lemonsqueezy", "label": "Lemon Squeezy", "auth_type": "api_key", "docs": "https://docs.lemonsqueezy.com"},
]


def _detect_intent(goal: str) -> IntentType:
    g = goal.lower()
    if any(k in g for k in ["payer", "paiement", "payment", "checkout", "stripe", "paypal", "gumroad", "kofi", "ko-fi"]):
        return "payments"
    if any(k in g for k in ["boutique", "ecommerce", "shopify", "woocommerce", "store"]):
        return "ecommerce"
    if any(k in g for k in ["email", "newsletter", "mailing"]):
        return "email"
    if any(k in g for k in ["zapier", "automatisation", "automation", "scenario make", "workflow"]):
        return "automation"
    if any(k in g for k in ["analytics", "tracking", "utm"]):
        return "analytics"
    return "unknown"


def _intent_catalog(intent: IntentType) -> List[Dict[str, Any]]:
    if intent == "payments":
        return PAYMENT_APPS
    if intent == "ecommerce":
        return ECOMMERCE_APPS
    if intent == "email":
        return EMAIL_APPS
    if intent == "automation":
        return AUTOMATION_APPS
    return []


async def _fake_composio_list_connected_apps() -> List[Dict[str, Any]]:
    """TODO: remplacer par un call vers tes vrais tools composio_* pour lister
    les apps vraiment connectées.
    """
    # Exemple de structure : app, connected, auth_type
    return [
        {"app": "notion", "connected": True, "auth_type": "oauth"},
        {"app": "slack", "connected": True, "auth_type": "oauth"},
    ]


def _build_recommendations(intent: IntentType, goal: str, connected_apps: List[Dict[str, Any]]) -> Dict[str, Any]:
    cat = _intent_catalog(intent)
    connected_ids = {a["app"] for a in connected_apps if a.get("connected")}

    primary: List[Dict[str, Any]] = []
    alternatives: List[Dict[str, Any]] = []

    for app in cat:
        is_connected = app["id"] in connected_ids
        base = {
            "id": app["id"],
            "label": app["label"],
            "auth_type": app["auth_type"],
            "docs": app["docs"],
            "connected": is_connected,
        }
        if is_connected:
            primary.append({**base, "reason": "déjà connecté via Composio"})
        else:
            alternatives.append({**base, "reason": "bonne option à connecter pour ce besoin"})

    return {
        "intent": intent,
        "goal": goal,
        "connected_apps": connected_apps,
        "primary_options": primary,
        "alternative_options": alternatives,
    }


def _build_human_summary(data: Dict[str, Any]) -> str:
    intent = data["intent"]
    goal = data["goal"]
    primary = data["primary_options"]
    alts = data["alternative_options"]

    lines: List[str] = []
    lines.append(f"🎯 Objectif compris : {goal}")

    if intent == "payments":
        lines.append("→ J'interprète ça comme un besoin de PAIEMENT / MONÉTISATION.")
    elif intent == "email":
        lines.append("→ J'interprète ça comme un besoin EMAIL / NEWSLETTER.")
    elif intent == "ecommerce":
        lines.append("→ J'interprète ça comme un besoin E-COMMERCE / BOUTIQUE.")
    elif intent == "automation":
        lines.append("→ J'interprète ça comme un besoin d'AUTOMATISATION / WORKFLOWS.")
    else:
        lines.append("→ Je ne catégorise pas encore ça parfaitement, mais je propose déjà des options.")

    if primary:
        lines.append("✅ Déjà disponible dans ton écosystème :")
        for p in primary:
            lines.append(f"- {p['label']} (connecté, {p['auth_type']}) – {p['reason']}")

    if alts:
        lines.append("Alternatives pertinentes que tu peux connecter :")
        for a in alts:
            lines.append(f"- {a['label']} ({a['auth_type']}) – {a['reason']}")

        lines.append("Tu peux en connecter plusieurs (ex: Stripe + Gumroad + Ko-fi).")

    if intent == "payments":
        lines.append("Exemples de flows que je peux ensuite piloter :")
        lines.append("- Page de paiement simple pour un produit digital")
        lines.append("- Abonnements mensuels récurrents")
        lines.append("- Donation / tip (Ko-fi, Paypal)")

    lines.append("Dis-moi :")
    lines.append("- 'Connecte STRIPE' ou 'Je préfère PAYPAL'")
    lines.append("- ou 'Propose-moi un flow complet de A à Z'")

    return "".join(lines)


def register_leion_ai_intelligence_tools(server: FastMCP):

    @server.tool()
    async def leion_ai_intelligence(
        goal: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Moteur d'intelligence proactif pour Leion OS.

        - Analyse le goal (ex: "je veux prendre des paiements")
        - Détecte une intention (paiements, email, ecommerce, automation, etc.)
        - Croise avec les intégrations déjà connectées (Composio, mock v0)
        - Propose des options primaires + alternatives (Stripe, Paypal, Gumroad, Ko-fi, etc.)

        TODO v2/v3 :
        - Brancher sur tes vrais outils composio_* pour la réalité des connexions.
        - Ajouter la lecture de Flowise / Zapier / business pour proposer encore mieux.
        """
        intent = _detect_intent(goal)
        connected = await _fake_composio_list_connected_apps()
        data = _build_recommendations(intent, goal, connected)

        structured = {
            "type": "leion_ai_intelligence",
            "data": data,
        }

        summary = _build_human_summary(data)

        return make_output(
            summary,
            structured,
            with_widget=False,
        )
