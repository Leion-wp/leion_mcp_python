import os
from fastmcp import FastMCP
from utils.config import load_env
from utils.logger import setup_logger

from tools.wp_tools import register_wp_tools

load_env()
setup_logger()

server = FastMCP(
    name="leion-wp",
    version="1.0.0",
)

register_wp_tools(server)

if __name__ == "__main__":
    server.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 7012)),
    )
