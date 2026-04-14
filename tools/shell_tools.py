import subprocess
from fastmcp import FastMCP

def register_shell_tools(server: FastMCP):

    @server.tool()
    def shell_run(command: str):
        """
        Exécute une commande système et retourne son résultat.
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True
            )

            return {
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }

        except Exception as e:
            return {
                "error": str(e)
            }