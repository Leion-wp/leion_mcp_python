from fastmcp import FastMCP
from tools.register import register_all_tools
from utils.config import load_env
from utils.logger import setup_logger

load_env()
setup_logger()

server = FastMCP(
    name="leion-os",
    version="1.0.0",
)

register_all_tools(server)
