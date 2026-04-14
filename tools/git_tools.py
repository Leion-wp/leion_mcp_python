import subprocess
from pathlib import Path
from typing import Optional
from fastmcp import FastMCP


def _run_git_command(repo_path: str, args: list[str]) -> dict:
    """Run a safe git command in the given repository and return structured output."""
    try:
        cwd = Path(repo_path) if repo_path else Path.cwd()
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            shell=False,
        )
        return {
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "args": ["git"] + args,
            "repo_path": str(cwd),
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "args": ["git"] + args, "repo_path": repo_path}


def register_git_tools(server: FastMCP):

    @server.tool()
    def git_init(repo_path: str, initial_branch: str = "main"):
        """Initialize a new git repository in repo_path."""
        # Use -b to set default branch name
        return _run_git_command(repo_path, ["init", "-b", initial_branch])

    @server.tool()
    def git_config_set(repo_path: str, key: str, value: str, is_global: bool = False):
        """Set a git config key/value (local by default)."""
        args = ["config"]
        if is_global:
            args.append("--global")
        args += [key, value]
        return _run_git_command(repo_path, args)

    @server.tool()
    def git_config_list(repo_path: str, is_global: bool = False):
        """List git config entries (local by default)."""
        args = ["config"]
        if is_global:
            args.append("--global")
        args.append("--list")
        return _run_git_command(repo_path, args)

    @server.tool()
    def git_status(repo_path: str):
        """Run `git status -sb` in the given repository path."""
        return _run_git_command(repo_path, ["status", "-sb"])

    @server.tool()
    def git_diff(repo_path: str, pathspec: Optional[str] = None):
        """Show `git diff` for the given repo."""
        args = ["diff"]
        if pathspec:
            args.append(pathspec)
        return _run_git_command(repo_path, args)

    @server.tool()
    def git_log(repo_path: str, max_commits: int = 20):
        """Show a short log of recent commits."""
        args = ["log", f"-n{max_commits}", "--oneline", "--decorate"]
        return _run_git_command(repo_path, args)

    @server.tool()
    def git_commit(repo_path: str, message: str):
        """Create a commit with the given message (assumes staged files)."""
        return _run_git_command(repo_path, ["commit", "-m", message])

    @server.tool()
    def git_add(repo_path: str, pathspec: str = "."):
        """Stage files for commit using `git add` (default: all)."""
        return _run_git_command(repo_path, ["add", pathspec])

    @server.tool()
    def git_branch(repo_path: str):
        """List local branches and highlight the current one."""
        return _run_git_command(repo_path, ["branch"])

    @server.tool()
    def git_checkout(repo_path: str, branch: str):
        """Checkout an existing branch (does not create new branches)."""
        return _run_git_command(repo_path, ["checkout", branch])
