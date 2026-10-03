import os

from fastmcp import FastMCP

from tools.leion_cli_runtime_tools import register_leion_cli_runtime_tools
from utils.config import load_env
from utils.logger import setup_logger


load_env()
setup_logger()

server = FastMCP(
    name="leion-runtime",
    version="1.0.0",
)

register_leion_cli_runtime_tools(server)


if __name__ == "__main__":
    server.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 7011)),
    )
