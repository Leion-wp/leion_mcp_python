from fastmcp import FastMCP
from .composio_tools import composio_run_action  # type: ignore


# NOTE : ces wrappers supposent que composio_run_action est disponible.

def register_composio_business_tools(server: FastMCP):

    @server.tool()
    def biz_slack_announce(channel: str, message: str):
        """
        Wrapper haut niveau pour envoyer un message Slack via Composio.
        """
        return composio_run_action("slack", "send_message", {"channel": channel, "text": message})

    @server.tool()
    def biz_github_issue(repo: str, title: str, body: str):
        """
        Crée une issue GitHub via Composio.
        """
        return composio_run_action("github", "create_issue", {"repo": repo, "title": title, "body": body})

    @server.tool()
    def biz_notion_page(database_id: str, title: str, content: str):
        """
        Crée une page Notion via Composio.
        """
        payload = {
            "database_id": database_id,
            "title": title,
            "content": content,
        }
        return composio_run_action("notion", "create_page", payload)

    @server.tool()
    def biz_gmail_send(to: str, subject: str, body: str):
        """
        Envoie un email via Gmail/Composio.
        """
        payload = {
            "to": to,
            "subject": subject,
            "body": body,
        }
        return composio_run_action("gmail", "send_email", payload)
