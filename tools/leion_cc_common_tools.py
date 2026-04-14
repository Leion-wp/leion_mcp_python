from typing import Any, Dict


# Identifiant de la resource MCP qui sert le widget HTML
WIDGET_RESOURCE_ID = "leion-cc://widget"


def make_text_content(text: str) -> Dict[str, Any]:
    return {"type": "text", "text": text}


def make_output(
    title: str,
    structured_content: Dict[str, Any],
    with_widget: bool = False,
) -> Dict[str, Any]:
    """
    Retour standard pour les tools orientés widget.

    - title : résumé pour le modèle
    - structured_content : payload pour le widget
    - with_widget : si True, on ajoute openai/outputTemplate vers la resource HTML
      du Control Center (leion-cc://widget).
    """
    meta: Dict[str, Any] = {}
    if with_widget:
        meta["openai/outputTemplate"] = {
            "resourceId": WIDGET_RESOURCE_ID,
            "mimeType": "text/html+skybridge",
        }

    return {
        "content": [make_text_content(title)],
        "structuredContent": structured_content,
        "_meta": meta,
    }
