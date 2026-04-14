import os
from fastmcp import FastMCP
from utils.config import load_env
from utils.logger import setup_logger

from tools.fs_tools import register_fs_tools
from tools.fs_patch import register_fs_patch_tools
from tools.fs_watch_tools import register_fs_watch_tools
from tools.fs_monitor_pro_tools import register_fs_monitor_pro_tools


load_env()
setup_logger()
FS_ROOT = os.environ.get("FS_ROOT", "/data")

server = FastMCP(
    name="leion-fs",
    version="1.0.0",
)

# File system primitives
register_fs_tools(server)

# Patch application
register_fs_patch_tools(server)

# File change polling
register_fs_watch_tools(server)

# Higher-level monitoring plan helpers
register_fs_monitor_pro_tools(server)

if __name__ == "__main__":
    import os
    server.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 7001)),
    )
