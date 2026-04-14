from fastmcp import FastMCP
from utils.config import load_env
from utils.logger import setup_logger

from tools.leion_cc_dashboard_tools import register_leion_cc_dashboard_tools
from tools.leion_cc_resources import register_leion_cc_resources


load_env()
setup_logger()

server = FastMCP(
    name="leion-control-center",
    version="1.0.0",
)

register_leion_cc_dashboard_tools(server)
register_leion_cc_resources(server)

if __name__ == "__main__":
    import os
    server.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 7010)),
    )
