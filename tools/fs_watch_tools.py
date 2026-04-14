from pathlib import Path
from fastmcp import FastMCP

# NOTE:
# Real-time filesystem watching with callbacks is outside the typical MCP
# request/response model. This tool instead provides a snapshot-style
# "watch": it lists files changed since a given mtime threshold.


def register_fs_watch_tools(server: FastMCP):

    @server.tool()
    def fs_watch(path: str, since_mtime: float):
        """
        Return a list of files under `path` whose modification time is
        greater than `since_mtime` (Unix timestamp).

        This allows the model to periodically poll for changes and react to
        them by calling other tools (build, test, re-index, etc.).
        """
        root = Path(path)
        if not root.exists():
            return {"error": "path does not exist", "path": path}
        if not root.is_dir():
            return {"error": "path is not a directory", "path": path}

        changed = []
        for p in root.rglob('*'):
            if p.is_file():
                try:
                    mtime = p.stat().st_mtime
                except Exception:
                    continue
                if mtime > since_mtime:
                    changed.append({"path": str(p), "mtime": mtime})

        return {"root": path, "since_mtime": since_mtime, "changed": changed}
