from fastmcp import FastMCP


def register_comm_tools(server: FastMCP):

    @server.tool()
    def comm_send_email_plan(to: str, subject: str, body: str):
        """
        Prépare l'envoi d'un email (à router ensuite via Composio ou autre).
        """
        return {
            "to": to,
            "subject": subject,
            "body": body,
        }

    @server.tool()
    def comm_post_social_plan(network: str, content: str):
        """
        Prépare un post réseau social.
        """
        return {
            "network": network,
            "content": content,
        }

    @server.tool()
    def comm_sms_plan(number: str, message: str):
        """
        Prépare un SMS à envoyer via une intégration externe.
        """
        return {
            "number": number,
            "message": message,
        }
