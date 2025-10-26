"""
Zoho OAuth 2.0 Authentication Service

Handles complete OAuth flow for Zoho services:
- Authorization code flow
- Token generation and refresh
- Multi-service scope management
- Secure token storage
"""

import logging
import httpx
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode, urlparse

logger = logging.getLogger(__name__)


class ZohoAuthService:
    """
    Complete Zoho OAuth 2.0 authentication service.
    Supports all Zoho services: CRM, Mail, Campaigns, Creator, Analytics.
    """

    # Default scopes for all services
    DEFAULT_SCOPES = [
        "ZohoCRM.modules.ALL",
        "ZohoCRM.settings.ALL",
        "ZohoCRM.users.ALL",
        "ZohoMail.messages.ALL",
        "ZohoMail.accounts.ALL",
        "ZohoCampaigns.campaign.ALL",
        "ZohoCampaigns.contact.ALL",
        "ZohoCreator.meta.ALL",
        "ZohoCreator.report.ALL",
        "ZohoAnalytics.data.ALL",
        "ZohoAnalytics.workspace.ALL"
    ]

    def __init__(
        self,
        db,
        client_id: str = None,
        client_secret: str = None,
        redirect_uri: str = None,
        data_center: str = None
    ):
        """
        Initialize Zoho Auth Service.

        Args:
            db: MongoDB database connection
            client_id: Zoho OAuth Client ID (from API Console)
            client_secret: Zoho OAuth Client Secret
            redirect_uri: OAuth redirect URI
            data_center: Optional Zoho data center suffix (e.g., "com", "in")
        """
        self.db = db
        self.client_id = client_id or os.environ.get('ZOHO_CLIENT_ID')
        self.client_secret = client_secret or os.environ.get('ZOHO_CLIENT_SECRET')
        self.redirect_uri = redirect_uri or os.environ.get('ZOHO_REDIRECT_URI')
        self.data_center = self._normalize_data_center(
            data_center or os.environ.get('ZOHO_DATA_CENTER')
        )
        self.accounts_domain = f"accounts.zoho.{self.data_center}"
        self.oauth_base_url = f"https://{self.accounts_domain}/oauth/v2"
        self.auth_url = f"{self.oauth_base_url}/auth"
        self.token_url = f"{self.oauth_base_url}/token"
        self.revoke_url = f"{self.oauth_base_url}/token/revoke"

        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            logger.warning(
                "Zoho OAuth credentials not fully configured. "
                "Set ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_REDIRECT_URI"
            )

        logger.info("Zoho Auth Service initialized")
        logger.info("Zoho data center resolved to %s", self.accounts_domain)

    @staticmethod
    def _normalize_data_center(value: Optional[str]) -> str:
        """
        Normalize Zoho data center input into a suffix (e.g., 'com', 'in').

        Supports direct suffixes, values with leading dots, hostnames, or URLs.
        Defaults to 'com' when no valid value is provided.
        """
        if not value:
            return "com"

        value = value.strip().lower()
        if not value:
            return "com"

        if value.startswith("http"):
            parsed = urlparse(value)
            host = parsed.hostname or ""
        else:
            host = value

        host = host.strip()
        host = host.lstrip(".")

        if host.startswith("accounts.zoho."):
            host = host.split("accounts.zoho.", 1)[1]
        elif host.startswith("zoho."):
            host = host.split("zoho.", 1)[1]

        host = host.strip(".")
        return host or "com"

    def get_authorization_url(
        self,
        state: str,
        scopes: List[str] = None,
        access_type: str = "offline"
    ) -> str:
        """
        Generate authorization URL for user consent.

        Args:
            state: State parameter for CSRF protection
            scopes: List of scopes to request (uses defaults if None)
            access_type: 'offline' to get refresh token, 'online' for access token only

        Returns:
            Authorization URL to redirect user to
        """
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": ",".join(scopes or self.DEFAULT_SCOPES),
            "redirect_uri": self.redirect_uri,
            "access_type": access_type,
            "state": state,
            "prompt": "consent"
        }

        auth_url = f"{self.auth_url}?{urlencode(params)}"
        logger.info(f"Generated authorization URL with state: {state}")
        return auth_url

    async def exchange_code_for_tokens(
        self,
        authorization_code: str,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            authorization_code: Code received from OAuth callback
            user_id: User identifier for storing tokens

        Returns:
            Dict with access_token, refresh_token, expires_in, etc.
        """
        try:
            async with httpx.AsyncClient() as client:
                data = {
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": self.redirect_uri,
                    "code": authorization_code
                }

                response = await client.post(self.token_url, data=data)

                if response.status_code != 200:
                    error_data = response.json()
                    logger.error(f"Token exchange failed: {error_data}")
                    return {
                        "status": "error",
                        "error": error_data.get("error"),
                        "message": error_data.get("error_description", "Token exchange failed")
                    }

                token_data = response.json()

                # Store tokens in database
                await self._store_tokens(user_id, token_data)

                logger.info(f"Successfully exchanged code for tokens for user: {user_id}")

                return {
                    "status": "success",
                    "access_token": token_data.get("access_token"),
                    "refresh_token": token_data.get("refresh_token"),
                    "expires_in": token_data.get("expires_in"),
                    "token_type": token_data.get("token_type"),
                    "scope": token_data.get("scope")
                }

        except Exception as e:
            logger.error(f"Error exchanging authorization code: {str(e)}")
            return {
                "status": "error",
                "error": "exchange_failed",
                "message": str(e)
            }

    async def refresh_access_token(self, user_id: str = "default_user") -> Dict[str, Any]:
        """
        Refresh access token using stored refresh token.
        Access tokens expire after 1 hour, use this to get new one.

        Args:
            user_id: User identifier

        Returns:
            Dict with new access_token and expires_in
        """
        try:
            # Get stored refresh token
            token_doc = await self.db.zoho_tokens.find_one({"user_id": user_id})
            if not token_doc or not token_doc.get("refresh_token"):
                logger.error(f"No refresh token found for user: {user_id}")
                return {
                    "status": "error",
                    "error": "no_refresh_token",
                    "message": "No refresh token available. User needs to re-authorize."
                }

            refresh_token = token_doc["refresh_token"]

            async with httpx.AsyncClient() as client:
                data = {
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token
                }

                response = await client.post(self.token_url, data=data)

                if response.status_code != 200:
                    error_data = response.json()
                    logger.error(f"Token refresh failed: {error_data}")
                    return {
                        "status": "error",
                        "error": error_data.get("error"),
                        "message": error_data.get("error_description", "Token refresh failed")
                    }

                token_data = response.json()

                # Update stored tokens
                await self._store_tokens(user_id, {
                    **token_data,
                    "refresh_token": refresh_token  # Keep existing refresh token
                })

                logger.info(f"Successfully refreshed access token for user: {user_id}")

                return {
                    "status": "success",
                    "access_token": token_data.get("access_token"),
                    "expires_in": token_data.get("expires_in")
                }

        except Exception as e:
            logger.error(f"Error refreshing access token: {str(e)}")
            return {
                "status": "error",
                "error": "refresh_failed",
                "message": str(e)
            }

    async def get_valid_access_token(self, user_id: str = "default_user") -> Optional[str]:
        """
        Get a valid access token, refreshing if necessary.
        This is the main method to call when you need an access token.

        Args:
            user_id: User identifier

        Returns:
            Valid access token or None if unavailable
        """
        try:
            token_doc = await self.db.zoho_tokens.find_one({"user_id": user_id})
            if not token_doc:
                logger.warning(f"No tokens found for user: {user_id}")
                return None

            # Check if token is expired or about to expire (5 min buffer)
            expires_at = datetime.fromisoformat(token_doc["expires_at"])
            now = datetime.now(timezone.utc)

            if expires_at - now < timedelta(minutes=5):
                logger.info(f"Token expired or expiring soon for user: {user_id}, refreshing...")
                refresh_result = await self.refresh_access_token(user_id)
                if refresh_result["status"] == "success":
                    return refresh_result["access_token"]
                else:
                    logger.error(f"Failed to refresh token: {refresh_result}")
                    return None

            return token_doc["access_token"]

        except Exception as e:
            logger.error(f"Error getting valid access token: {str(e)}")
            return None

    async def _store_tokens(self, user_id: str, token_data: Dict[str, Any]) -> None:
        """
        Store tokens in database with expiration tracking.

        Args:
            user_id: User identifier
            token_data: Token data from Zoho
        """
        try:
            expires_in = token_data.get("expires_in", 3600)  # Default 1 hour
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

            token_doc = {
                "user_id": user_id,
                "access_token": token_data.get("access_token"),
                "refresh_token": token_data.get("refresh_token"),
                "token_type": token_data.get("token_type", "Bearer"),
                "expires_in": expires_in,
                "expires_at": expires_at.isoformat(),
                "scope": token_data.get("scope"),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }

            await self.db.zoho_tokens.update_one(
                {"user_id": user_id},
                {"$set": token_doc},
                upsert=True
            )

            logger.info(f"Stored tokens for user: {user_id}, expires at: {expires_at}")

        except Exception as e:
            logger.error(f"Error storing tokens: {str(e)}")
            raise

    async def revoke_token(self, user_id: str = "default_user") -> Dict[str, Any]:
        """
        Revoke user's access token (disconnect Zoho integration).

        Args:
            user_id: User identifier

        Returns:
            Dict with status
        """
        try:
            access_token = await self.get_valid_access_token(user_id)
            if not access_token:
                return {
                    "status": "error",
                    "message": "No access token found"
                }

            async with httpx.AsyncClient() as client:
                params = {"token": access_token}
                response = await client.post(self.revoke_url, params=params)

                if response.status_code == 200:
                    # Remove tokens from database
                    await self.db.zoho_tokens.delete_one({"user_id": user_id})
                    logger.info(f"Revoked tokens for user: {user_id}")

                    return {
                        "status": "success",
                        "message": "Zoho integration disconnected"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Failed to revoke token"
                    }

        except Exception as e:
            logger.error(f"Error revoking token: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def get_connection_status(self, user_id: str = "default_user") -> Dict[str, Any]:
        """
        Check if user has valid Zoho connection.

        Args:
            user_id: User identifier

        Returns:
            Dict with connection status and details
        """
        try:
            token_doc = await self.db.zoho_tokens.find_one({"user_id": user_id})
            if not token_doc:
                return {
                    "connected": False,
                    "message": "Not connected to Zoho"
                }

            expires_at = datetime.fromisoformat(token_doc["expires_at"])
            now = datetime.now(timezone.utc)
            is_expired = expires_at <= now

            return {
                "connected": True,
                "is_expired": is_expired,
                "expires_at": token_doc["expires_at"],
                "scope": token_doc.get("scope"),
                "updated_at": token_doc.get("updated_at")
            }

        except Exception as e:
            logger.error(f"Error checking connection status: {str(e)}")
            return {
                "connected": False,
                "error": str(e)
            }

    def get_auth_header(self, access_token: str) -> Dict[str, str]:
        """
        Get properly formatted authorization header for Zoho API calls.

        Args:
            access_token: Valid access token

        Returns:
            Dict with Authorization header
        """
        return {
            "Authorization": f"Zoho-oauthtoken {access_token}"
        }
