"""
Social Media Publishing Service for Facebook and Instagram.
Handles auto-publishing of marketing content to social platforms.
"""
import httpx
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class SocialMediaPublishingError(Exception):
    """Base exception for social media publishing errors."""
    pass

class FacebookPublishingError(SocialMediaPublishingError):
    """Facebook-specific publishing error."""
    pass

class InstagramPublishingError(SocialMediaPublishingError):
    """Instagram-specific publishing error."""
    pass

class SocialMediaService:
    """
    Service for publishing content to Facebook and Instagram.
    Uses Meta Graph API for both platforms.
    """
    
    GRAPH_API_BASE = "https://graph.facebook.com/v18.0"
    MAX_INSTAGRAM_CAPTION_LENGTH = 2200
    MAX_STATUS_CHECKS = 30  # Max polling attempts for Instagram container
    STATUS_CHECK_INTERVAL = 2  # Seconds between status checks
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def publish_to_facebook(
        self,
        page_id: str,
        access_token: str,
        message: str,
        image_url: Optional[str] = None,
        link: Optional[str] = None,
        scheduled_time: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Post content to Facebook Page.
        
        Args:
            page_id: Facebook Page ID
            access_token: Page access token
            message: Post text content
            image_url: Optional image URL (publicly accessible)
            link: Optional link to include in post
            scheduled_time: Optional Unix timestamp for scheduled publishing
            
        Returns:
            Dictionary containing post_id and status
            
        Raises:
            FacebookPublishingError: If posting fails
        """
        try:
            self.logger.info(f"Publishing to Facebook Page {page_id}")
            
            # Determine endpoint based on content type
            if image_url:
                endpoint = f"{self.GRAPH_API_BASE}/{page_id}/photos"
            else:
                endpoint = f"{self.GRAPH_API_BASE}/{page_id}/feed"
            
            # Prepare parameters
            params = {
                "access_token": access_token,
                "message": message
            }
            
            if image_url:
                params["url"] = image_url
            
            if link and not image_url:
                params["link"] = link
            
            if scheduled_time:
                params["scheduled_publish_time"] = scheduled_time
                params["published"] = "false"
            
            # Make API request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(endpoint, data=params)
                
                if response.status_code != 200:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "Unknown error")
                    self.logger.error(f"Facebook API error: {error_msg}")
                    raise FacebookPublishingError(f"Failed to post to Facebook: {error_msg}")
                
                result = response.json()
                post_id = result.get("post_id") or result.get("id")
                
                self.logger.info(f"Successfully posted to Facebook. Post ID: {post_id}")
                
                return {
                    "platform": "facebook",
                    "post_id": post_id,
                    "status": "scheduled" if scheduled_time else "published",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
        except httpx.RequestError as e:
            self.logger.error(f"Network error posting to Facebook: {str(e)}")
            raise FacebookPublishingError(f"Network error: {str(e)}")
        except Exception as e:
            if isinstance(e, FacebookPublishingError):
                raise
            self.logger.error(f"Unexpected error posting to Facebook: {str(e)}")
            raise FacebookPublishingError(f"Unexpected error: {str(e)}")
    
    async def publish_to_instagram(
        self,
        instagram_account_id: str,
        access_token: str,
        image_url: str,
        caption: str,
        location_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Post image to Instagram Business account using container workflow.
        
        Instagram posting is a two-step process:
        1. Create a media container with content
        2. Publish the container after it's processed
        
        Args:
            instagram_account_id: Instagram Business Account ID
            access_token: Access token (usually Page access token)
            image_url: Image URL (must be publicly accessible JPEG)
            caption: Post caption (max 2200 characters)
            location_id: Optional Facebook Place ID for location tagging
            
        Returns:
            Dictionary containing media_id and status
            
        Raises:
            InstagramPublishingError: If posting fails
        """
        try:
            self.logger.info(f"Publishing to Instagram account {instagram_account_id}")
            
            # Validate caption length
            if len(caption) > self.MAX_INSTAGRAM_CAPTION_LENGTH:
                caption = caption[:self.MAX_INSTAGRAM_CAPTION_LENGTH]
                self.logger.warning("Caption truncated to 2200 characters")
            
            # Step 1: Create media container
            container_id = await self._create_instagram_container(
                instagram_account_id,
                access_token,
                image_url,
                caption,
                location_id
            )
            
            # Step 2: Wait for container processing
            await self._wait_for_container_ready(container_id, access_token)
            
            # Step 3: Publish the container
            media_id = await self._publish_instagram_container(
                instagram_account_id,
                access_token,
                container_id
            )
            
            self.logger.info(f"Successfully posted to Instagram. Media ID: {media_id}")
            
            return {
                "platform": "instagram",
                "media_id": media_id,
                "container_id": container_id,
                "status": "published",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            if isinstance(e, InstagramPublishingError):
                raise
            self.logger.error(f"Unexpected error posting to Instagram: {str(e)}")
            raise InstagramPublishingError(f"Unexpected error: {str(e)}")
    
    async def _create_instagram_container(
        self,
        instagram_account_id: str,
        access_token: str,
        image_url: str,
        caption: str,
        location_id: Optional[str] = None
    ) -> str:
        """
        Create Instagram media container.
        
        Returns:
            Container ID
        """
        endpoint = f"{self.GRAPH_API_BASE}/{instagram_account_id}/media"
        
        params = {
            "image_url": image_url,
            "caption": caption,
            "access_token": access_token
        }
        
        if location_id:
            params["location_id"] = location_id
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(endpoint, data=params)
            
            if response.status_code != 200:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", "Unknown error")
                self.logger.error(f"Instagram container creation error: {error_msg}")
                raise InstagramPublishingError(f"Failed to create container: {error_msg}")
            
            result = response.json()
            container_id = result.get("id")
            
            self.logger.info(f"Created Instagram container: {container_id}")
            return container_id
    
    async def _wait_for_container_ready(
        self,
        container_id: str,
        access_token: str
    ) -> None:
        """
        Poll container status until it's ready for publishing.
        
        Raises:
            InstagramPublishingError: If container processing fails or times out
        """
        endpoint = f"{self.GRAPH_API_BASE}/{container_id}"
        params = {
            "fields": "status_code",
            "access_token": access_token
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for attempt in range(self.MAX_STATUS_CHECKS):
                response = await client.get(endpoint, params=params)
                
                if response.status_code != 200:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "Unknown error")
                    raise InstagramPublishingError(f"Failed to check container status: {error_msg}")
                
                result = response.json()
                status_code = result.get("status_code")
                
                self.logger.debug(f"Container {container_id} status: {status_code}")
                
                if status_code == "FINISHED":
                    self.logger.info(f"Container {container_id} ready for publishing")
                    return
                elif status_code == "ERROR":
                    raise InstagramPublishingError(
                        "Container processing failed. Check image format and requirements."
                    )
                elif status_code == "IN_PROGRESS":
                    await asyncio.sleep(self.STATUS_CHECK_INTERVAL)
                    continue
                else:
                    raise InstagramPublishingError(f"Unknown container status: {status_code}")
            
            # If we get here, we've exceeded max attempts
            raise InstagramPublishingError(
                "Container processing timeout. Please try again later."
            )
    
    async def _publish_instagram_container(
        self,
        instagram_account_id: str,
        access_token: str,
        container_id: str
    ) -> str:
        """
        Publish a processed Instagram container.
        
        Returns:
            Published media ID
        """
        endpoint = f"{self.GRAPH_API_BASE}/{instagram_account_id}/media_publish"
        
        params = {
            "creation_id": container_id,
            "access_token": access_token
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(endpoint, data=params)
            
            if response.status_code != 200:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", "Unknown error")
                self.logger.error(f"Instagram publishing error: {error_msg}")
                raise InstagramPublishingError(f"Failed to publish container: {error_msg}")
            
            result = response.json()
            media_id = result.get("id")
            
            self.logger.info(f"Published Instagram media: {media_id}")
            return media_id
    
    async def publish_to_multiple_platforms(
        self,
        platforms: list,
        credentials: Dict[str, Any],
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Publish content to multiple platforms simultaneously.
        
        Args:
            platforms: List of platform names (e.g., ["facebook", "instagram"])
            credentials: Dictionary of credentials for each platform
            content: Content dictionary with message, image_url, etc.
            
        Returns:
            Dictionary with results for each platform
        """
        results = {}
        
        for platform in platforms:
            try:
                if platform.lower() == "facebook":
                    result = await self.publish_to_facebook(
                        page_id=credentials.get("facebook_page_id"),
                        access_token=credentials.get("facebook_access_token"),
                        message=content.get("message", ""),
                        image_url=content.get("image_url"),
                        link=content.get("link")
                    )
                    results["facebook"] = result
                    
                elif platform.lower() == "instagram":
                    if not content.get("image_url"):
                        results["instagram"] = {
                            "status": "skipped",
                            "reason": "Instagram requires an image"
                        }
                        continue
                    
                    result = await self.publish_to_instagram(
                        instagram_account_id=credentials.get("instagram_account_id"),
                        access_token=credentials.get("instagram_access_token") or credentials.get("facebook_access_token"),
                        image_url=content.get("image_url"),
                        caption=content.get("message", "")
                    )
                    results["instagram"] = result
                    
                else:
                    results[platform] = {
                        "status": "error",
                        "message": f"Unsupported platform: {platform}"
                    }
                    
            except Exception as e:
                self.logger.error(f"Error publishing to {platform}: {str(e)}")
                results[platform] = {
                    "status": "error",
                    "message": str(e)
                }
        
        return results
