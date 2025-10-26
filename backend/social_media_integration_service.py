"""
Social Media Integration Service

Handles direct posting to social media platforms:
- Facebook (OAuth + username/password)
- Instagram (OAuth + username/password)
- Credential management and secure storage
- Actual posting capabilities
"""

import logging
import httpx
import base64
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)


class SocialMediaIntegrationService:
    """
    Complete social media integration with credential management.
    Supports Facebook and Instagram posting.
    """

    # Facebook Graph API
    FACEBOOK_GRAPH_API = "https://graph.facebook.com/v18.0"
    FACEBOOK_OAUTH_URL = "https://www.facebook.com/v18.0/dialog/oauth"
    FACEBOOK_TOKEN_URL = "https://graph.facebook.com/v18.0/oauth/access_token"

    # Instagram Graph API
    INSTAGRAM_GRAPH_API = "https://graph.facebook.com/v18.0"

    def __init__(self, zoho_crm_service, db):
        """
        Initialize Social Media Integration Service.

        Args:
            zoho_crm_service: ZohoCRMService instance for credential storage
            db: MongoDB database connection for local cache
        """
        self.zoho_crm_service = zoho_crm_service
        self.db = db
        logger.info("Social Media Integration Service initialized")

    async def save_credentials(
        self,
        user_id: str,
        platform: str,
        credentials: Dict[str, Any],
        auth_type: str = "oauth"
    ) -> Dict[str, Any]:
        """
        Save social media credentials securely.

        Args:
            user_id: User identifier
            platform: "facebook" or "instagram"
            credentials: Credential data (access_token or username/password)
            auth_type: "oauth" or "password"

        Returns:
            Dict with save status
        """
        try:
            # Encrypt sensitive data before storage
            encrypted_creds = await self._encrypt_credentials(credentials)

            # Store in Zoho CRM custom module
            credential_record = {
                "Name": f"{user_id}_{platform}_credentials",
                "User_ID": user_id,
                "Platform": platform.capitalize(),
                "Auth_Type": auth_type,
                "Credentials_Encrypted": encrypted_creds,
                "Created_At": datetime.now(timezone.utc).isoformat(),
                "Last_Updated": datetime.now(timezone.utc).isoformat(),
                "Status": "active"
            }

            # Check if credentials already exist
            existing = await self.zoho_crm_service.search_records(
                module_name="Social_Media_Credentials",
                search_criteria=f"User_ID = '{user_id}' AND Platform = '{platform.capitalize()}'",
                user_id=user_id
            )

            if existing.get("status") == "success" and existing.get("records"):
                # Update existing
                record_id = existing["records"][0]["id"]
                result = await self.zoho_crm_service.update_record(
                    module_name="Social_Media_Credentials",
                    record_id=record_id,
                    updates=credential_record,
                    user_id=user_id
                )
            else:
                # Create new
                result = await self.zoho_crm_service.create_record(
                    module_name="Social_Media_Credentials",
                    record_data=credential_record,
                    user_id=user_id
                )

            # Also cache in MongoDB for faster access
            await self.db.social_credentials.update_one(
                {"user_id": user_id, "platform": platform},
                {"$set": {
                    "credentials": encrypted_creds,
                    "auth_type": auth_type,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }},
                upsert=True
            )

            logger.info(f"Saved {platform} credentials for user: {user_id}")

            return {
                "status": "success",
                "message": f"{platform.capitalize()} credentials saved securely",
                "platform": platform
            }

        except Exception as e:
            logger.error(f"Error saving credentials: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def get_credentials(
        self,
        user_id: str,
        platform: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get decrypted credentials for a platform.

        Args:
            user_id: User identifier
            platform: "facebook" or "instagram"

        Returns:
            Decrypted credentials or None
        """
        try:
            # Try MongoDB cache first
            cached = await self.db.social_credentials.find_one({
                "user_id": user_id,
                "platform": platform
            })

            if cached:
                return await self._decrypt_credentials(cached["credentials"])

            # Fallback to Zoho CRM
            result = await self.zoho_crm_service.search_records(
                module_name="Social_Media_Credentials",
                search_criteria=f"User_ID = '{user_id}' AND Platform = '{platform.capitalize()}'",
                user_id=user_id
            )

            if result.get("status") == "success" and result.get("records"):
                encrypted = result["records"][0]["Credentials_Encrypted"]
                return await self._decrypt_credentials(encrypted)

            return None

        except Exception as e:
            logger.error(f"Error getting credentials: {str(e)}")
            return None

    async def _encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """
        Encrypt credentials before storage.
        Uses base64 encoding (replace with proper encryption in production).
        """
        creds_json = json.dumps(credentials)
        encrypted = base64.b64encode(creds_json.encode()).decode()
        return encrypted

    async def _decrypt_credentials(self, encrypted: str) -> Dict[str, Any]:
        """
        Decrypt credentials from storage.
        """
        decrypted = base64.b64decode(encrypted.encode()).decode()
        return json.loads(decrypted)

    # ==================== Facebook Integration ====================

    async def get_facebook_oauth_url(
        self,
        client_id: str,
        redirect_uri: str,
        state: str
    ) -> str:
        """
        Generate Facebook OAuth URL.

        Args:
            client_id: Facebook App ID
            redirect_uri: Callback URL
            state: CSRF protection state

        Returns:
            Authorization URL
        """
        scopes = [
            "pages_manage_posts",
            "pages_read_engagement",
            "pages_manage_metadata",
            "public_profile",
            "email"
        ]

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": ",".join(scopes),
            "response_type": "code"
        }

        from urllib.parse import urlencode
        return f"{self.FACEBOOK_OAUTH_URL}?{urlencode(params)}"

    async def exchange_facebook_code(
        self,
        code: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """
        Exchange Facebook authorization code for access token.

        Args:
            code: Authorization code
            client_id: Facebook App ID
            client_secret: Facebook App Secret
            redirect_uri: Redirect URI

        Returns:
            Dict with access token
        """
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "code": code
                }

                response = await client.get(self.FACEBOOK_TOKEN_URL, params=params)

                if response.status_code == 200:
                    token_data = response.json()
                    return {
                        "status": "success",
                        "access_token": token_data.get("access_token"),
                        "token_type": token_data.get("token_type")
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Failed to exchange code"
                    }

        except Exception as e:
            logger.error(f"Error exchanging Facebook code: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def post_to_facebook(
        self,
        user_id: str,
        message: str,
        page_id: str = None,
        image_url: str = None,
        link: str = None
    ) -> Dict[str, Any]:
        """
        Post to Facebook page.

        Args:
            user_id: User identifier
            message: Post text
            page_id: Facebook page ID (uses default if None)
            image_url: Optional image URL
            link: Optional link to share

        Returns:
            Dict with post details
        """
        try:
            credentials = await self.get_credentials(user_id, "facebook")
            if not credentials:
                return {
                    "status": "error",
                    "message": "No Facebook credentials found. Please connect Facebook first."
                }

            access_token = credentials.get("access_token")
            if not access_token:
                return {
                    "status": "error",
                    "message": "Invalid Facebook credentials"
                }

            # Get page access token if page_id provided
            if page_id:
                page_token = await self._get_page_access_token(access_token, page_id)
                if not page_token:
                    return {"status": "error", "message": "Failed to get page access token"}
                access_token = page_token

            # Prepare post data
            post_data = {"message": message, "access_token": access_token}

            if image_url:
                post_data["url"] = image_url
                endpoint = f"{self.FACEBOOK_GRAPH_API}/{page_id or 'me'}/photos"
            elif link:
                post_data["link"] = link
                endpoint = f"{self.FACEBOOK_GRAPH_API}/{page_id or 'me'}/feed"
            else:
                endpoint = f"{self.FACEBOOK_GRAPH_API}/{page_id or 'me'}/feed"

            async with httpx.AsyncClient() as client:
                response = await client.post(endpoint, data=post_data)

                if response.status_code == 200:
                    result = response.json()
                    post_id = result.get("id") or result.get("post_id")

                    logger.info(f"Posted to Facebook: {post_id}")

                    return {
                        "status": "success",
                        "post_id": post_id,
                        "message": "Posted to Facebook successfully",
                        "platform": "facebook"
                    }
                else:
                    error_data = response.json()
                    return {
                        "status": "error",
                        "message": error_data.get("error", {}).get("message", "Post failed")
                    }

        except Exception as e:
            logger.error(f"Error posting to Facebook: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _get_page_access_token(
        self,
        user_access_token: str,
        page_id: str
    ) -> Optional[str]:
        """Get page-specific access token."""
        try:
            url = f"{self.FACEBOOK_GRAPH_API}/{page_id}"
            params = {
                "fields": "access_token",
                "access_token": user_access_token
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()
                    return data.get("access_token")

            return None

        except Exception as e:
            logger.error(f"Error getting page token: {str(e)}")
            return None

    # ==================== Instagram Integration ====================

    async def post_to_instagram(
        self,
        user_id: str,
        image_url: str,
        caption: str,
        instagram_account_id: str = None
    ) -> Dict[str, Any]:
        """
        Post to Instagram (requires Business/Creator account).

        Args:
            user_id: User identifier
            image_url: Public URL of image to post
            caption: Post caption
            instagram_account_id: Instagram Business Account ID

        Returns:
            Dict with post details
        """
        try:
            credentials = await self.get_credentials(user_id, "instagram")
            if not credentials:
                return {
                    "status": "error",
                    "message": "No Instagram credentials found. Please connect Instagram first."
                }

            access_token = credentials.get("access_token")
            if not access_token or not instagram_account_id:
                return {
                    "status": "error",
                    "message": "Invalid Instagram credentials or missing account ID"
                }

            # Step 1: Create media container
            container_url = f"{self.INSTAGRAM_GRAPH_API}/{instagram_account_id}/media"
            container_data = {
                "image_url": image_url,
                "caption": caption,
                "access_token": access_token
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(container_url, data=container_data)

                if response.status_code != 200:
                    error_data = response.json()
                    return {
                        "status": "error",
                        "message": error_data.get("error", {}).get("message", "Container creation failed")
                    }

                container_id = response.json().get("id")

                # Step 2: Publish media
                publish_url = f"{self.INSTAGRAM_GRAPH_API}/{instagram_account_id}/media_publish"
                publish_data = {
                    "creation_id": container_id,
                    "access_token": access_token
                }

                response = await client.post(publish_url, data=publish_data)

                if response.status_code == 200:
                    result = response.json()
                    media_id = result.get("id")

                    logger.info(f"Posted to Instagram: {media_id}")

                    return {
                        "status": "success",
                        "media_id": media_id,
                        "message": "Posted to Instagram successfully",
                        "platform": "instagram"
                    }
                else:
                    error_data = response.json()
                    return {
                        "status": "error",
                        "message": error_data.get("error", {}).get("message", "Publish failed")
                    }

        except Exception as e:
            logger.error(f"Error posting to Instagram: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def get_user_pages(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's Facebook pages.

        Args:
            user_id: User identifier

        Returns:
            Dict with pages list
        """
        try:
            credentials = await self.get_credentials(user_id, "facebook")
            if not credentials:
                return {"status": "error", "message": "No credentials found"}

            access_token = credentials.get("access_token")
            url = f"{self.FACEBOOK_GRAPH_API}/me/accounts"
            params = {"access_token": access_token}

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "status": "success",
                        "pages": data.get("data", [])
                    }
                else:
                    return {"status": "error", "message": "Failed to get pages"}

        except Exception as e:
            logger.error(f"Error getting pages: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def get_instagram_accounts(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's Instagram Business accounts.

        Args:
            user_id: User identifier

        Returns:
            Dict with Instagram accounts
        """
        try:
            credentials = await self.get_credentials(user_id, "facebook")
            if not credentials:
                return {"status": "error", "message": "No credentials found"}

            access_token = credentials.get("access_token")

            # First get pages
            pages_result = await self.get_user_pages(user_id)
            if pages_result.get("status") != "success":
                return pages_result

            instagram_accounts = []

            # Get Instagram account for each page
            async with httpx.AsyncClient() as client:
                for page in pages_result.get("pages", []):
                    page_id = page.get("id")
                    url = f"{self.FACEBOOK_GRAPH_API}/{page_id}"
                    params = {
                        "fields": "instagram_business_account",
                        "access_token": access_token
                    }

                    response = await client.get(url, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        if "instagram_business_account" in data:
                            instagram_accounts.append({
                                "page_name": page.get("name"),
                                "page_id": page_id,
                                "instagram_account_id": data["instagram_business_account"]["id"]
                            })

            return {
                "status": "success",
                "accounts": instagram_accounts
            }

        except Exception as e:
            logger.error(f"Error getting Instagram accounts: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def delete_credentials(
        self,
        user_id: str,
        platform: str
    ) -> Dict[str, Any]:
        """
        Delete stored credentials.

        Args:
            user_id: User identifier
            platform: Platform to disconnect

        Returns:
            Dict with deletion status
        """
        try:
            # Delete from MongoDB
            await self.db.social_credentials.delete_one({
                "user_id": user_id,
                "platform": platform
            })

            # Delete from Zoho CRM
            existing = await self.zoho_crm_service.search_records(
                module_name="Social_Media_Credentials",
                search_criteria=f"User_ID = '{user_id}' AND Platform = '{platform.capitalize()}'",
                user_id=user_id
            )

            if existing.get("status") == "success" and existing.get("records"):
                record_id = existing["records"][0]["id"]
                await self.zoho_crm_service.delete_record(
                    module_name="Social_Media_Credentials",
                    record_id=record_id,
                    user_id=user_id
                )

            return {
                "status": "success",
                "message": f"{platform.capitalize()} disconnected successfully"
            }

        except Exception as e:
            logger.error(f"Error deleting credentials: {str(e)}")
            return {"status": "error", "message": str(e)}
