from fastmcp import FastMCP
from utils.config import load_env
from utils.logger import setup_logger

load_env()

from tools.vector_memory_tools import register_vector_memory_tools
from tools.memory_tools import register_memory_tools
from tools.profile_ai_tools import register_profile_ai_tools


setup_logger()

server = FastMCP(
    name="leion-memory",
    version="1.0.0",
)

register_vector_memory_tools(server)
register_memory_tools(server)
register_profile_ai_tools(server)

if __name__ == "__main__":
    import os
    server.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 7004)),
    )
