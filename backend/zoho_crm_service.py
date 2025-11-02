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

    # ============================================================
    # CAMPAIGN DATA MANAGEMENT - Save Scraped Contacts & Content
    # ============================================================

    async def save_scraped_contacts(
        self,
        contacts: List[Dict[str, Any]],
        campaign_id: str,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Save scraped contacts to Zoho CRM Leads module and link to campaign.

        Args:
            contacts: List of contact dictionaries with name, email, phone, etc.
            campaign_id: Zoho CRM campaign ID to link contacts to
            user_id: User identifier

        Returns:
            Dict with save status and created lead IDs
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            # Format contacts for Zoho Leads module
            leads_data = []
            for contact in contacts:
                # Split name into first and last name
                name_parts = contact.get("name", "Unknown").split(" ", 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ""

                lead = {
                    "First_Name": first_name,
                    "Last_Name": last_name,
                    "Email": contact.get("email"),
                    "Phone": contact.get("phone"),
                    "Company": contact.get("company", contact.get("business_name")),
                    "Website": contact.get("website"),
                    "Street": contact.get("address", contact.get("street")),
                    "City": contact.get("city"),
                    "State": contact.get("state"),
                    "Zip_Code": contact.get("zip_code", contact.get("postal_code")),
                    "Country": contact.get("country"),
                    "Lead_Source": "Scraped Data",
                    "Lead_Status": "Not Contacted",
                    "Description": f"Scraped for campaign {campaign_id}",
                    # Custom fields
                    "Rating": contact.get("rating"),
                    "Industry": contact.get("industry"),
                    # Link to campaign
                    "$se_module": "Campaigns",
                    "$campaigns": [{"id": campaign_id}]
                }

                # Remove None values
                lead = {k: v for k, v in lead.items() if v is not None}
                leads_data.append(lead)

            # Zoho allows max 100 records per API call, batch if needed
            created_leads = []
            batch_size = 100

            for i in range(0, len(leads_data), batch_size):
                batch = leads_data[i:i + batch_size]
                zoho_payload = {"data": batch}
                url = f"{self.API_BASE_URL}/Leads"

                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, headers=headers, json=zoho_payload)

                    if response.status_code in [200, 201]:
                        result = response.json()
                        for record in result.get("data", []):
                            if record.get("status") == "success":
                                created_leads.append({
                                    "id": record["details"]["id"],
                                    "email": batch[result["data"].index(record)].get("Email")
                                })
                        logger.info(f"Created {len(batch)} leads in Zoho CRM")
                    else:
                        error_data = response.json()
                        logger.error(f"Failed to create leads batch: {error_data}")

            return {
                "status": "success",
                "message": f"Successfully saved {len(created_leads)} contacts to Zoho CRM",
                "created_leads": created_leads,
                "total_contacts": len(contacts),
                "successful": len(created_leads),
                "campaign_id": campaign_id
            }

        except Exception as e:
            logger.error(f"Error saving scraped contacts: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def get_campaign_contacts(
        self,
        campaign_id: str,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Get all contacts/leads associated with a campaign.

        Args:
            campaign_id: Zoho CRM campaign ID
            user_id: User identifier

        Returns:
            Dict with contact list
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            # Get leads linked to this campaign
            url = f"{self.API_BASE_URL}/Campaigns/{campaign_id}/Leads"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    result = response.json()
                    contacts = result.get("data", [])

                    return {
                        "status": "success",
                        "contacts": contacts,
                        "count": len(contacts),
                        "campaign_id": campaign_id
                    }
                else:
                    logger.warning(f"No contacts found for campaign {campaign_id}")
                    return {
                        "status": "success",
                        "contacts": [],
                        "count": 0,
                        "campaign_id": campaign_id
                    }

        except Exception as e:
            logger.error(f"Error getting campaign contacts: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def save_campaign_content(
        self,
        campaign_id: str,
        content_data: Dict[str, Any],
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Save generated content to campaign notes/description.

        Args:
            campaign_id: Zoho CRM campaign ID
            content_data: Content generated by ContentAgent
            user_id: User identifier

        Returns:
            Dict with save status
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            # Format content for campaign description/notes
            content_text = f"""
=== GENERATED CAMPAIGN CONTENT ===

Subject Line: {content_data.get('subject_line', 'N/A')}
Preview Text: {content_data.get('preview_text', 'N/A')}

Email Body:
{content_data.get('body', content_data.get('text', 'N/A'))}

Call-to-Action: {content_data.get('cta', content_data.get('cta_text', 'N/A'))}

Personalization Tokens: {', '.join(content_data.get('personalization_tokens', []))}

Variants:
{chr(10).join(f'- {v}' for v in content_data.get('variants', []))}

Generated by: ContentAgent
Timestamp: {datetime.now(timezone.utc).isoformat()}
"""

            # Update campaign with content
            update_data = {
                "Description": content_text,
                "Content_Generated": True,
                "Content_Type": content_data.get("content_type", "email")
            }

            result = await self.update_campaign(campaign_id, update_data, user_id)

            if result["status"] == "success":
                logger.info(f"Saved content to campaign {campaign_id}")
                return {
                    "status": "success",
                    "message": "Campaign content saved to Zoho CRM",
                    "campaign_id": campaign_id
                }
            else:
                return result

        except Exception as e:
            logger.error(f"Error saving campaign content: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def get_campaign_content(
        self,
        campaign_id: str,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Get campaign content from Zoho CRM.

        Args:
            campaign_id: Zoho CRM campaign ID
            user_id: User identifier

        Returns:
            Dict with campaign content
        """
        try:
            campaign_result = await self.get_campaign(campaign_id, user_id)

            if campaign_result["status"] == "success":
                campaign = campaign_result["campaign"]
                content = {
                    "description": campaign.get("Description", ""),
                    "content_generated": campaign.get("Content_Generated", False),
                    "content_type": campaign.get("Content_Type", ""),
                    "campaign_name": campaign.get("Campaign_Name", "")
                }

                return {
                    "status": "success",
                    "content": content
                }
            else:
                return campaign_result

        except Exception as e:
            logger.error(f"Error getting campaign content: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def bulk_create_contacts(
        self,
        contacts: List[Dict[str, Any]],
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Bulk create contacts in Zoho CRM Contacts module (not Leads).

        Args:
            contacts: List of contact dictionaries
            user_id: User identifier

        Returns:
            Dict with creation status
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            # Format contacts for Zoho Contacts module
            contacts_data = []
            for contact in contacts:
                name_parts = contact.get("name", "Unknown").split(" ", 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ""

                contact_record = {
                    "First_Name": first_name,
                    "Last_Name": last_name,
                    "Email": contact.get("email"),
                    "Phone": contact.get("phone"),
                    "Mailing_Street": contact.get("address", contact.get("street")),
                    "Mailing_City": contact.get("city"),
                    "Mailing_State": contact.get("state"),
                    "Mailing_Zip": contact.get("zip_code"),
                    "Mailing_Country": contact.get("country"),
                    "Description": contact.get("description", "Imported via scraping")
                }

                # Remove None values
                contact_record = {k: v for k, v in contact_record.items() if v is not None}
                contacts_data.append(contact_record)

            # Batch create (max 100 per request)
            created_contacts = []
            batch_size = 100

            for i in range(0, len(contacts_data), batch_size):
                batch = contacts_data[i:i + batch_size]
                zoho_payload = {"data": batch}
                url = f"{self.API_BASE_URL}/Contacts"

                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, headers=headers, json=zoho_payload)

                    if response.status_code in [200, 201]:
                        result = response.json()
                        for record in result.get("data", []):
                            if record.get("status") == "success":
                                created_contacts.append(record["details"]["id"])

            return {
                "status": "success",
                "message": f"Created {len(created_contacts)} contacts in Zoho CRM",
                "created_contacts": created_contacts,
                "total": len(contacts)
            }

        except Exception as e:
            logger.error(f"Error bulk creating contacts: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def link_contacts_to_campaign(
        self,
        campaign_id: str,
        contact_ids: List[str],
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Link existing contacts to a campaign.

        Args:
            campaign_id: Zoho CRM campaign ID
            contact_ids: List of contact/lead IDs
            user_id: User identifier

        Returns:
            Dict with link status
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            # Use Associate Records API
            url = f"{self.API_BASE_URL}/Campaigns/{campaign_id}/Leads"

            # Zoho expects list of lead IDs
            payload = {
                "data": [{"id": contact_id} for contact_id in contact_ids]
            }

            async with httpx.AsyncClient() as client:
                response = await client.put(url, headers=headers, json=payload)

                if response.status_code == 200:
                    return {
                        "status": "success",
                        "message": f"Linked {len(contact_ids)} contacts to campaign",
                        "campaign_id": campaign_id
                    }
                else:
                    error_data = response.json()
                    return {
                        "status": "error",
                        "message": error_data.get("message", "Failed to link contacts")
                    }

        except Exception as e:
            logger.error(f"Error linking contacts to campaign: {str(e)}")
            return {"status": "error", "message": str(e)}
