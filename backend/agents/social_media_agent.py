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
    Now with ACTUAL POSTING capabilities to Facebook, Instagram, Twitter, and LinkedIn.
    Supports both legacy and new unified social services.
    """

    def __init__(self, social_media_service=None, unified_social_service=None, job_scheduler=None):
        super().__init__(
            agent_name="SocialMediaAgent",
            system_prompt=SOCIAL_SYSTEM_PROMPT,
            model="gpt-4o"
        )
        self.social_media_service = social_media_service  # Legacy service
        self.unified_social_service = unified_social_service  # New unified service
        self.job_scheduler = job_scheduler  # For scheduling posts

    def set_social_media_service(self, service):
        """Set the social media integration service (legacy)."""
        self.social_media_service = service

    def set_unified_social_service(self, service):
        """Set the unified social media service (new)."""
        self.unified_social_service = service

    def set_job_scheduler(self, scheduler):
        """Set the job scheduler for scheduling posts."""
        self.job_scheduler = scheduler

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

    async def post_to_unified_platform(
        self,
        user_id: str,
        account_id: str,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Post to a platform using the new unified social service.
        Supports: Facebook, Instagram, Twitter, LinkedIn

        Args:
            user_id: User identifier
            account_id: Connected social account ID
            content: Post content (text, image_url, etc.)

        Returns:
            Dict with posting result
        """
        if not self.unified_social_service:
            # Fallback to legacy service
            return await self.post_to_platform(user_id, "facebook", content)

        try:
            result = await self.unified_social_service.post_to_platform(
                account_id=account_id,
                content=content,
                user_id=user_id
            )
            return result

        except Exception as e:
            logger.error(f"Error posting to unified platform: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def post_to_multiple_platforms(
        self,
        user_id: str,
        account_ids: list,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Post same content to multiple social media accounts at once.

        Args:
            user_id: User identifier
            account_ids: List of connected account IDs
            content: Post content

        Returns:
            Dict with results for each platform
        """
        if not self.unified_social_service:
            return {
                "success": False,
                "error": "Unified social service not configured"
            }

        try:
            result = await self.unified_social_service.post_to_multiple(
                account_ids=account_ids,
                content=content,
                user_id=user_id
            )
            return result

        except Exception as e:
            logger.error(f"Error posting to multiple platforms: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def schedule_post(
        self,
        user_id: str,
        account_ids: list,
        content: Dict[str, Any],
        scheduled_time: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Schedule a post for later publication.

        Args:
            user_id: User identifier
            account_ids: List of account IDs to post to
            content: Post content
            scheduled_time: ISO format datetime string
            metadata: Optional metadata

        Returns:
            Dict with schedule result and job ID
        """
        if not self.job_scheduler:
            return {
                "success": False,
                "error": "Job scheduler not configured"
            }

        try:
            from datetime import datetime
            scheduled_datetime = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))

            result = await self.job_scheduler.schedule_post(
                user_id=user_id,
                account_ids=account_ids,
                content=content,
                scheduled_time=scheduled_datetime,
                metadata=metadata
            )
            return result

        except Exception as e:
            logger.error(f"Error scheduling post: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_connected_accounts(self, user_id: str, platform: str = None) -> Dict[str, Any]:
        """
        Get all connected social media accounts for a user.

        Args:
            user_id: User identifier
            platform: Optional platform filter

        Returns:
            Dict with list of connected accounts
        """
        if not self.unified_social_service:
            return {
                "success": False,
                "error": "Unified social service not configured"
            }

        try:
            result = await self.unified_social_service.get_connected_accounts(
                user_id=user_id,
                platform=platform
            )
            return result

        except Exception as e:
            logger.error(f"Error getting connected accounts: {str(e)}")
            return {
                "success": False,
                "error": str(e)
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
