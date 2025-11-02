"""
Unified Social Media Service
Handles all social media platform integrations with OAuth and posting
Supports: Facebook, Instagram, Twitter, LinkedIn
"""

import logging
import httpx
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import base64
import json

logger = logging.getLogger(__name__)


class UnifiedSocialService:
    """
    Unified service for all social media platforms.
    Handles OAuth, posting, analytics, and account management.
    """

    def __init__(self, db):
        self.db = db

        # Platform configurations
        self.platforms = {
            "facebook": {
                "app_id": os.environ.get('FACEBOOK_APP_ID'),
                "app_secret": os.environ.get('FACEBOOK_APP_SECRET'),
                "graph_api_version": "v18.0",
                "auth_url": "https://www.facebook.com/v18.0/dialog/oauth",
                "token_url": "https://graph.facebook.com/v18.0/oauth/access_token",
                "api_base": "https://graph.facebook.com/v18.0"
            },
            "instagram": {
                "app_id": os.environ.get('FACEBOOK_APP_ID'),  # Instagram uses Facebook app
                "app_secret": os.environ.get('FACEBOOK_APP_SECRET'),
                "graph_api_version": "v18.0",
                "api_base": "https://graph.facebook.com/v18.0"
            },
            "twitter": {
                "api_key": os.environ.get('TWITTER_API_KEY'),
                "api_secret": os.environ.get('TWITTER_API_SECRET'),
                "bearer_token": os.environ.get('TWITTER_BEARER_TOKEN'),
                "auth_url": "https://twitter.com/i/oauth2/authorize",
                "token_url": "https://api.twitter.com/2/oauth2/token",
                "api_base": "https://api.twitter.com/2"
            },
            "linkedin": {
                "client_id": os.environ.get('LINKEDIN_CLIENT_ID'),
                "client_secret": os.environ.get('LINKEDIN_CLIENT_SECRET'),
                "auth_url": "https://www.linkedin.com/oauth/v2/authorization",
                "token_url": "https://www.linkedin.com/oauth/v2/accessToken",
                "api_base": "https://api.linkedin.com/v2"
            }
        }

        logger.info("UnifiedSocialService initialized for Facebook, Instagram, Twitter, LinkedIn")

    # ==================== ACCOUNT CONNECTION ====================

    async def get_auth_url(self, platform: str, user_id: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Generate OAuth authorization URL for platform connection.

        Args:
            platform: "facebook", "instagram", "twitter", "linkedin"
            user_id: User identifier
            redirect_uri: Where to redirect after auth

        Returns:
            Dict with authorization_url and state
        """
        try:
            import secrets
            state = secrets.token_urlsafe(32)

            # Store state for verification
            await self.db.oauth_states.insert_one({
                "state": state,
                "user_id": user_id,
                "platform": platform,
                "redirect_uri": redirect_uri,
                "created_at": datetime.now(timezone.utc),
                "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10)
            })

            if platform == "facebook":
                params = {
                    "client_id": self.platforms["facebook"]["app_id"],
                    "redirect_uri": redirect_uri,
                    "state": state,
                    "scope": "pages_manage_posts,pages_read_engagement,pages_show_list,instagram_basic,instagram_content_publish,public_profile"
                }
                auth_url = f"{self.platforms['facebook']['auth_url']}?{'&'.join(f'{k}={v}' for k, v in params.items())}"

            elif platform == "instagram":
                # Instagram uses Facebook OAuth
                params = {
                    "client_id": self.platforms["instagram"]["app_id"],
                    "redirect_uri": redirect_uri,
                    "state": state,
                    "scope": "instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement"
                }
                auth_url = f"https://www.facebook.com/v18.0/dialog/oauth?{'&'.join(f'{k}={v}' for k, v in params.items())}"

            elif platform == "twitter":
                params = {
                    "client_id": self.platforms["twitter"]["api_key"],
                    "redirect_uri": redirect_uri,
                    "state": state,
                    "response_type": "code",
                    "scope": "tweet.read tweet.write users.read offline.access"
                }
                auth_url = f"{self.platforms['twitter']['auth_url']}?{'&'.join(f'{k}={v}' for k, v in params.items())}"

            elif platform == "linkedin":
                params = {
                    "client_id": self.platforms["linkedin"]["client_id"],
                    "redirect_uri": redirect_uri,
                    "state": state,
                    "response_type": "code",
                    "scope": "w_member_social r_liteprofile r_emailaddress"
                }
                auth_url = f"{self.platforms['linkedin']['auth_url']}?{'&'.join(f'{k}={v}' for k, v in params.items())}"

            else:
                raise ValueError(f"Unsupported platform: {platform}")

            return {
                "status": "success",
                "authorization_url": auth_url,
                "state": state,
                "platform": platform
            }

        except Exception as e:
            logger.error(f"Error generating auth URL for {platform}: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def handle_oauth_callback(
        self,
        platform: str,
        code: str,
        state: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Handle OAuth callback and exchange code for access token.

        Args:
            platform: Platform name
            code: Authorization code
            state: State parameter for verification
            user_id: User identifier

        Returns:
            Dict with status and account info
        """
        try:
            # Verify state
            state_doc = await self.db.oauth_states.find_one({
                "state": state,
                "user_id": user_id,
                "platform": platform
            })

            if not state_doc:
                return {"status": "error", "error": "Invalid state parameter"}

            # Check if expired
            if datetime.now(timezone.utc) > datetime.fromisoformat(state_doc["expires_at"]):
                return {"status": "error", "error": "State expired"}

            redirect_uri = state_doc["redirect_uri"]

            # Exchange code for token
            if platform == "facebook":
                result = await self._exchange_facebook_code(code, redirect_uri, user_id)
            elif platform == "instagram":
                result = await self._exchange_instagram_code(code, redirect_uri, user_id)
            elif platform == "twitter":
                result = await self._exchange_twitter_code(code, redirect_uri, user_id)
            elif platform == "linkedin":
                result = await self._exchange_linkedin_code(code, redirect_uri, user_id)
            else:
                return {"status": "error", "error": f"Unsupported platform: {platform}"}

            # Clean up state
            await self.db.oauth_states.delete_one({"state": state})

            return result

        except Exception as e:
            logger.error(f"OAuth callback error for {platform}: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _exchange_facebook_code(self, code: str, redirect_uri: str, user_id: str) -> Dict[str, Any]:
        """Exchange Facebook authorization code for access token."""
        try:
            async with httpx.AsyncClient() as client:
                # Get access token
                token_params = {
                    "client_id": self.platforms["facebook"]["app_id"],
                    "client_secret": self.platforms["facebook"]["app_secret"],
                    "redirect_uri": redirect_uri,
                    "code": code
                }

                response = await client.get(
                    self.platforms["facebook"]["token_url"],
                    params=token_params
                )

                if response.status_code != 200:
                    logger.error(f"Facebook token exchange failed: {response.text}")
                    return {"status": "error", "error": "Token exchange failed"}

                token_data = response.json()
                access_token = token_data["access_token"]

                # Get user pages (for posting)
                pages_response = await client.get(
                    f"{self.platforms['facebook']['api_base']}/me/accounts",
                    params={"access_token": access_token}
                )

                pages_data = pages_response.json()

                # Store each page as separate account
                accounts_created = []
                for page in pages_data.get("data", []):
                    account_id = f"fb_{page['id']}"

                    account_doc = {
                        "user_id": user_id,
                        "platform": "facebook",
                        "account_id": account_id,
                        "account_name": page.get("name"),
                        "account_username": page.get("name"),
                        "profile_picture": None,
                        "auth_type": "oauth",
                        "credentials": {
                            "access_token": page["access_token"],  # Page access token
                            "page_id": page["id"],
                            "token_expires_at": None  # Page tokens don't expire
                        },
                        "account_info": {
                            "page_id": page["id"],
                            "category": page.get("category"),
                            "tasks": page.get("tasks", [])
                        },
                        "status": "active",
                        "connected_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    }

                    await self.db.social_accounts.update_one(
                        {"user_id": user_id, "account_id": account_id},
                        {"$set": account_doc},
                        upsert=True
                    )

                    accounts_created.append({
                        "account_id": account_id,
                        "name": page.get("name"),
                        "platform": "facebook"
                    })

                return {
                    "status": "success",
                    "platform": "facebook",
                    "accounts": accounts_created,
                    "message": f"Connected {len(accounts_created)} Facebook page(s)"
                }

        except Exception as e:
            logger.error(f"Facebook code exchange error: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _exchange_instagram_code(self, code: str, redirect_uri: str, user_id: str) -> Dict[str, Any]:
        """Exchange Instagram authorization code for access token."""
        try:
            # Instagram uses Facebook Graph API
            async with httpx.AsyncClient() as client:
                # Get access token
                token_params = {
                    "client_id": self.platforms["instagram"]["app_id"],
                    "client_secret": self.platforms["instagram"]["app_secret"],
                    "redirect_uri": redirect_uri,
                    "code": code
                }

                response = await client.get(
                    f"https://graph.facebook.com/v18.0/oauth/access_token",
                    params=token_params
                )

                if response.status_code != 200:
                    return {"status": "error", "error": "Token exchange failed"}

                token_data = response.json()
                access_token = token_data["access_token"]

                # Get Facebook pages
                pages_response = await client.get(
                    f"{self.platforms['instagram']['api_base']}/me/accounts",
                    params={"access_token": access_token}
                )

                pages_data = pages_response.json()
                accounts_created = []

                # For each page, get connected Instagram Business account
                for page in pages_data.get("data", []):
                    ig_response = await client.get(
                        f"{self.platforms['instagram']['api_base']}/{page['id']}",
                        params={
                            "fields": "instagram_business_account",
                            "access_token": page["access_token"]
                        }
                    )

                    ig_data = ig_response.json()

                    if "instagram_business_account" in ig_data:
                        ig_account_id = ig_data["instagram_business_account"]["id"]

                        # Get Instagram account info
                        ig_info_response = await client.get(
                            f"{self.platforms['instagram']['api_base']}/{ig_account_id}",
                            params={
                                "fields": "username,profile_picture_url,followers_count,follows_count,media_count",
                                "access_token": page["access_token"]
                            }
                        )

                        ig_info = ig_info_response.json()

                        account_id = f"ig_{ig_account_id}"

                        account_doc = {
                            "user_id": user_id,
                            "platform": "instagram",
                            "account_id": account_id,
                            "account_name": ig_info.get("username"),
                            "account_username": ig_info.get("username"),
                            "profile_picture": ig_info.get("profile_picture_url"),
                            "auth_type": "oauth",
                            "credentials": {
                                "access_token": page["access_token"],
                                "instagram_business_id": ig_account_id,
                                "page_id": page["id"]
                            },
                            "account_info": {
                                "followers": ig_info.get("followers_count", 0),
                                "following": ig_info.get("follows_count", 0),
                                "posts_count": ig_info.get("media_count", 0),
                                "business_account": True
                            },
                            "status": "active",
                            "connected_at": datetime.now(timezone.utc),
                            "updated_at": datetime.now(timezone.utc)
                        }

                        await self.db.social_accounts.update_one(
                            {"user_id": user_id, "account_id": account_id},
                            {"$set": account_doc},
                            upsert=True
                        )

                        accounts_created.append({
                            "account_id": account_id,
                            "name": ig_info.get("username"),
                            "platform": "instagram"
                        })

                if not accounts_created:
                    return {
                        "status": "error",
                        "error": "No Instagram Business accounts found. Please convert your Instagram account to a Business account and connect it to a Facebook Page."
                    }

                return {
                    "status": "success",
                    "platform": "instagram",
                    "accounts": accounts_created,
                    "message": f"Connected {len(accounts_created)} Instagram Business account(s)"
                }

        except Exception as e:
            logger.error(f"Instagram code exchange error: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _exchange_twitter_code(self, code: str, redirect_uri: str, user_id: str) -> Dict[str, Any]:
        """Exchange Twitter authorization code for access token."""
        try:
            async with httpx.AsyncClient() as client:
                # Exchange code for token
                token_data = {
                    "code": code,
                    "grant_type": "authorization_code",
                    "client_id": self.platforms["twitter"]["api_key"],
                    "redirect_uri": redirect_uri,
                    "code_verifier": "challenge"  # Should be stored during auth URL generation
                }

                response = await client.post(
                    self.platforms["twitter"]["token_url"],
                    data=token_data,
                    auth=(
                        self.platforms["twitter"]["api_key"],
                        self.platforms["twitter"]["api_secret"]
                    )
                )

                if response.status_code != 200:
                    return {"status": "error", "error": "Token exchange failed"}

                token_response = response.json()
                access_token = token_response["access_token"]
                refresh_token = token_response.get("refresh_token")

                # Get user info
                user_response = await client.get(
                    f"{self.platforms['twitter']['api_base']}/users/me",
                    params={"user.fields": "profile_image_url,public_metrics"},
                    headers={"Authorization": f"Bearer {access_token}"}
                )

                user_data = user_response.json().get("data", {})
                account_id = f"tw_{user_data['id']}"

                account_doc = {
                    "user_id": user_id,
                    "platform": "twitter",
                    "account_id": account_id,
                    "account_name": user_data.get("name"),
                    "account_username": user_data.get("username"),
                    "profile_picture": user_data.get("profile_image_url"),
                    "auth_type": "oauth",
                    "credentials": {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "token_expires_at": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
                    },
                    "account_info": {
                        "followers": user_data.get("public_metrics", {}).get("followers_count", 0),
                        "following": user_data.get("public_metrics", {}).get("following_count", 0),
                        "verified": user_data.get("verified", False)
                    },
                    "status": "active",
                    "connected_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }

                await self.db.social_accounts.update_one(
                    {"user_id": user_id, "account_id": account_id},
                    {"$set": account_doc},
                    upsert=True
                )

                return {
                    "status": "success",
                    "platform": "twitter",
                    "accounts": [{
                        "account_id": account_id,
                        "name": user_data.get("username"),
                        "platform": "twitter"
                    }],
                    "message": "Connected Twitter account"
                }

        except Exception as e:
            logger.error(f"Twitter code exchange error: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _exchange_linkedin_code(self, code: str, redirect_uri: str, user_id: str) -> Dict[str, Any]:
        """Exchange LinkedIn authorization code for access token."""
        try:
            async with httpx.AsyncClient() as client:
                # Exchange code for token
                token_data = {
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": self.platforms["linkedin"]["client_id"],
                    "client_secret": self.platforms["linkedin"]["client_secret"]
                }

                response = await client.post(
                    self.platforms["linkedin"]["token_url"],
                    data=token_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )

                if response.status_code != 200:
                    return {"status": "error", "error": "Token exchange failed"}

                token_response = response.json()
                access_token = token_response["access_token"]

                # Get user info
                user_response = await client.get(
                    f"{self.platforms['linkedin']['api_base']}/me",
                    headers={"Authorization": f"Bearer {access_token}"}
                )

                user_data = user_response.json()
                account_id = f"li_{user_data['id']}"

                account_doc = {
                    "user_id": user_id,
                    "platform": "linkedin",
                    "account_id": account_id,
                    "account_name": f"{user_data.get('localizedFirstName', '')} {user_data.get('localizedLastName', '')}",
                    "account_username": user_data.get('id'),
                    "profile_picture": None,
                    "auth_type": "oauth",
                    "credentials": {
                        "access_token": access_token,
                        "token_expires_at": (datetime.now(timezone.utc) + timedelta(days=60)).isoformat()
                    },
                    "account_info": {},
                    "status": "active",
                    "connected_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }

                await self.db.social_accounts.update_one(
                    {"user_id": user_id, "account_id": account_id},
                    {"$set": account_doc},
                    upsert=True
                )

                return {
                    "status": "success",
                    "platform": "linkedin",
                    "accounts": [{
                        "account_id": account_id,
                        "name": account_doc["account_name"],
                        "platform": "linkedin"
                    }],
                    "message": "Connected LinkedIn account"
                }

        except Exception as e:
            logger.error(f"LinkedIn code exchange error: {str(e)}")
            return {"status": "error", "error": str(e)}

    # ==================== ACCOUNT MANAGEMENT ====================

    async def get_connected_accounts(self, user_id: str, platform: str = None) -> Dict[str, Any]:
        """Get all connected social media accounts for a user."""
        try:
            query = {"user_id": user_id, "status": "active"}
            if platform:
                query["platform"] = platform

            accounts = await self.db.social_accounts.find(
                query,
                {"_id": 0, "credentials.access_token": 0, "credentials.refresh_token": 0}
            ).to_list(100)

            return {
                "status": "success",
                "accounts": accounts,
                "count": len(accounts)
            }

        except Exception as e:
            logger.error(f"Error getting connected accounts: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def disconnect_account(self, account_id: str, user_id: str) -> Dict[str, Any]:
        """Disconnect a social media account."""
        try:
            result = await self.db.social_accounts.update_one(
                {"account_id": account_id, "user_id": user_id},
                {"$set": {"status": "disconnected", "updated_at": datetime.now(timezone.utc)}}
            )

            if result.modified_count > 0:
                return {"status": "success", "message": "Account disconnected"}
            else:
                return {"status": "error", "error": "Account not found"}

        except Exception as e:
            logger.error(f"Error disconnecting account: {str(e)}")
            return {"status": "error", "error": str(e)}

    # ==================== POSTING ====================

    async def post_to_platform(
        self,
        account_id: str,
        content: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Post content to a specific platform account.

        Args:
            account_id: Account identifier
            content: Dict with message, images, videos, link
            user_id: User identifier

        Returns:
            Dict with status and platform_post_id
        """
        try:
            # Get account
            account = await self.db.social_accounts.find_one({
                "account_id": account_id,
                "user_id": user_id,
                "status": "active"
            })

            if not account:
                return {"status": "error", "error": "Account not found or not active"}

            platform = account["platform"]

            # Post to platform
            if platform == "facebook":
                result = await self._post_to_facebook(account, content)
            elif platform == "instagram":
                result = await self._post_to_instagram(account, content)
            elif platform == "twitter":
                result = await self._post_to_twitter(account, content)
            elif platform == "linkedin":
                result = await self._post_to_linkedin(account, content)
            else:
                return {"status": "error", "error": f"Unsupported platform: {platform}"}

            # Update last_used
            await self.db.social_accounts.update_one(
                {"account_id": account_id},
                {"$set": {"last_used": datetime.now(timezone.utc)}}
            )

            return result

        except Exception as e:
            logger.error(f"Error posting to platform: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def _post_to_facebook(self, account: Dict, content: Dict) -> Dict[str, Any]:
        """Post to Facebook page."""
        try:
            async with httpx.AsyncClient() as client:
                page_id = account["credentials"]["page_id"]
                access_token = account["credentials"]["access_token"]

                post_data = {
                    "message": content.get("message", ""),
                    "access_token": access_token
                }

                if content.get("link"):
                    post_data["link"] = content["link"]

                # If images, use photo endpoint
                if content.get("images") and len(content["images"]) > 0:
                    # For now, post first image (can be enhanced for multiple)
                    post_data["url"] = content["images"][0]
                    endpoint = f"https://graph.facebook.com/v18.0/{page_id}/photos"
                else:
                    endpoint = f"https://graph.facebook.com/v18.0/{page_id}/feed"

                response = await client.post(endpoint, data=post_data)

                if response.status_code == 200:
                    response_data = response.json()
                    return {
                        "status": "published",
                        "platform_post_id": response_data.get("id"),
                        "platform": "facebook"
                    }
                else:
                    logger.error(f"Facebook post failed: {response.text}")
                    return {
                        "status": "failed",
                        "error": response.text
                    }

        except Exception as e:
            logger.error(f"Facebook posting error: {str(e)}")
            return {"status": "failed", "error": str(e)}

    async def _post_to_instagram(self, account: Dict, content: Dict) -> Dict[str, Any]:
        """Post to Instagram Business account."""
        try:
            async with httpx.AsyncClient() as client:
                ig_account_id = account["credentials"]["instagram_business_id"]
                access_token = account["credentials"]["access_token"]

                # Instagram requires image URL
                if not content.get("images"):
                    return {"status": "failed", "error": "Instagram requires at least one image"}

                image_url = content["images"][0]
                caption = content.get("message", "")

                # Step 1: Create media container
                container_data = {
                    "image_url": image_url,
                    "caption": caption,
                    "access_token": access_token
                }

                container_response = await client.post(
                    f"https://graph.facebook.com/v18.0/{ig_account_id}/media",
                    data=container_data
                )

                if container_response.status_code != 200:
                    return {"status": "failed", "error": container_response.text}

                container_id = container_response.json()["id"]

                # Step 2: Publish media
                publish_response = await client.post(
                    f"https://graph.facebook.com/v18.0/{ig_account_id}/media_publish",
                    data={"creation_id": container_id, "access_token": access_token}
                )

                if publish_response.status_code == 200:
                    return {
                        "status": "published",
                        "platform_post_id": publish_response.json().get("id"),
                        "platform": "instagram"
                    }
                else:
                    return {"status": "failed", "error": publish_response.text}

        except Exception as e:
            logger.error(f"Instagram posting error: {str(e)}")
            return {"status": "failed", "error": str(e)}

    async def _post_to_twitter(self, account: Dict, content: Dict) -> Dict[str, Any]:
        """Post to Twitter."""
        try:
            async with httpx.AsyncClient() as client:
                access_token = account["credentials"]["access_token"]

                tweet_data = {
                    "text": content.get("message", "")
                }

                response = await client.post(
                    f"https://api.twitter.com/2/tweets",
                    json=tweet_data,
                    headers={"Authorization": f"Bearer {access_token}"}
                )

                if response.status_code == 201:
                    return {
                        "status": "published",
                        "platform_post_id": response.json().get("data", {}).get("id"),
                        "platform": "twitter"
                    }
                else:
                    return {"status": "failed", "error": response.text}

        except Exception as e:
            logger.error(f"Twitter posting error: {str(e)}")
            return {"status": "failed", "error": str(e)}

    async def _post_to_linkedin(self, account: Dict, content: Dict) -> Dict[str, Any]:
        """Post to LinkedIn."""
        try:
            async with httpx.AsyncClient() as client:
                access_token = account["credentials"]["access_token"]
                author_id = account["account_username"]  # LinkedIn user ID

                share_data = {
                    "author": f"urn:li:person:{author_id}",
                    "lifecycleState": "PUBLISHED",
                    "specificContent": {
                        "com.linkedin.ugc.ShareContent": {
                            "shareCommentary": {
                                "text": content.get("message", "")
                            },
                            "shareMediaCategory": "NONE"
                        }
                    },
                    "visibility": {
                        "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                    }
                }

                if content.get("link"):
                    share_data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "ARTICLE"
                    share_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [{
                        "status": "READY",
                        "originalUrl": content["link"]
                    }]

                response = await client.post(
                    f"https://api.linkedin.com/v2/ugcPosts",
                    json=share_data,
                    headers={"Authorization": f"Bearer {access_token}"}
                )

                if response.status_code in [200, 201]:
                    return {
                        "status": "published",
                        "platform_post_id": response.json().get("id"),
                        "platform": "linkedin"
                    }
                else:
                    return {"status": "failed", "error": response.text}

        except Exception as e:
            logger.error(f"LinkedIn posting error: {str(e)}")
            return {"status": "failed", "error": str(e)}

    async def post_to_multiple(
        self,
        account_ids: List[str],
        content: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Post same content to multiple accounts."""
        results = []

        for account_id in account_ids:
            result = await self.post_to_platform(account_id, content, user_id)
            results.append({
                "account_id": account_id,
                **result
            })

        success_count = sum(1 for r in results if r.get("status") == "published")

        return {
            "status": "completed",
            "results": results,
            "success_count": success_count,
            "total_count": len(account_ids)
        }
