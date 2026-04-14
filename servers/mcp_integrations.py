from fastmcp import FastMCP
from utils.config import load_env
from utils.logger import setup_logger

from tools.composio_tools import register_composio_tools
from tools.composio_list_apps_tools import register_composio_list_apps_tools
from tools.composio_connect_app_tools import register_composio_connect_app_tools
from tools.comm_tools import register_comm_tools


load_env()
setup_logger()

server = FastMCP(
    name="leion-integrations",
    version="1.0.0",
)

register_composio_tools(server)
register_composio_list_apps_tools(server)
register_composio_connect_app_tools(server)
register_comm_tools(server)

if __name__ == "__main__":
    import os
    server.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 7006)),
    )
