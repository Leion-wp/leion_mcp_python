from fastmcp import FastMCP

# IMPORTANT : on utilise le même identifiant que dans WIDGET_RESOURCE_ID
WIDGET_RESOURCE_ID = "leion-cc://widget"


def register_leion_cc_resources(server: FastMCP):
    @server.resource(WIDGET_RESOURCE_ID)
    def leion_cc_widget() -> str:
        """
        Resource MCP qui renvoie le HTML de l'UI Leion Control Center.
        ChatGPT utilisera cette resource comme template (text/html+skybridge).
        """
        # Ici on renvoie le HTML du widget, qui charge ton bundle React
        return """<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Leion Control Center</title>
    <meta
      http-equiv="Content-Security-Policy"
      content="default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; style-src 'unsafe-inline';"
    />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/app/web/dist/component.js"></script>
  </body>
</html>"""
