from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP


DEFAULT_TIMEOUT_SECONDS = 60
MAX_TIMEOUT_SECONDS = 600
MAX_DIAGNOSTIC_CHARS = 16_384


def _error(code: str, message: str, **extra: Any) -> Dict[str, Any]:
    return {"ok": False, "error": {"code": code, "message": message}, **extra}


def _cli_repo() -> Optional[Path]:
    raw = os.getenv("LEION_CLI_REPO", "").strip()
    if not raw:
        return None
    return Path(raw).expanduser().resolve()


def _cli_entry() -> Optional[Path]:
    explicit = os.getenv("LEION_CLI_ENTRY", "").strip()
    if explicit:
        return Path(explicit).expanduser().resolve()

    repo = _cli_repo()
    if not repo:
        return None
    return (repo / "packages" / "cli" / "out" / "index.js").resolve()


def _allowed_roots() -> List[Path]:
    raw = os.getenv("LEION_RUNTIME_ALLOWED_ROOTS", "").strip()
    if not raw:
        return []

    roots: List[Path] = []
    for value in raw.split(os.pathsep):
        value = value.strip()
        if value:
            roots.append(Path(value).expanduser().resolve())
    return roots


def _is_within(path: Path, root: Path) -> bool:
    try:
        return os.path.commonpath([str(path), str(root)]) == str(root)
    except ValueError:
        # Different Windows drives, or otherwise incomparable roots.
        return False


def _resolve_workspace(workspace: str) -> Path:
    raw = (workspace or "").strip()
    if not raw:
        raise ValueError("workspace is required")

    roots = _allowed_roots()
    if not roots:
        raise PermissionError(
            "LEION_RUNTIME_ALLOWED_ROOTS is empty; workspace execution is disabled"
        )

    path = Path(raw).expanduser().resolve()
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(f"Workspace does not exist or is not a directory: {path}")

    if not any(_is_within(path, root) for root in roots):
        raise PermissionError("Workspace is outside LEION_RUNTIME_ALLOWED_ROOTS")

    return path


def _bounded(text: str) -> str:
    value = text or ""
    if len(value) <= MAX_DIAGNOSTIC_CHARS:
        return value
    return value[:MAX_DIAGNOSTIC_CHARS] + "\n...[truncated]"


def _run_cli(
    command: str,
    args: Optional[List[str]] = None,
    *,
    workspace: Optional[str] = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> Dict[str, Any]:
    repo = _cli_repo()
    entry = _cli_entry()

    if not repo or not entry:
        return _error(
            "LEION_CLI_NOT_CONFIGURED",
            "Set LEION_CLI_REPO or LEION_CLI_ENTRY before using the runtime MCP.",
        )
    if not repo.exists() or not repo.is_dir():
        return _error("LEION_CLI_REPO_NOT_FOUND", "LEION_CLI_REPO does not exist.")
    if not entry.exists() or not entry.is_file():
        return _error(
            "LEION_CLI_ENTRY_NOT_FOUND",
            "CLI build entry not found. Build cli_leion_engine or set LEION_CLI_ENTRY.",
        )

    try:
        timeout = int(timeout_seconds)
    except (TypeError, ValueError):
        return _error("LEION_CLI_TIMEOUT_INVALID", "timeout_seconds must be an integer.")
    if timeout < 1 or timeout > MAX_TIMEOUT_SECONDS:
        return _error(
            "LEION_CLI_TIMEOUT_INVALID",
            f"timeout_seconds must be between 1 and {MAX_TIMEOUT_SECONDS}.",
        )

    argv = [
        os.getenv("LEION_NODE_BIN", "node"),
        str(entry),
        command,
    ]

    if workspace is not None:
        try:
            resolved_workspace = _resolve_workspace(workspace)
        except FileNotFoundError as exc:
            return _error("LEION_WORKSPACE_NOT_FOUND", str(exc))
        except PermissionError as exc:
            return _error("LEION_WORKSPACE_FORBIDDEN", str(exc))
        except ValueError as exc:
            return _error("LEION_WORKSPACE_INVALID", str(exc))
        argv.extend(["--workspace", str(resolved_workspace)])

    argv.extend(args or [])
    argv.append("--json")

    try:
        completed = subprocess.run(
            argv,
            cwd=str(repo),
            capture_output=True,
            text=True,
            shell=False,
            timeout=timeout,
        )
    except FileNotFoundError:
        return _error(
            "LEION_NODE_NOT_FOUND",
            "Node executable not found. Set LEION_NODE_BIN if it is not on PATH.",
        )
    except subprocess.TimeoutExpired:
        return _error(
            "LEION_CLI_TIMEOUT",
            f"CLI command exceeded {timeout} seconds.",
            command=command,
        )
    except Exception as exc:
        return _error("LEION_CLI_EXEC_FAILED", str(exc), command=command)

    stdout = completed.stdout or ""
    stderr = completed.stderr or ""

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return _error(
            "LEION_CLI_RESPONSE_INVALID",
            "CLI stdout was not valid JSON.",
            command=command,
            returncode=completed.returncode,
            stdout_bytes=len(stdout.encode("utf-8", errors="replace")),
            stderr=_bounded(stderr),
        )

    return {
        "ok": completed.returncode == 0,
        "command": command,
        "returncode": completed.returncode,
        "data": payload,
        **({"stderr": _bounded(stderr)} if stderr else {}),
    }


def _workspace_call(
    command: str,
    workspace: str,
    args: Optional[List[str]] = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> Dict[str, Any]:
    return _run_cli(
        command,
        args=args,
        workspace=workspace,
        timeout_seconds=timeout_seconds,
    )


def register_leion_cli_runtime_tools(server: FastMCP) -> None:
    """Expose the bounded public cli_leion_engine protocol over MCP.

    This adapter intentionally does not expose arbitrary shell execution.
    Commands are passed to Node with shell=False and workspace-bearing calls
    are confined to LEION_RUNTIME_ALLOWED_ROOTS.
    """

    @server.tool()
    def leion_runtime_describe() -> Dict[str, Any]:
        """Return cli_leion_engine runtime protocol, contracts and capabilities."""
        return _run_cli("runtime_describe")

    @server.tool()
    def leion_runtime_catalog() -> Dict[str, Any]:
        """Return the public runtime capability catalog."""
        return _run_cli("catalog", ["--section", "capabilities"])

    @server.tool()
    def leion_runtime_validate_pipeline(
        workspace: str,
        pipeline: str,
    ) -> Dict[str, Any]:
        """Statically validate a pipeline inside an allowed workspace."""
        reference = (pipeline or "").strip()
        if not reference:
            return _error("PIPELINE_REQUIRED", "pipeline is required")
        return _workspace_call(
            "validate_pipeline",
            workspace,
            ["--pipeline", reference],
        )

    @server.tool()
    def leion_runtime_run_pipeline(
        workspace: str,
        pipeline: str,
        correlation_id: Optional[str] = None,
        from_step: Optional[str] = None,
        dry_run: bool = False,
        detached: bool = True,
        timeout_seconds: int = 120,
    ) -> Dict[str, Any]:
        """Run a validated Leion pipeline through the CLI runtime.

        Detached execution is the default so MCP callers receive a stable run
        identity and can use status/log/control tools without holding a request
        open for the lifetime of the pipeline.
        """
        reference = (pipeline or "").strip()
        if not reference:
            return _error("PIPELINE_REQUIRED", "pipeline is required")

        args = ["--pipeline", reference]
        if from_step:
            args.extend(["--from", str(from_step)])
        if dry_run:
            args.append("--dry_run")
        if detached:
            args.append("--detached")
        if correlation_id:
            if not detached:
                return _error(
                    "RUN_CORRELATION_REQUIRES_DETACHED",
                    "correlation_id requires detached=True",
                )
            args.extend(["--correlation_id", str(correlation_id)])

        return _workspace_call(
            "run_pipeline",
            workspace,
            args,
            timeout_seconds=timeout_seconds,
        )

    @server.tool()
    def leion_runtime_run_status(
        workspace: str,
        run_id: str,
    ) -> Dict[str, Any]:
        """Read status for a detached/runtime/correlation run identity."""
        value = (run_id or "").strip()
        if not value:
            return _error("RUN_ID_REQUIRED", "run_id is required")
        return _workspace_call("run_status", workspace, ["--run_id", value])

    @server.tool()
    def leion_runtime_run_list(workspace: str) -> Dict[str, Any]:
        """List persisted runtime runs for an allowed workspace."""
        return _workspace_call("run_list", workspace)

    @server.tool()
    def leion_runtime_run_logs(
        workspace: str,
        run_id: str,
        cursor: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Read a bounded page of structured runtime events."""
        value = (run_id or "").strip()
        if not value:
            return _error("RUN_ID_REQUIRED", "run_id is required")
        if limit < 1 or limit > 200:
            return _error("RUN_LIMIT_INVALID", "limit must be between 1 and 200")

        args = ["--run_id", value, "--limit", str(limit)]
        if cursor:
            args.extend(["--cursor", str(cursor)])
        return _workspace_call("run_logs", workspace, args)

    @server.tool()
    def leion_runtime_pause(
        workspace: str,
        run_id: str,
    ) -> Dict[str, Any]:
        """Request a safe pipeline pause."""
        value = (run_id or "").strip()
        if not value:
            return _error("RUN_ID_REQUIRED", "run_id is required")
        return _workspace_call("stop_pipeline", workspace, ["--run_id", value])

    @server.tool()
    def leion_runtime_resume(
        workspace: str,
        run_id: str,
    ) -> Dict[str, Any]:
        """Resume a paused pipeline."""
        value = (run_id or "").strip()
        if not value:
            return _error("RUN_ID_REQUIRED", "run_id is required")
        return _workspace_call("resume_pipeline", workspace, ["--run_id", value])

    @server.tool()
    def leion_runtime_cancel(
        workspace: str,
        run_id: str,
    ) -> Dict[str, Any]:
        """Cancel a pipeline run and its active terminal process tree."""
        value = (run_id or "").strip()
        if not value:
            return _error("RUN_ID_REQUIRED", "run_id is required")
        return _workspace_call("cancel_pipeline", workspace, ["--run_id", value])
