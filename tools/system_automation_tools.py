from __future__ import annotations

import subprocess
import time
from typing import Any, Dict, List

from fastmcp import FastMCP

try:
    import pyautogui  # type: ignore
except Exception:  # pragma: no cover - si pyautogui n'est pas installé
    pyautogui = None  # type: ignore


# ---------------------- LOGIQUE TOOLS ----------------------


def system_open_app(command: str) -> Dict[str, Any]:
    """Ouvre une application via une commande système.

    Exemple :
      - 'notepad'
      - 'code'
      - 'chrome'
    """
    # shell=True pour supporter les commandes simples type Windows
    subprocess.Popen(command, shell=True)
    return {"status": "ok", "command": command}


def system_type_text(text: str, interval: float = 0.02) -> Dict[str, Any]:
    """Tape du texte dans la fenêtre active.

    Requiert pyautogui.
    """
    if pyautogui is None:
        return {"status": "error", "error": "pyautogui non disponible"}
    pyautogui.typewrite(text, interval=interval)
    return {"status": "ok", "typed": text}


def system_press_key(key: str) -> Dict[str, Any]:
    """Simule l'appui sur une touche (enter, tab, esc, etc.)."""
    if pyautogui is None:
        return {"status": "error", "error": "pyautogui non disponible"}
    pyautogui.press(key)
    return {"status": "ok", "key": key}


def system_hotkey(*keys: str) -> Dict[str, Any]:
    """Simule un raccourci clavier, ex : ("ctrl", "s"), ("alt", "tab")."""
    if pyautogui is None:
        return {"status": "error", "error": "pyautogui non disponible"}
    pyautogui.hotkey(*keys)
    return {"status": "ok", "keys": list(keys)}


def system_sleep(seconds: float) -> Dict[str, Any]:
    """Pause d'attente (utile pour laisser une app se lancer, etc.)."""
    time.sleep(seconds)
    return {"status": "ok", "slept": seconds}


# ---------------------- ENREGISTREMENT FASTMCP ----------------------


def register_system_automation_tools(server: FastMCP) -> None:
    """
    Enregistre les tools d'automatisation PC dans le MCP server.

    Pattern identique à register_agent_tools : on utilise @server.tool().
    """

    @server.tool()
    def system_open_app_tool(command: str) -> Dict[str, Any]:
        return system_open_app(command)

    @server.tool()
    def system_type_text_tool(text: str, interval: float = 0.02) -> Dict[str, Any]:
        return system_type_text(text, interval)

    @server.tool()
    def system_press_key_tool(key: str) -> Dict[str, Any]:
        return system_press_key(key)

    @server.tool()
    def system_hotkey_tool(keys: List[str]) -> Dict[str, Any]:
        # On passe par une liste pour le schema, puis on déplie.
        return system_hotkey(*keys)

    @server.tool()
    def system_sleep_tool(seconds: float) -> Dict[str, Any]:
        return system_sleep(seconds)
