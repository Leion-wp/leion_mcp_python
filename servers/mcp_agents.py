from fastmcp import FastMCP
from utils.config import load_env
from utils.logger import setup_logger

from tools.agent_tools import register_agent_tools
from tools.agent_supervisor_tools import register_agent_supervisor_tools
from tools.orchestrator_tools import register_orchestrator_tools
from tools.leion_cc_agents_tools import register_leion_cc_agents_tools


load_env()
setup_logger()

server = FastMCP(
    name="leion-agents",
    version="1.0.0",
)

register_agent_tools(server)
register_agent_supervisor_tools(server)
register_orchestrator_tools(server)
register_leion_cc_agents_tools(server)

if __name__ == "__main__":
    import os
    server.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 7005)),
    )
