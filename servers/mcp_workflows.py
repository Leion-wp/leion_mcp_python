from fastmcp import FastMCP
from utils.config import load_env
from utils.logger import setup_logger

load_env()

from tools.workflow_tools import register_workflow_tools
from tools.workflow_builder_tools import register_workflow_builder_tools
from tools.flowise_tools import register_flowise_rube_zapier_tools
from tools.leion_ai_workflow_engine_tools import register_leion_ai_workflow_engine_tools
from tools.leion_cc_workflows_tools import register_leion_cc_workflows_tools
from tools.leion_cc_run_workflow_tools import register_leion_cc_run_workflow_tools
from tools.leion_engine_tools import register_leion_engine_tools  # Phase C: Engine :8001 integration


setup_logger()

server = FastMCP(
    name="leion-workflows",
    version="1.0.0",
)

register_workflow_tools(server)
register_workflow_builder_tools(server)
register_flowise_rube_zapier_tools(server)
register_leion_ai_workflow_engine_tools(server)
register_leion_cc_workflows_tools(server)
register_leion_cc_run_workflow_tools(server)
register_leion_engine_tools(server)  # Phase C: Control plane → Data plane (Engine :8001)


if __name__ == "__main__":
    import os

    server.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 7003)),
    )
