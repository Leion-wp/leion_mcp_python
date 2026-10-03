import os

from fastmcp import FastMCP

from tools.n8n_tools import register_n8n_tools
from utils.config import load_env
from utils.logger import setup_logger


load_env()
setup_logger()

server = FastMCP(
    name="leion-n8n",
    version="1.0.0",
)

register_n8n_tools(server)


if __name__ == "__main__":
    server.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 7013)),
    )
