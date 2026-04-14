from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from fastmcp import FastMCP


def _apply_simple_patch(root: Path, patch: str) -> Dict[str, Any]:
    """
    Apply a very simple multi-file patch under ``root``.

    Ce n'est PAS un moteur de patch git complet. C’est volontairement
    limité pour les workflows assistant → code, où le patch contient,
    pour chaque fichier, le contenu final sous forme de lignes de
    contexte + lignes ajoutées.

    Sous-ensemble supporté :

      - lignes "diff --git ..."   → utilisées uniquement pour séparer les fichiers
      - lignes "+++ <path>"       → sélection du fichier cible
      - lignes "@@ ... @@"        → début d’un hunk (juste un marqueur)
      - lignes commençant par "+" → ligne ajoutée (contenu final)
      - lignes commençant par "-" → ligne supprimée (on ignore)
      - le reste = lignes de contexte recopiées telles quelles

    Pour chaque fichier on reconstruit simplement le nouveau contenu
    à partir des lignes de contexte et des lignes "+", puis on
    écrase le fichier cible.
    """

    lines = patch.splitlines()
    file_changes: List[str] = []
    current_file: str | None = None
    buffer: List[str] = []
    mode: str | None = None

    def flush() -> None:
        nonlocal buffer, current_file
        if not current_file:
            return
        target = root / current_file
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(buffer), encoding="utf-8")
        file_changes.append(current_file)
        buffer = []
        current_file = None

    for line in lines:
        if line.startswith("diff --git"):
            # nouveau fichier → flush du précédent
            flush()
            continue

        if line.startswith("+++ "):
            # Exemple: "+++ b/src/components/NodePalette.tsx"
            path = line[4:].strip()
            if path.startswith("a/") or path.startswith("b/"):
                path = path[2:]
            current_file = path
            buffer = []
            mode = None
            continue

        if line.startswith("@@"):
            mode = "hunk"
            continue

        if mode == "hunk" and current_file:
            if line.startswith("+") and not line.startswith("+++"):
                buffer.append(line[1:])
            elif line.startswith("-") and not line.startswith("---"):
                # ligne supprimée → on ne la recopie pas
                continue
            else:
                # ligne de contexte (inchangée)
                buffer.append(line)

    # dernier fichier
    flush()
    return {"status": "ok", "files": file_changes}


def register_fs_patch_tools(server: FastMCP) -> None:
    """
    Enregistre les tools de patch dans le MCP server.
    Pattern identique à register_fs_tools / register_orchestrator_tools.
    """

    @server.tool()
    def fs_patch(root_path: str, patch: str) -> Dict[str, Any]:
        """
        Applique un patch "unified diff" relatif à ``root_path``.

        Attention : on supporte seulement le sous-ensemble décrit
        dans _apply_simple_patch (usage assistant → code, pas un
        moteur git complet).
        """
        root = Path(root_path)
        if not root.exists():
            return {"error": f"Root path does not exist: {root_path}"}

        return _apply_simple_patch(root, patch)
