"""
Credits and Usage Tracking Service

Handles:
- Credit management and billing
- Usage tracking (LLM tokens, DB space, features)
- Cost calculation
- Low credits alerts
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class CreditsService:
    """
    Credits management and usage tracking service.
    """

    # Pricing configuration (credits per unit)
    PRICING = {
        "llm_tokens": {
            "per_1k_tokens": 0.01  # 0.01 credits per 1000 tokens
        },
        "db_storage": {
            "per_mb_per_month": 0.001  # 0.001 credits per MB per month
        },
        "social_post": {
            "per_post": 0.1  # 0.1 credits per post
        },
        "social_schedule": {
            "per_scheduled_post": 0.15  # 0.15 credits per scheduled post
        },
        "email_campaign": {
            "per_email": 0.02  # 0.02 credits per email sent
        },
        "data_scraping": {
            "google_maps_per_record": 0.05,  # 0.05 credits per record
            "linkedin_per_profile": 0.10,  # 0.10 credits per profile
            "website_per_page": 0.03  # 0.03 credits per page
        },
        "analytics_report": {
            "per_report": 0.05  # 0.05 credits per analytics report
        }
    }

    # Credit packages for purchase
    CREDIT_PACKAGES = {
        "starter": {
            "credits": 1000,
            "price_usd": 10.00,
            "bonus_credits": 0
        },
        "professional": {
            "credits": 5000,
            "price_usd": 45.00,
            "bonus_credits": 500  # 10% bonus
        },
        "enterprise": {
            "credits": 20000,
            "price_usd": 180.00,
            "bonus_credits": 4000  # 20% bonus
        }
    }

    def __init__(self, tenant_service, db):
        """
        Initialize Credits Service.

        Args:
            tenant_service: TenantService instance
            db: MongoDB database
        """
        self.tenant_service = tenant_service
        self.db = db
        self.usage_collection = db.usage_tracking
        self.transactions_collection = db.credit_transactions
        logger.info("Credits Service initialized")

    async def track_llm_usage(
        self,
        tenant_id: str,
        tokens_used: int,
        model: str,
        operation: str
    ) -> Dict[str, Any]:
        """
        Track LLM API usage and deduct credits.

        Args:
            tenant_id: Tenant identifier
            tokens_used: Number of tokens consumed
            model: LLM model used
            operation: Operation description

        Returns:
            Dict with usage details and remaining credits
        """
        try:
            # Calculate credits cost
            credits_cost = (tokens_used / 1000) * self.PRICING["llm_tokens"]["per_1k_tokens"]

            # Check if tenant has enough credits
            has_credits = await self.tenant_service.check_credits(tenant_id, credits_cost)

            if not has_credits:
                return {
                    "status": "error",
                    "message": "Insufficient credits",
                    "credits_required": credits_cost
                }

            # Deduct credits
            await self.tenant_service.update_credits_balance(tenant_id, -credits_cost)

            # Log usage
            await self.usage_collection.insert_one({
                "tenant_id": tenant_id,
                "type": "llm_usage",
                "tokens_used": tokens_used,
                "model": model,
                "operation": operation,
                "credits_cost": credits_cost,
                "timestamp": datetime.now(timezone.utc)
            })

            logger.info(f"LLM usage tracked for {tenant_id}: {tokens_used} tokens, {credits_cost:.4f} credits")

            return {
                "status": "success",
                "tokens_used": tokens_used,
                "credits_cost": credits_cost
            }

        except Exception as e:
            logger.error(f"Error tracking LLM usage: {e}")
            return {"status": "error", "message": str(e)}

    async def track_social_post(
        self,
        tenant_id: str,
        platform: str,
        is_scheduled: bool = False
    ) -> Dict[str, Any]:
        """
        Track social media post and deduct credits.

        Args:
            tenant_id: Tenant identifier
            platform: Social media platform
            is_scheduled: Whether post is scheduled

        Returns:
            Usage tracking result
        """
        try:
            # Calculate credits cost
            if is_scheduled:
                credits_cost = self.PRICING["social_schedule"]["per_scheduled_post"]
                post_type = "scheduled_post"
            else:
                credits_cost = self.PRICING["social_post"]["per_post"]
                post_type = "instant_post"

            # Check credits
            has_credits = await self.tenant_service.check_credits(tenant_id, credits_cost)

            if not has_credits:
                return {
                    "status": "error",
                    "message": "Insufficient credits",
                    "credits_required": credits_cost
                }

            # Deduct credits
            await self.tenant_service.update_credits_balance(tenant_id, -credits_cost)

            # Log usage
            await self.usage_collection.insert_one({
                "tenant_id": tenant_id,
                "type": post_type,
                "platform": platform,
                "credits_cost": credits_cost,
                "timestamp": datetime.now(timezone.utc)
            })

            logger.info(f"Social post tracked for {tenant_id}: {platform}, {credits_cost:.4f} credits")

            return {
                "status": "success",
                "credits_cost": credits_cost
            }

        except Exception as e:
            logger.error(f"Error tracking social post: {e}")
            return {"status": "error", "message": str(e)}

    async def track_email_campaign(
        self,
        tenant_id: str,
        emails_sent: int
    ) -> Dict[str, Any]:
        """Track email campaign usage."""
        try:
            credits_cost = emails_sent * self.PRICING["email_campaign"]["per_email"]

            has_credits = await self.tenant_service.check_credits(tenant_id, credits_cost)

            if not has_credits:
                return {
                    "status": "error",
                    "message": "Insufficient credits",
                    "credits_required": credits_cost
                }

            await self.tenant_service.update_credits_balance(tenant_id, -credits_cost)

            await self.usage_collection.insert_one({
                "tenant_id": tenant_id,
                "type": "email_campaign",
                "emails_sent": emails_sent,
                "credits_cost": credits_cost,
                "timestamp": datetime.now(timezone.utc)
            })

            logger.info(f"Email campaign tracked for {tenant_id}: {emails_sent} emails, {credits_cost:.4f} credits")

            return {
                "status": "success",
                "emails_sent": emails_sent,
                "credits_cost": credits_cost
            }

        except Exception as e:
            logger.error(f"Error tracking email campaign: {e}")
            return {"status": "error", "message": str(e)}

    async def track_data_scraping(
        self,
        tenant_id: str,
        scraping_type: str,
        records_scraped: int
    ) -> Dict[str, Any]:
        """
        Track data scraping usage.

        Args:
            tenant_id: Tenant identifier
            scraping_type: Type (google_maps, linkedin, website)
            records_scraped: Number of records scraped

        Returns:
            Usage tracking result
        """
        try:
            # Get pricing based on scraping type
            pricing_key = f"{scraping_type}_per_record" if scraping_type == "google_maps" else \
                          f"{scraping_type}_per_profile" if scraping_type == "linkedin" else \
                          f"{scraping_type}_per_page"

            credits_per_record = self.PRICING["data_scraping"].get(pricing_key, 0.05)
            credits_cost = records_scraped * credits_per_record

            has_credits = await self.tenant_service.check_credits(tenant_id, credits_cost)

            if not has_credits:
                return {
                    "status": "error",
                    "message": "Insufficient credits",
                    "credits_required": credits_cost
                }

            await self.tenant_service.update_credits_balance(tenant_id, -credits_cost)

            await self.usage_collection.insert_one({
                "tenant_id": tenant_id,
                "type": "data_scraping",
                "scraping_type": scraping_type,
                "records_scraped": records_scraped,
                "credits_cost": credits_cost,
                "timestamp": datetime.now(timezone.utc)
            })

            logger.info(f"Data scraping tracked for {tenant_id}: {scraping_type}, {records_scraped} records, {credits_cost:.4f} credits")

            return {
                "status": "success",
                "records_scraped": records_scraped,
                "credits_cost": credits_cost
            }

        except Exception as e:
            logger.error(f"Error tracking data scraping: {e}")
            return {"status": "error", "message": str(e)}

    async def add_credits(
        self,
        tenant_id: str,
        package_name: str,
        payment_id: str = None
    ) -> Dict[str, Any]:
        """
        Add credits to tenant account (after successful payment).

        Args:
            tenant_id: Tenant identifier
            package_name: Credit package name
            payment_id: Payment transaction ID

        Returns:
            Result with new balance
        """
        try:
            package = self.CREDIT_PACKAGES.get(package_name)

            if not package:
                return {
                    "status": "error",
                    "message": "Invalid package name"
                }

            total_credits = package["credits"] + package["bonus_credits"]

            # Add credits to tenant
            result = await self.tenant_service.update_credits_balance(tenant_id, total_credits)

            if result["status"] == "success":
                # Log transaction
                await self.transactions_collection.insert_one({
                    "tenant_id": tenant_id,
                    "type": "purchase",
                    "package": package_name,
                    "credits_added": total_credits,
                    "base_credits": package["credits"],
                    "bonus_credits": package["bonus_credits"],
                    "amount_usd": package["price_usd"],
                    "payment_id": payment_id,
                    "timestamp": datetime.now(timezone.utc)
                })

                logger.info(f"Credits added for {tenant_id}: {total_credits} credits from {package_name} package")

                return {
                    "status": "success",
                    "credits_added": total_credits,
                    "new_balance": result["new_balance"]
                }

            return result

        except Exception as e:
            logger.error(f"Error adding credits: {e}")
            return {"status": "error", "message": str(e)}

    async def get_usage_summary(
        self,
        tenant_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get usage summary for a tenant.

        Args:
            tenant_id: Tenant identifier
            days: Number of days to look back

        Returns:
            Usage summary
        """
        try:
            from datetime import timedelta

            start_date = datetime.now(timezone.utc) - timedelta(days=days)

            # Aggregate usage
            pipeline = [
                {
                    "$match": {
                        "tenant_id": tenant_id,
                        "timestamp": {"$gte": start_date}
                    }
                },
                {
                    "$group": {
                        "_id": "$type",
                        "total_credits": {"$sum": "$credits_cost"},
                        "count": {"$sum": 1}
                    }
                }
            ]

            usage_data = await self.usage_collection.aggregate(pipeline).to_list(length=100)

            # Get tenant stats
            tenant_stats = await self.tenant_service.get_tenant_usage_stats(tenant_id)

            summary = {
                "tenant_id": tenant_id,
                "period_days": days,
                "credits_balance": tenant_stats.get("credits_balance", 0),
                "plan_type": tenant_stats.get("plan_type", "Free"),
                "usage_by_type": {}
            }

            total_spent = 0
            for item in usage_data:
                usage_type = item["_id"]
                summary["usage_by_type"][usage_type] = {
                    "credits_spent": round(item["total_credits"], 4),
                    "count": item["count"]
                }
                total_spent += item["total_credits"]

            summary["total_credits_spent"] = round(total_spent, 4)

            return {
                "status": "success",
                "summary": summary
            }

        except Exception as e:
            logger.error(f"Error getting usage summary: {e}")
            return {"status": "error", "message": str(e)}

    async def get_transaction_history(
        self,
        tenant_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get credit transaction history."""
        try:
            transactions = await self.transactions_collection.find(
                {"tenant_id": tenant_id}
            ).sort("timestamp", -1).limit(limit).to_list(length=limit)

            return [{
                "type": t["type"],
                "package": t.get("package"),
                "credits_added": t.get("credits_added"),
                "amount_usd": t.get("amount_usd"),
                "timestamp": t["timestamp"].isoformat()
            } for t in transactions]

        except Exception as e:
            logger.error(f"Error getting transaction history: {e}")
            return []

    async def check_low_credits_alert(self, tenant_id: str) -> Dict[str, Any]:
        """Check if tenant has low credits and send alert."""
        try:
            tenant_stats = await self.tenant_service.get_tenant_usage_stats(tenant_id)
            credits_balance = tenant_stats.get("credits_balance", 0)

            # Alert thresholds
            low_credits_threshold = 100
            critical_credits_threshold = 10

            if credits_balance < critical_credits_threshold:
                return {
                    "status": "critical",
                    "message": f"Critical: Only {credits_balance:.2f} credits remaining!",
                    "credits_balance": credits_balance
                }
            elif credits_balance < low_credits_threshold:
                return {
                    "status": "warning",
                    "message": f"Warning: Low credits ({credits_balance:.2f})",
                    "credits_balance": credits_balance
                }

            return {
                "status": "ok",
                "credits_balance": credits_balance
            }

        except Exception as e:
            logger.error(f"Error checking credits alert: {e}")
            return {"status": "error", "message": str(e)}

    def get_pricing_info(self) -> Dict[str, Any]:
        """Get pricing information."""
        return {
            "pricing": self.PRICING,
            "packages": self.CREDIT_PACKAGES
        }
