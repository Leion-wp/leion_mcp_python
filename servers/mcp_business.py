from fastmcp import FastMCP
from utils.config import load_env
from utils.logger import setup_logger

load_env()

from tools.business_launcher_tools import register_business_launcher_tools
from tools.business_assets_tools import register_business_assets_tools
from tools.composio_business_tools import register_composio_business_tools
from tools.asset_creator_tools import register_asset_creator_tools


setup_logger()

server = FastMCP(
    name="leion-business",
    version="1.0.0",
)

register_business_launcher_tools(server)
register_business_assets_tools(server)
register_composio_business_tools(server)
register_asset_creator_tools(server)

if __name__ == "__main__":
    import os
    server.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 7008)),
    )
