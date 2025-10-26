"""
Zoho CRM Service

Handles all Zoho CRM operations:
- Campaign management
- Custom modules for tenants/credentials
- Records creation and management
- Campaign tracking and analytics
"""

import logging
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ZohoCRMService:
    """
    Complete Zoho CRM integration for campaign and data management.
    """

    # Zoho CRM API base URL (adjust for your data center)
    API_BASE_URL = "https://www.zohoapis.com/crm/v8"

    def __init__(self, auth_service):
        """
        Initialize Zoho CRM Service.

        Args:
            auth_service: ZohoAuthService instance for authentication
        """
        self.auth_service = auth_service
        logger.info("Zoho CRM Service initialized")

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

    async def create_campaign(
        self,
        campaign_data: Dict[str, Any],
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Create a marketing campaign in Zoho CRM.

        Args:
            campaign_data: Campaign details
            user_id: User identifier

        Returns:
            Dict with created campaign details
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {
                    "status": "error",
                    "error": "authentication_failed",
                    "message": "No valid Zoho connection. Please connect to Zoho first."
                }

            # Format data for Zoho CRM Campaigns module
            zoho_campaign = {
                "data": [{
                    "Campaign_Name": campaign_data.get("name"),
                    "Status": campaign_data.get("status", "Planning"),
                    "Type": campaign_data.get("type", "Email"),
                    "Start_Date": campaign_data.get("start_date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
                    "End_Date": campaign_data.get("end_date"),
                    "Expected_Revenue": campaign_data.get("expected_revenue", 0),
                    "Budget_Cost": campaign_data.get("budget", 0),
                    "Actual_Cost": campaign_data.get("actual_cost", 0),
                    "Expected_Response": campaign_data.get("expected_response", 0),
                    "Description": campaign_data.get("description", ""),
                    "Product": campaign_data.get("product"),
                    "Target_Audience": campaign_data.get("target_audience"),
                    # Custom fields
                    "Content_Generated": campaign_data.get("content_generated", False),
                    "AI_Generated": True,
                    "Platform": campaign_data.get("platform", "Multi-channel"),
                    "Campaign_Goal": campaign_data.get("goal")
                }]
            }

            url = f"{self.API_BASE_URL}/Campaigns"

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=zoho_campaign)

                if response.status_code in [200, 201]:
                    result = response.json()
                    campaign_id = result["data"][0]["details"]["id"]

                    logger.info(f"Created campaign in Zoho CRM: {campaign_id}")

                    return {
                        "status": "success",
                        "campaign_id": campaign_id,
                        "message": "Campaign created successfully in Zoho CRM",
                        "details": result["data"][0]
                    }
                else:
                    error_data = response.json()
                    logger.error(f"Failed to create campaign: {error_data}")
                    return {
                        "status": "error",
                        "error": "creation_failed",
                        "message": error_data.get("message", "Failed to create campaign")
                    }

        except Exception as e:
            logger.error(f"Error creating campaign: {str(e)}")
            return {
                "status": "error",
                "error": "exception",
                "message": str(e)
            }

    async def get_campaign(
        self,
        campaign_id: str,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Get campaign details by ID.

        Args:
            campaign_id: Zoho CRM campaign ID
            user_id: User identifier

        Returns:
            Dict with campaign details
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            url = f"{self.API_BASE_URL}/Campaigns/{campaign_id}"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "status": "success",
                        "campaign": result["data"][0]
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Campaign not found"
                    }

        except Exception as e:
            logger.error(f"Error getting campaign: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def update_campaign(
        self,
        campaign_id: str,
        updates: Dict[str, Any],
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Update campaign in Zoho CRM.

        Args:
            campaign_id: Zoho CRM campaign ID
            updates: Fields to update
            user_id: User identifier

        Returns:
            Dict with update status
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            zoho_update = {"data": [{"id": campaign_id, **updates}]}
            url = f"{self.API_BASE_URL}/Campaigns"

            async with httpx.AsyncClient() as client:
                response = await client.put(url, headers=headers, json=zoho_update)

                if response.status_code == 200:
                    return {
                        "status": "success",
                        "message": "Campaign updated successfully"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Failed to update campaign"
                    }

        except Exception as e:
            logger.error(f"Error updating campaign: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def list_campaigns(
        self,
        user_id: str = "default_user",
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        List all campaigns.

        Args:
            user_id: User identifier
            page: Page number
            per_page: Records per page

        Returns:
            Dict with campaigns list
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            url = f"{self.API_BASE_URL}/Campaigns"
            params = {"page": page, "per_page": per_page}

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params)

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "status": "success",
                        "campaigns": result.get("data", []),
                        "info": result.get("info", {})
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Failed to list campaigns"
                    }

        except Exception as e:
            logger.error(f"Error listing campaigns: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def create_custom_module(
        self,
        module_name: str,
        module_config: Dict[str, Any],
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Create a custom module in Zoho CRM.
        WARNING: Costs 500 credits per module!

        Args:
            module_name: Name of the module
            module_config: Module configuration
            user_id: User identifier

        Returns:
            Dict with creation status
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            module_data = {
                "modules": [{
                    "module_name": module_name,
                    "singular_label": module_config.get("singular_label", module_name),
                    "plural_label": module_config.get("plural_label", module_name + "s"),
                    "api_name": module_config.get("api_name", module_name),
                    **module_config
                }]
            }

            url = f"{self.API_BASE_URL}/settings/modules"

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=module_data)

                if response.status_code in [200, 201]:
                    result = response.json()
                    logger.info(f"Created custom module: {module_name}")
                    return {
                        "status": "success",
                        "message": f"Custom module '{module_name}' created",
                        "details": result
                    }
                else:
                    error_data = response.json()
                    return {
                        "status": "error",
                        "message": error_data.get("message", "Failed to create module")
                    }

        except Exception as e:
            logger.error(f"Error creating custom module: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def create_record(
        self,
        module_name: str,
        record_data: Dict[str, Any],
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Create a record in any Zoho CRM module.

        Args:
            module_name: Module API name (e.g., "Campaigns", "Leads", "Contacts")
            record_data: Record data
            user_id: User identifier

        Returns:
            Dict with created record details
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            zoho_record = {"data": [record_data]}
            url = f"{self.API_BASE_URL}/{module_name}"

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=zoho_record)

                if response.status_code in [200, 201]:
                    result = response.json()
                    record_id = result["data"][0]["details"]["id"]

                    return {
                        "status": "success",
                        "record_id": record_id,
                        "message": f"Record created in {module_name}",
                        "details": result["data"][0]
                    }
                else:
                    error_data = response.json()
                    return {
                        "status": "error",
                        "message": error_data.get("message", "Failed to create record")
                    }

        except Exception as e:
            logger.error(f"Error creating record: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def get_records(
        self,
        module_name: str,
        user_id: str = "default_user",
        page: int = 1,
        per_page: int = 20,
        fields: List[str] = None
    ) -> Dict[str, Any]:
        """
        Get records from any Zoho CRM module.

        Args:
            module_name: Module API name
            user_id: User identifier
            page: Page number
            per_page: Records per page
            fields: List of field API names to retrieve

        Returns:
            Dict with records
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            url = f"{self.API_BASE_URL}/{module_name}"
            params = {"page": page, "per_page": per_page}

            if fields:
                params["fields"] = ",".join(fields)

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params)

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "status": "success",
                        "records": result.get("data", []),
                        "info": result.get("info", {})
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Failed to get records"
                    }

        except Exception as e:
            logger.error(f"Error getting records: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def search_records(
        self,
        module_name: str,
        search_criteria: str,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Search records using COQL (CRM Object Query Language).

        Args:
            module_name: Module API name
            search_criteria: Search query
            user_id: User identifier

        Returns:
            Dict with search results
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            url = f"{self.API_BASE_URL}/coql"
            query_data = {
                "select_query": f"SELECT * FROM {module_name} WHERE {search_criteria}"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=query_data)

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "status": "success",
                        "records": result.get("data", []),
                        "info": result.get("info", {})
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Search failed"
                    }

        except Exception as e:
            logger.error(f"Error searching records: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def get_module_fields(
        self,
        module_name: str,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Get metadata for module fields.

        Args:
            module_name: Module API name
            user_id: User identifier

        Returns:
            Dict with field metadata
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            url = f"{self.API_BASE_URL}/settings/fields"
            params = {"module": module_name}

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params)

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "status": "success",
                        "fields": result.get("fields", [])
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Failed to get field metadata"
                    }

        except Exception as e:
            logger.error(f"Error getting module fields: {str(e)}")
            return {"status": "error", "message": str(e)}
