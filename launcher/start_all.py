from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = Path(__file__).with_name("servers.json")
DEFAULT_LOG_DIR = REPO_ROOT / ".logs" / "mcp"
HEALTH_TIMEOUT_SECONDS = 10.0
RESTART_DELAY_SECONDS = 2.0
MAX_RESTARTS = 5


@dataclass
class ManagedServer:
    spec: Dict[str, Any]
    process: subprocess.Popen
    log_handle: Any
    restarts: int = 0


def load_config(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or not isinstance(data.get("servers"), list):
        raise ValueError("Launcher config must contain a 'servers' array.")
    return data


def port_open(port: int, host: str = "127.0.0.1") -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.35):
            return True
    except OSError:
        return False


def wait_for_port(port: int, timeout: float = HEALTH_TIMEOUT_SECONDS) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if port_open(port):
            return True
        time.sleep(0.2)
    return False


def selected_specs(config: Dict[str, Any], profile: str) -> List[Dict[str, Any]]:
    selected = []
    for raw in config["servers"]:
        if not isinstance(raw, dict):
            continue
        profiles = raw.get("profiles") or []
        if profile in profiles:
            selected.append(raw)
    return selected


def process_creation_kwargs() -> Dict[str, Any]:
    if os.name == "nt":
        return {
            "creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        }
    return {"start_new_session": True}


def launch_server(spec: Dict[str, Any], log_dir: Path) -> Optional[ManagedServer]:
    name = str(spec["name"])
    module = str(spec["module"])
    port = int(spec["port"])

    if port_open(port):
        print(f"~ {name:<16} :{port} already in use; treating it as externally managed")
        return None

    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{name}.log"
    log_handle = log_path.open("a", encoding="utf-8", buffering=1)
    log_handle.write(
        f"\n=== launch {time.strftime('%Y-%m-%d %H:%M:%S')} module={module} port={port} ===\n"
    )

    env = os.environ.copy()
    env["PORT"] = str(port)

    process = subprocess.Popen(
        [sys.executable, "-m", module],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        **process_creation_kwargs(),
    )

    managed = ManagedServer(spec=spec, process=process, log_handle=log_handle)

    if wait_for_port(port):
        print(f"✓ {name:<16} :{port} pid={process.pid}")
        return managed

    code = process.poll()
    if code is None:
        print(
            f"! {name:<16} :{port} did not open within {HEALTH_TIMEOUT_SECONDS:.0f}s "
            f"(pid={process.pid}); see {log_path}"
        )
        return managed

    print(f"✗ {name:<16} exited code={code}; see {log_path}")
    log_handle.close()
    return None


def terminate_process_tree(managed: ManagedServer) -> None:
    process = managed.process
    if process.poll() is not None:
        return

    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            text=True,
            check=False,
        )
        return

    try:
        os.killpg(process.pid, 15)
    except ProcessLookupError:
        return


def close_managed(managed: ManagedServer) -> None:
    try:
        terminate_process_tree(managed)
        managed.process.wait(timeout=5)
    except Exception:
        try:
            managed.process.kill()
        except Exception:
            pass
    finally:
        try:
            managed.log_handle.close()
        except Exception:
            pass


def print_catalog(config: Dict[str, Any]) -> None:
    print("Leion MCP launcher catalog")
    for spec in config["servers"]:
        profiles = ",".join(spec.get("profiles") or [])
        print(
            f"- {spec['name']:<16} :{spec['port']} "
            f"{spec['module']:<30} profiles={profiles}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Launch and supervise Leion MCP servers.")
    parser.add_argument(
        "--profile",
        default="full",
        choices=["core", "dev", "revenue", "full"],
        help="Server profile to launch.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Path to launcher server config.",
    )
    parser.add_argument(
        "--logs-dir",
        type=Path,
        default=DEFAULT_LOG_DIR,
        help="Directory for per-server logs.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print the server catalog and exit.",
    )
    parser.add_argument(
        "--no-restart",
        action="store_true",
        help="Do not restart managed servers that exit.",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    if args.list:
        print_catalog(config)
        return 0

    specs = selected_specs(config, args.profile)
    if not specs:
        print(f"No servers are configured for profile '{args.profile}'.")
        return 2

    print(f"Leion MCP profile: {args.profile}")
    print(f"Repository: {REPO_ROOT}")
    print(f"Logs: {args.logs_dir}")
    print("")

    managed: Dict[str, ManagedServer] = {}
    for spec in specs:
        launched = launch_server(spec, args.logs_dir)
        if launched is not None:
            managed[str(spec["name"])] = launched

    print("")
    print("Leion MCP supervisor running. Press Ctrl+C to stop managed servers.")

    try:
        while True:
            time.sleep(1.0)
            for name, current in list(managed.items()):
                code = current.process.poll()
                if code is None:
                    continue

                current.log_handle.write(
                    f"=== exited code={code} at {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n"
                )
                current.log_handle.close()

                restart_allowed = bool(current.spec.get("restart", True)) and not args.no_restart
                if not restart_allowed:
                    print(f"✗ {name} exited code={code}; restart disabled")
                    managed.pop(name, None)
                    continue

                if current.restarts >= MAX_RESTARTS:
                    print(f"✗ {name} exceeded {MAX_RESTARTS} automatic restarts")
                    managed.pop(name, None)
                    continue

                port = int(current.spec["port"])
                time.sleep(RESTART_DELAY_SECONDS)
                if port_open(port):
                    print(f"~ {name} port :{port} is now owned by another process; no restart")
                    managed.pop(name, None)
                    continue

                print(f"↻ restarting {name} after exit code={code}")
                replacement = launch_server(current.spec, args.logs_dir)
                if replacement is None:
                    managed.pop(name, None)
                    continue
                replacement.restarts = current.restarts + 1
                managed[name] = replacement
    except KeyboardInterrupt:
        print("\nStopping managed MCP servers...")
    finally:
        for managed_server in reversed(list(managed.values())):
            close_managed(managed_server)

    print("Leion MCP supervisor stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
