import os
from fastmcp import FastMCP

def register_fs_tools(server: FastMCP):

    @server.tool()
    def fs_list_directory(path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Directory not found: {path}")
        return {
            "path": path,
            "items": os.listdir(path)
        }

    @server.tool()
    def fs_read_file(path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return {"path": path, "content": f.read()}

    @server.tool()
    def fs_write_file(path: str, content: str):
        folder = os.path.dirname(path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return {"path": path, "status": "written"}

    @server.tool()
    def fs_append_file(path: str, content: str):
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)
        return {"path": path, "status": "appended"}

    @server.tool()
    def fs_delete_file(path: str):
        if os.path.exists(path):
            os.remove(path)
            return {"status": "deleted", "path": path}
        raise FileNotFoundError(f"File not found: {path}")

    @server.tool()
    def fs_make_directory(path: str):
        os.makedirs(path, exist_ok=True)
        return {"status": "created", "path": path}
