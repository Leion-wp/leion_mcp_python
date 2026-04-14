import os
import requests
from fastmcp import FastMCP

BASE_URL = os.getenv("WP_BASE_URL", "").rstrip("/")
WP_USER = os.getenv("WP_USER", "")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")
TIMEOUT = int(os.getenv("WP_TIMEOUT", "60"))


def _auth():
    if not WP_USER or not WP_APP_PASSWORD:
        return None
    return (WP_USER, WP_APP_PASSWORD)


def _build_url(path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    if not BASE_URL:
        return path
    return f"{BASE_URL}{path}"


def _request(method: str, path: str, params: dict | None = None, json: dict | None = None, data: dict | None = None):
    url = _build_url(path)
    try:
        resp = requests.request(
            method=method,
            url=url,
            params=params,
            json=json,
            data=data,
            auth=_auth(),
            timeout=TIMEOUT,
        )
        content_type = resp.headers.get("content-type", "")
        payload = resp.json() if "application/json" in content_type else resp.text
        return {
            "ok": resp.ok,
            "status": resp.status_code,
            "url": url,
            "data": payload,
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "url": url}


# -------------------------------------------------------------------
# MCP Tools
# -------------------------------------------------------------------

def register_wp_tools(server: FastMCP):

    # -------------------------
    # Generic
    # -------------------------

    @server.tool()
    def wp_request(
        method: str,
        path: str,
        params: dict | None = None,
        json: dict | None = None,
        data: dict | None = None,
    ):
        """Generic WordPress REST request."""
        return _request(method, path, params=params, json=json, data=data)

    # -------------------------
    # Posts
    # -------------------------

    @server.tool()
    def wp_list_posts(
        status: str | None = None,
        per_page: int = 10,
        search: str = "",
        page: int = 1,
    ):
        params = {"per_page": per_page, "page": page}
        if status:
            params["status"] = status
        if search:
            params["search"] = search
        return _request("GET", "/wp-json/wp/v2/posts", params=params)

    @server.tool()
    def wp_get_post(post_id: int):
        return _request("GET", f"/wp-json/wp/v2/posts/{post_id}")

    @server.tool()
    def wp_create_post(
        title: str,
        content: str,
        status: str = "draft",
        excerpt: str | None = None,
    ):
        payload = {"title": title, "content": content, "status": status}
        if excerpt:
            payload["excerpt"] = excerpt
        return _request("POST", "/wp-json/wp/v2/posts", json=payload)

    @server.tool()
    def wp_update_post(
        post_id: int,
        title: str | None = None,
        content: str | None = None,
        status: str | None = None,
    ):
        payload = {}
        if title is not None:
            payload["title"] = title
        if content is not None:
            payload["content"] = content
        if status is not None:
            payload["status"] = status
        return _request("POST", f"/wp-json/wp/v2/posts/{post_id}", json=payload)

    @server.tool()
    def wp_delete_post(post_id: int, force: bool = True):
        params = {"force": "true" if force else "false"}
        return _request("DELETE", f"/wp-json/wp/v2/posts/{post_id}", params=params)

    # -------------------------
    # Pages
    # -------------------------

    @server.tool()
    def wp_list_pages(
        status: str | None = None,
        per_page: int = 10,
        search: str = "",
        page: int = 1,
    ):
        params = {"per_page": per_page, "page": page}
        if status:
            params["status"] = status
        if search:
            params["search"] = search
        return _request("GET", "/wp-json/wp/v2/pages", params=params)

    @server.tool()
    def wp_get_page(page_id: int):
        return _request("GET", f"/wp-json/wp/v2/pages/{page_id}")

    @server.tool()
    def wp_create_page(
        title: str,
        content: str,
        status: str = "draft",
        excerpt: str | None = None,
    ):
        payload = {"title": title, "content": content, "status": status}
        if excerpt:
            payload["excerpt"] = excerpt
        return _request("POST", "/wp-json/wp/v2/pages", json=payload)

    @server.tool()
    def wp_update_page(
        page_id: int,
        title: str | None = None,
        content: str | None = None,
        status: str | None = None,
    ):
        payload = {}
        if title is not None:
            payload["title"] = title
        if content is not None:
            payload["content"] = content
        if status is not None:
            payload["status"] = status
        return _request("POST", f"/wp-json/wp/v2/pages/{page_id}", json=payload)

    @server.tool()
    def wp_delete_page(page_id: int, force: bool = True):
        params = {"force": "true" if force else "false"}
        return _request("DELETE", f"/wp-json/wp/v2/pages/{page_id}", params=params)

    # -------------------------
    # Media
    # -------------------------

    @server.tool()
    def wp_list_media(
        per_page: int = 10,
        search: str = "",
        page: int = 1,
    ):
        params = {"per_page": per_page, "page": page}
        if search:
            params["search"] = search
        return _request("GET", "/wp-json/wp/v2/media", params=params)

    @server.tool()
    def wp_get_media(media_id: int):
        return _request("GET", f"/wp-json/wp/v2/media/{media_id}")

    @server.tool()
    def wp_import_media_url(url: str):
        return _request(
            "POST",
            "/wp-json/ai/v1/media/import",
            json={"url": url},
        )

    # -------------------------
    # Plugins (AI Gateway)
    # -------------------------

    @server.tool()
    def wp_list_plugins():
        return _request("GET", "/wp-json/ai/v1/plugins")

    @server.tool()
    def wp_search_plugins(query: str):
        return _request(
            "GET",
            "/wp-json/ai/v1/plugins/search",
            params={"query": query},
        )

    @server.tool()
    def wp_install_plugin(slug: str):
        return _request(
            "POST",
            "/wp-json/ai/v1/plugins/install",
            json={"slug": slug},
        )

    @server.tool()
    def wp_activate_plugin(plugin_file: str):
        return _request(
            "POST",
            "/wp-json/ai/v1/plugins/activate",
            json={"plugin_file": plugin_file},
        )

    @server.tool()
    def wp_deactivate_plugin(plugin_file: str):
        return _request(
            "POST",
            "/wp-json/ai/v1/plugins/deactivate",
            json={"plugin_file": plugin_file},
        )

    @server.tool()
    def wp_delete_plugin(plugin_file: str):
        return _request(
            "POST",
            "/wp-json/ai/v1/plugins/delete",
            json={"plugin_file": plugin_file},
        )
