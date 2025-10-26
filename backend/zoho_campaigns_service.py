"""
Zoho Campaigns Service

Handles email marketing campaign operations:
- Campaign creation and management
- Mailing list management
- Email templates
- Campaign analytics and tracking
"""

import logging
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ZohoCampaignsService:
    """
    Complete Zoho Campaigns integration for email marketing.
    """

    # Zoho Campaigns API base URL
    API_BASE_URL = "https://campaigns.zoho.com/api/v1.1"

    def __init__(self, auth_service):
        """
        Initialize Zoho Campaigns Service.

        Args:
            auth_service: ZohoAuthService instance for authentication
        """
        self.auth_service = auth_service
        logger.info("Zoho Campaigns Service initialized")

    async def _get_headers(self, user_id: str = "default_user") -> Optional[Dict[str, str]]:
        """Get authorization headers with valid access token."""
        access_token = await self.auth_service.get_valid_access_token(user_id)
        if not access_token:
            logger.error(f"No valid access token for user: {user_id}")
            return None

        return {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Content-Type": "application/json"
        }

    async def create_mailing_list(
        self,
        list_name: str,
        list_description: str = "",
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Create a mailing list.

        Args:
            list_name: Name of the mailing list
            list_description: Description
            user_id: User identifier

        Returns:
            Dict with created list details
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {
                    "status": "error",
                    "message": "No valid Zoho connection"
                }

            url = f"{self.API_BASE_URL}/createmailinglist"
            params = {
                "listname": list_name,
                "description": list_description
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, params=params)

                if response.status_code in [200, 201]:
                    result = response.json()
                    list_key = result.get("list_key")

                    logger.info(f"Created mailing list: {list_name} ({list_key})")

                    return {
                        "status": "success",
                        "list_key": list_key,
                        "list_name": list_name,
                        "message": "Mailing list created successfully"
                    }
                else:
                    error_data = response.json()
                    return {
                        "status": "error",
                        "message": error_data.get("message", "Failed to create mailing list")
                    }

        except Exception as e:
            logger.error(f"Error creating mailing list: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def add_contacts_to_list(
        self,
        list_key: str,
        contacts: List[Dict[str, Any]],
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Add contacts to a mailing list.

        Args:
            list_key: Mailing list key
            contacts: List of contact dicts with 'Contact Email', 'First Name', etc.
            user_id: User identifier

        Returns:
            Dict with add status
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            url = f"{self.API_BASE_URL}/{list_key}/contacts/add"
            contact_data = {"contactinfo": contacts}

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=contact_data)

                if response.status_code in [200, 201]:
                    result = response.json()
                    logger.info(f"Added {len(contacts)} contacts to list {list_key}")

                    return {
                        "status": "success",
                        "message": f"Added {len(contacts)} contacts",
                        "details": result
                    }
                else:
                    error_data = response.json()
                    return {
                        "status": "error",
                        "message": error_data.get("message", "Failed to add contacts")
                    }

        except Exception as e:
            logger.error(f"Error adding contacts: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def create_campaign(
        self,
        campaign_name: str,
        list_key: str,
        subject: str,
        from_email: str,
        html_content: str,
        campaign_type: str = "email",
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Create an email campaign.

        Args:
            campaign_name: Campaign name
            list_key: Mailing list key to send to
            subject: Email subject
            from_email: From email address
            html_content: Email HTML content
            campaign_type: Campaign type (email, test, scheduled)
            user_id: User identifier

        Returns:
            Dict with created campaign details
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            url = f"{self.API_BASE_URL}/createcampaign"

            campaign_data = {
                "campaign_name": campaign_name,
                "from_email": from_email,
                "subject": subject,
                "mail_content": html_content,
                "list_key": list_key,
                "campaign_type": campaign_type
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=campaign_data)

                if response.status_code in [200, 201]:
                    result = response.json()
                    campaign_key = result.get("campaign_key")

                    logger.info(f"Created campaign: {campaign_name} ({campaign_key})")

                    return {
                        "status": "success",
                        "campaign_key": campaign_key,
                        "campaign_name": campaign_name,
                        "message": "Campaign created successfully"
                    }
                else:
                    error_data = response.json()
                    return {
                        "status": "error",
                        "message": error_data.get("message", "Failed to create campaign")
                    }

        except Exception as e:
            logger.error(f"Error creating campaign: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def send_campaign(
        self,
        campaign_key: str,
        schedule_time: str = None,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Send or schedule a campaign.

        Args:
            campaign_key: Campaign key
            schedule_time: ISO format datetime to schedule (None = send immediately)
            user_id: User identifier

        Returns:
            Dict with send status
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            if schedule_time:
                url = f"{self.API_BASE_URL}/{campaign_key}/schedulecampaign"
                params = {"scheduled_time": schedule_time}
            else:
                url = f"{self.API_BASE_URL}/{campaign_key}/sendcampaign"
                params = {}

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, params=params)

                if response.status_code in [200, 201]:
                    logger.info(f"Campaign {campaign_key} sent/scheduled")

                    return {
                        "status": "success",
                        "message": "Campaign sent" if not schedule_time else "Campaign scheduled",
                        "campaign_key": campaign_key
                    }
                else:
                    error_data = response.json()
                    return {
                        "status": "error",
                        "message": error_data.get("message", "Failed to send campaign")
                    }

        except Exception as e:
            logger.error(f"Error sending campaign: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def get_campaign_details(
        self,
        campaign_key: str,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Get campaign details and statistics.

        Args:
            campaign_key: Campaign key
            user_id: User identifier

        Returns:
            Dict with campaign details
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            url = f"{self.API_BASE_URL}/{campaign_key}/getcampaigndetails"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "status": "success",
                        "campaign": result
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Campaign not found"
                    }

        except Exception as e:
            logger.error(f"Error getting campaign details: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def get_campaign_statistics(
        self,
        campaign_key: str,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Get campaign analytics and statistics.

        Args:
            campaign_key: Campaign key
            user_id: User identifier

        Returns:
            Dict with statistics (open rate, click rate, etc.)
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            url = f"{self.API_BASE_URL}/{campaign_key}/stats"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "status": "success",
                        "statistics": {
                            "sent": result.get("sent", 0),
                            "opened": result.get("opened", 0),
                            "clicked": result.get("clicked", 0),
                            "bounced": result.get("bounced", 0),
                            "unsubscribed": result.get("unsubscribed", 0),
                            "open_rate": result.get("open_rate", 0),
                            "click_rate": result.get("click_rate", 0)
                        }
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Statistics not available"
                    }

        except Exception as e:
            logger.error(f"Error getting campaign statistics: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def list_campaigns(
        self,
        status: str = "all",
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        List all campaigns.

        Args:
            status: Filter by status (all, sent, scheduled, draft)
            user_id: User identifier

        Returns:
            Dict with campaigns list
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            url = f"{self.API_BASE_URL}/listcampaigns"
            params = {"status": status}

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params)

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "status": "success",
                        "campaigns": result.get("campaigns", [])
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Failed to list campaigns"
                    }

        except Exception as e:
            logger.error(f"Error listing campaigns: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def list_mailing_lists(self, user_id: str = "default_user") -> Dict[str, Any]:
        """
        List all mailing lists.

        Args:
            user_id: User identifier

        Returns:
            Dict with mailing lists
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            url = f"{self.API_BASE_URL}/getmailinglists"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "status": "success",
                        "lists": result.get("list_of_details", [])
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Failed to list mailing lists"
                    }

        except Exception as e:
            logger.error(f"Error listing mailing lists: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def delete_campaign(
        self,
        campaign_key: str,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Delete a campaign.

        Args:
            campaign_key: Campaign key
            user_id: User identifier

        Returns:
            Dict with deletion status
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            url = f"{self.API_BASE_URL}/{campaign_key}/deletecampaign"

            async with httpx.AsyncClient() as client:
                response = await client.delete(url, headers=headers)

                if response.status_code == 200:
                    return {
                        "status": "success",
                        "message": "Campaign deleted successfully"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Failed to delete campaign"
                    }

        except Exception as e:
            logger.error(f"Error deleting campaign: {str(e)}")
            return {"status": "error", "message": str(e)}
