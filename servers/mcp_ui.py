from fastmcp import FastMCP
from utils.config import load_env
from utils.logger import setup_logger

from tools.ui_component_generator_tools import register_ui_component_generator_tools


load_env()
setup_logger()

server = FastMCP(
    name="leion-ui",
    version="1.0.0",
)

register_ui_component_generator_tools(server)

if __name__ == "__main__":
    import os
    server.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 7009)),
    )
