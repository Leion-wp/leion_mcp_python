from fastmcp import FastMCP
from utils.config import load_env
from utils.logger import setup_logger

from tools.code_refactorer_tools import register_code_refactorer_tools
from tools.dependency_ai_tools import register_dependency_ai_tools
from tools.auto_tester_tools import register_auto_tester_tools
from tools.observability_tools import register_observability_tools


load_env()
setup_logger()

server = FastMCP(
    name="leion-dev-quality",
    version="1.0.0",
)

register_code_refactorer_tools(server)
register_dependency_ai_tools(server)
register_auto_tester_tools(server)
register_observability_tools(server)


if __name__ == "__main__":
    import os
    server.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 7007)),
    )
