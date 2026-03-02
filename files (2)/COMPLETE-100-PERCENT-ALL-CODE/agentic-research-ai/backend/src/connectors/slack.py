"""
Slack Connector
"""
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional

class SlackConnector:
    """Production Slack webhook connector."""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def post_message(
        self,
        text: str,
        channel: Optional[str] = None,
        username: Optional[str] = "Agentic AI",
        icon_emoji: Optional[str] = ":robot_face:",
        blocks: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Post message to Slack."""
        
        payload = {
            "text": text,
            "username": username,
            "icon_emoji": icon_emoji,
        }
        
        if channel:
            payload["channel"] = channel
        
        if blocks:
            payload["blocks"] = blocks
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.webhook_url, json=payload) as response:
                if response.status == 200:
                    return {"success": True, "message": "Posted to Slack"}
                else:
                    return {"success": False, "error": await response.text()}
    
    async def post_research_complete(
        self,
        project_name: str,
        findings: str,
        url: str,
    ) -> Dict[str, Any]:
        """Post research complete notification with rich formatting."""
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"✅ Research Complete: {project_name}",
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Key Findings:*\n{findings}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Results"
                        },
                        "url": url,
                        "style": "primary"
                    }
                ]
            }
        ]
        
        return await self.post_message(
            text=f"Research Complete: {project_name}",
            blocks=blocks,
        )


# =================================================================
