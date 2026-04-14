from fastmcp import FastMCP
from utils.config import load_env
from utils.logger import setup_logger

from tools.git_tools import register_git_tools
from tools.project_tools import register_project_tools
from tools.repo_builder_tools import register_repo_builder_tools


load_env()
setup_logger()

server = FastMCP(
    name="leion-git-project",
    version="1.0.0",
)

register_git_tools(server)
register_project_tools(server)
register_repo_builder_tools(server)

if __name__ == "__main__":
    import os
    server.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 7002)),
    )
