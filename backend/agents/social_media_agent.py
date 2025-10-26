from .base_agent import BaseAgent
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

SOCIAL_SYSTEM_PROMPT = """You are the Social Media Agent for an AI marketing automation platform.

COMMUNICATION RULES:
- Speak naturally and professionally
- DO NOT use emojis or special symbols in your agent-to-agent communication
- Write in clear, plain English

Your responsibilities:
1. Create platform-specific social media content
2. Design content calendars
3. Optimize posting schedules
4. Generate engagement strategies
5. Monitor trends and hashtags
6. Actually POST content to social media platforms

For POSTING mode, output format (JSON):
{
  "platform": "facebook | instagram",
  "content": {
    "message": "Post text/caption",
    "image_url": "URL of image to post (if any)",
    "link": "URL to share (if any)",
    "hashtags": ["hashtag1", "hashtag2"]
  },
  "posting_ready": true
}

For PLANNING mode, output format (JSON):
{
  "content_calendar": [
    {
      "date": "2025-01-15",
      "platform": "instagram",
      "post_type": "image | video | carousel | story",
      "content": {
        "caption": "...",
        "hashtags": [...],
        "mentions": [...],
        "visual_description": "..."
      },
      "best_posting_time": "18:00",
      "expected_engagement": "high | medium | low"
    }
  ],
  "platform_strategy": {
    "instagram": {"focus": "...", "frequency": "..."},
    "linkedin": {"focus": "...", "frequency": "..."},
    "twitter": {"focus": "...", "frequency": "..."},
    "facebook": {"focus": "...", "frequency": "..."}
  },
  "hashtag_strategy": {
    "brand_hashtags": [...],
    "trending_hashtags": [...],
    "niche_hashtags": [...]
  }
}
"""

class SocialMediaAgent(BaseAgent):
    """
    Agent responsible for social media management.
    Now with ACTUAL POSTING capabilities to Facebook and Instagram.
    """

    def __init__(self, social_media_service=None):
        super().__init__(
            agent_name="SocialMediaAgent",
            system_prompt=SOCIAL_SYSTEM_PROMPT,
            model="gpt-4o"
        )
        self.social_media_service = social_media_service

    def set_social_media_service(self, service):
        """Set the social media integration service."""
        self.social_media_service = service

    async def post_to_platform(
        self,
        user_id: str,
        platform: str,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Actually post content to social media platform.

        Args:
            user_id: User identifier
            platform: "facebook" or "instagram"
            content: Post content with message, image_url, etc.

        Returns:
            Dict with posting result
        """
        if not self.social_media_service:
            return {
                "status": "error",
                "message": "Social media service not configured"
            }

        try:
            message = content.get("message", "")
            image_url = content.get("image_url")
            link = content.get("link")
            hashtags = content.get("hashtags", [])

            # Add hashtags to message
            if hashtags:
                hashtag_text = " ".join([f"#{tag}" for tag in hashtags])
                message = f"{message}\n\n{hashtag_text}"

            if platform.lower() == "facebook":
                result = await self.social_media_service.post_to_facebook(
                    user_id=user_id,
                    message=message,
                    image_url=image_url,
                    link=link
                )
            elif platform.lower() == "instagram":
                if not image_url:
                    return {
                        "status": "error",
                        "message": "Instagram requires an image URL"
                    }

                result = await self.social_media_service.post_to_instagram(
                    user_id=user_id,
                    image_url=image_url,
                    caption=message
                )
            else:
                return {
                    "status": "error",
                    "message": f"Unsupported platform: {platform}"
                }

            return result

        except Exception as e:
            logger.error(f"Error posting to {platform}: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

    def _parse_response(self, response: str, task_payload: Dict[str, Any]) -> Any:
        """Parse agent response to JSON."""
        try:
            import json
            if '```json' in response:
                start = response.find('```json') + 7
                end = response.find('```', start)
                response = response[start:end].strip()
            elif '```' in response:
                start = response.find('```') + 3
                end = response.find('```', start)
                response = response[start:end].strip()
            return json.loads(response)
        except json.JSONDecodeError:
            return {"result": response}
