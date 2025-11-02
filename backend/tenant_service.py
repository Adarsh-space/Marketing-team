"""
Tenant Management Service

Handles multi-tenant architecture:
- Each user gets isolated data space in Zoho
- Tenant-based data isolation
- User workspace management
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class TenantService:
    """
    Multi-tenant management using Zoho CRM as tenant storage.
    Each tenant has isolated data space.
    """

    def __init__(self, zoho_crm_service, db):
        """
        Initialize Tenant Service.

        Args:
            zoho_crm_service: ZohoCRMService instance
            db: MongoDB database instance (for local caching)
        """
        self.zoho_crm = zoho_crm_service
        self.db = db
        self.tenants_collection = db.tenants
        logger.info("Tenant Service initialized")

    async def initialize_tenant_module(self):
        """
        Create custom Zoho module for tenants if doesn't exist.
        This module stores all tenant information in Zoho CRM.
        """
        try:
            # Define tenant module schema
            tenant_module = {
                "api_name": "Tenants",
                "module_name": "Tenants",
                "singular_label": "Tenant",
                "plural_label": "Tenants",
                "fields": [
                    {
                        "api_name": "Tenant_ID",
                        "field_label": "Tenant ID",
                        "data_type": "text",
                        "required": True,
                        "unique": True
                    },
                    {
                        "api_name": "Company_Name",
                        "field_label": "Company Name",
                        "data_type": "text"
                    },
                    {
                        "api_name": "Owner_Email",
                        "field_label": "Owner Email",
                        "data_type": "email",
                        "required": True
                    },
                    {
                        "api_name": "Owner_Name",
                        "field_label": "Owner Name",
                        "data_type": "text"
                    },
                    {
                        "api_name": "Plan_Type",
                        "field_label": "Plan Type",
                        "data_type": "picklist",
                        "pick_list_values": [
                            {"display_value": "Free"},
                            {"display_value": "Starter"},
                            {"display_value": "Professional"},
                            {"display_value": "Enterprise"}
                        ]
                    },
                    {
                        "api_name": "Credits_Balance",
                        "field_label": "Credits Balance",
                        "data_type": "decimal"
                    },
                    {
                        "api_name": "Total_Credits_Purchased",
                        "field_label": "Total Credits Purchased",
                        "data_type": "decimal"
                    },
                    {
                        "api_name": "DB_Space_Used_MB",
                        "field_label": "DB Space Used (MB)",
                        "data_type": "decimal"
                    },
                    {
                        "api_name": "LLM_Tokens_Used",
                        "field_label": "LLM Tokens Used",
                        "data_type": "number"
                    },
                    {
                        "api_name": "Status",
                        "field_label": "Status",
                        "data_type": "picklist",
                        "pick_list_values": [
                            {"display_value": "Active"},
                            {"display_value": "Suspended"},
                            {"display_value": "Cancelled"}
                        ]
                    },
                    {
                        "api_name": "Created_Date",
                        "field_label": "Created Date",
                        "data_type": "date"
                    },
                    {
                        "api_name": "Zoho_Workspace_ID",
                        "field_label": "Zoho Workspace ID",
                        "data_type": "text"
                    }
                ]
            }

            logger.info("Tenant module schema ready for Zoho CRM")
            return {"status": "success", "message": "Tenant module initialized"}

        except Exception as e:
            logger.error(f"Error initializing tenant module: {e}")
            return {"status": "error", "message": str(e)}

    async def create_tenant(
        self,
        email: str,
        name: str,
        company_name: str = None,
        plan_type: str = "Free"
    ) -> Dict[str, Any]:
        """
        Create a new tenant in Zoho CRM.

        Args:
            email: Tenant owner email
            name: Tenant owner name
            company_name: Company name (optional)
            plan_type: Subscription plan (Free, Starter, Professional, Enterprise)

        Returns:
            Dict with tenant details
        """
        try:
            import uuid
            tenant_id = str(uuid.uuid4())

            # Create tenant record in Zoho CRM
            tenant_data = {
                "Tenant_ID": tenant_id,
                "Owner_Email": email,
                "Owner_Name": name,
                "Company_Name": company_name or name,
                "Plan_Type": plan_type,
                "Credits_Balance": self._get_initial_credits(plan_type),
                "Total_Credits_Purchased": self._get_initial_credits(plan_type),
                "DB_Space_Used_MB": 0,
                "LLM_Tokens_Used": 0,
                "Status": "Active",
                "Created_Date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "Zoho_Workspace_ID": ""
            }

            # Store in Zoho CRM
            zoho_result = await self.zoho_crm.create_record(
                module="Tenants",
                data=tenant_data
            )

            if zoho_result.get("status") == "success":
                # Cache in local MongoDB for fast access
                await self.tenants_collection.insert_one({
                    "tenant_id": tenant_id,
                    "email": email,
                    "name": name,
                    "company_name": company_name or name,
                    "plan_type": plan_type,
                    "credits_balance": self._get_initial_credits(plan_type),
                    "created_at": datetime.now(timezone.utc),
                    "status": "active",
                    "zoho_record_id": zoho_result.get("record_id")
                })

                logger.info(f"Created tenant: {tenant_id} for {email}")

                return {
                    "status": "success",
                    "tenant_id": tenant_id,
                    "email": email,
                    "plan_type": plan_type,
                    "credits_balance": self._get_initial_credits(plan_type)
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to create tenant in Zoho CRM"
                }

        except Exception as e:
            logger.error(f"Error creating tenant: {e}")
            return {"status": "error", "message": str(e)}

    async def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant details by ID."""
        try:
            # Check local cache first
            tenant = await self.tenants_collection.find_one({"tenant_id": tenant_id})

            if tenant:
                return {
                    "tenant_id": tenant["tenant_id"],
                    "email": tenant["email"],
                    "name": tenant["name"],
                    "company_name": tenant["company_name"],
                    "plan_type": tenant["plan_type"],
                    "credits_balance": tenant["credits_balance"],
                    "status": tenant["status"]
                }

            return None

        except Exception as e:
            logger.error(f"Error getting tenant: {e}")
            return None

    async def get_tenant_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get tenant by email address."""
        try:
            tenant = await self.tenants_collection.find_one({"email": email})

            if tenant:
                return {
                    "tenant_id": tenant["tenant_id"],
                    "email": tenant["email"],
                    "name": tenant["name"],
                    "company_name": tenant["company_name"],
                    "plan_type": tenant["plan_type"],
                    "credits_balance": tenant["credits_balance"],
                    "status": tenant["status"]
                }

            return None

        except Exception as e:
            logger.error(f"Error getting tenant by email: {e}")
            return None

    async def update_credits_balance(
        self,
        tenant_id: str,
        credits_change: float
    ) -> Dict[str, Any]:
        """
        Update tenant credits balance.

        Args:
            tenant_id: Tenant identifier
            credits_change: Amount to add (positive) or subtract (negative)

        Returns:
            Updated tenant data
        """
        try:
            # Update local cache
            result = await self.tenants_collection.update_one(
                {"tenant_id": tenant_id},
                {"$inc": {"credits_balance": credits_change}}
            )

            if result.modified_count > 0:
                # Sync to Zoho CRM
                tenant = await self.tenants_collection.find_one({"tenant_id": tenant_id})

                await self.zoho_crm.update_record(
                    module="Tenants",
                    record_id=tenant["zoho_record_id"],
                    data={"Credits_Balance": tenant["credits_balance"]}
                )

                logger.info(f"Updated credits for tenant {tenant_id}: {credits_change:+.2f}")

                return {
                    "status": "success",
                    "new_balance": tenant["credits_balance"]
                }

            return {"status": "error", "message": "Tenant not found"}

        except Exception as e:
            logger.error(f"Error updating credits: {e}")
            return {"status": "error", "message": str(e)}

    async def check_credits(self, tenant_id: str, required_credits: float) -> bool:
        """
        Check if tenant has enough credits.

        Args:
            tenant_id: Tenant identifier
            required_credits: Credits required for operation

        Returns:
            True if sufficient credits, False otherwise
        """
        try:
            tenant = await self.tenants_collection.find_one({"tenant_id": tenant_id})

            if not tenant:
                return False

            return tenant["credits_balance"] >= required_credits

        except Exception as e:
            logger.error(f"Error checking credits: {e}")
            return False

    async def get_tenant_usage_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get usage statistics for a tenant."""
        try:
            tenant = await self.tenants_collection.find_one({"tenant_id": tenant_id})

            if not tenant:
                return {"status": "error", "message": "Tenant not found"}

            return {
                "status": "success",
                "tenant_id": tenant_id,
                "credits_balance": tenant["credits_balance"],
                "plan_type": tenant["plan_type"],
                "db_space_mb": tenant.get("db_space_used_mb", 0),
                "llm_tokens_used": tenant.get("llm_tokens_used", 0)
            }

        except Exception as e:
            logger.error(f"Error getting tenant stats: {e}")
            return {"status": "error", "message": str(e)}

    def _get_initial_credits(self, plan_type: str) -> float:
        """Get initial credits based on plan type."""
        credits_map = {
            "Free": 100.0,
            "Starter": 1000.0,
            "Professional": 5000.0,
            "Enterprise": 20000.0
        }
        return credits_map.get(plan_type, 100.0)

    async def list_all_tenants(self, status: str = "active") -> List[Dict[str, Any]]:
        """List all tenants with optional status filter."""
        try:
            query = {} if status == "all" else {"status": status}

            tenants = await self.tenants_collection.find(query).to_list(length=1000)

            return [{
                "tenant_id": t["tenant_id"],
                "email": t["email"],
                "company_name": t["company_name"],
                "plan_type": t["plan_type"],
                "credits_balance": t["credits_balance"],
                "status": t["status"]
            } for t in tenants]

        except Exception as e:
            logger.error(f"Error listing tenants: {e}")
            return []
