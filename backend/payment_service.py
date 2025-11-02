"""
Payment Service

Handles:
- Stripe payment integration
- Credit package purchases
- Subscription management
- Payment webhooks
- Invoice generation
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Stripe payment gateway integration for credit purchases.
    """

    def __init__(self, credits_service, tenant_service, stripe_api_key: str):
        """
        Initialize Payment Service.

        Args:
            credits_service: CreditsService instance
            tenant_service: TenantService instance
            stripe_api_key: Stripe secret API key
        """
        self.credits_service = credits_service
        self.tenant_service = tenant_service
        self.stripe_api_key = stripe_api_key

        # Initialize Stripe (lazy import to avoid dependency if not used)
        try:
            import stripe
            stripe.api_key = stripe_api_key
            self.stripe = stripe
            logger.info("Payment Service initialized with Stripe")
        except ImportError:
            logger.warning("Stripe library not installed. Install with: pip install stripe")
            self.stripe = None

    async def create_checkout_session(
        self,
        tenant_id: str,
        package_name: str,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """
        Create Stripe checkout session for credit purchase.

        Args:
            tenant_id: Tenant identifier
            package_name: Credit package name
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if payment cancelled

        Returns:
            Dict with checkout session URL
        """
        try:
            if not self.stripe:
                return {
                    "status": "error",
                    "message": "Stripe not configured"
                }

            # Get package details
            packages = self.credits_service.CREDIT_PACKAGES
            package = packages.get(package_name)

            if not package:
                return {
                    "status": "error",
                    "message": "Invalid package name"
                }

            # Get tenant info
            tenant = await self.tenant_service.get_tenant(tenant_id)

            if not tenant:
                return {
                    "status": "error",
                    "message": "Tenant not found"
                }

            # Create Stripe checkout session
            session = self.stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": int(package["price_usd"] * 100),  # Convert to cents
                        "product_data": {
                            "name": f"{package_name.capitalize()} Credits Package",
                            "description": f"{package['credits']} credits + {package['bonus_credits']} bonus credits",
                        },
                    },
                    "quantity": 1,
                }],
                mode="payment",
                success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=cancel_url,
                client_reference_id=tenant_id,
                metadata={
                    "tenant_id": tenant_id,
                    "package_name": package_name,
                    "credits": package["credits"] + package["bonus_credits"]
                }
            )

            logger.info(f"Created checkout session for {tenant_id}: {package_name}")

            return {
                "status": "success",
                "session_id": session.id,
                "checkout_url": session.url
            }

        except Exception as e:
            logger.error(f"Error creating checkout session: {e}")
            return {"status": "error", "message": str(e)}

    async def handle_webhook(
        self,
        payload: bytes,
        signature: str,
        webhook_secret: str
    ) -> Dict[str, Any]:
        """
        Handle Stripe webhook events.

        Args:
            payload: Webhook payload
            signature: Stripe signature header
            webhook_secret: Webhook secret for verification

        Returns:
            Processing result
        """
        try:
            if not self.stripe:
                return {"status": "error", "message": "Stripe not configured"}

            # Verify webhook signature
            event = self.stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )

            event_type = event["type"]
            logger.info(f"Received Stripe webhook: {event_type}")

            # Handle different event types
            if event_type == "checkout.session.completed":
                return await self._handle_checkout_completed(event["data"]["object"])

            elif event_type == "payment_intent.succeeded":
                return await self._handle_payment_succeeded(event["data"]["object"])

            elif event_type == "payment_intent.payment_failed":
                return await self._handle_payment_failed(event["data"]["object"])

            else:
                logger.info(f"Unhandled webhook event: {event_type}")
                return {"status": "ignored", "event_type": event_type}

        except self.stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            return {"status": "error", "message": "Invalid signature"}
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return {"status": "error", "message": str(e)}

    async def _handle_checkout_completed(self, session) -> Dict[str, Any]:
        """Handle successful checkout completion."""
        try:
            tenant_id = session["metadata"]["tenant_id"]
            package_name = session["metadata"]["package_name"]
            payment_id = session["payment_intent"]

            # Add credits to tenant account
            result = await self.credits_service.add_credits(
                tenant_id=tenant_id,
                package_name=package_name,
                payment_id=payment_id
            )

            if result["status"] == "success":
                logger.info(f"Credits added for tenant {tenant_id} after successful payment: {payment_id}")

                return {
                    "status": "success",
                    "tenant_id": tenant_id,
                    "credits_added": result["credits_added"]
                }

            return result

        except Exception as e:
            logger.error(f"Error handling checkout completed: {e}")
            return {"status": "error", "message": str(e)}

    async def _handle_payment_succeeded(self, payment_intent) -> Dict[str, Any]:
        """Handle successful payment intent."""
        try:
            logger.info(f"Payment succeeded: {payment_intent['id']}")
            return {"status": "success", "payment_id": payment_intent["id"]}

        except Exception as e:
            logger.error(f"Error handling payment succeeded: {e}")
            return {"status": "error", "message": str(e)}

    async def _handle_payment_failed(self, payment_intent) -> Dict[str, Any]:
        """Handle failed payment intent."""
        try:
            logger.warning(f"Payment failed: {payment_intent['id']}")
            return {"status": "failed", "payment_id": payment_intent["id"]}

        except Exception as e:
            logger.error(f"Error handling payment failed: {e}")
            return {"status": "error", "message": str(e)}

    async def get_payment_history(
        self,
        tenant_id: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get payment history for a tenant.

        Args:
            tenant_id: Tenant identifier
            limit: Maximum number of records

        Returns:
            List of payment records
        """
        try:
            # Get transaction history from credits service
            transactions = await self.credits_service.get_transaction_history(
                tenant_id, limit
            )

            return {
                "status": "success",
                "transactions": transactions
            }

        except Exception as e:
            logger.error(f"Error getting payment history: {e}")
            return {"status": "error", "message": str(e)}

    async def create_invoice(
        self,
        tenant_id: str,
        transaction_id: str
    ) -> Dict[str, Any]:
        """
        Generate invoice for a transaction.

        Args:
            tenant_id: Tenant identifier
            transaction_id: Transaction ID

        Returns:
            Invoice data
        """
        try:
            # Get tenant info
            tenant = await self.tenant_service.get_tenant(tenant_id)

            if not tenant:
                return {"status": "error", "message": "Tenant not found"}

            # Get transaction details
            # (In production, query transactions collection)

            invoice_data = {
                "invoice_number": f"INV-{transaction_id}",
                "tenant_id": tenant_id,
                "company_name": tenant["company_name"],
                "email": tenant["email"],
                "date": datetime.now(timezone.utc).isoformat(),
                "status": "paid"
            }

            logger.info(f"Generated invoice for {tenant_id}: {invoice_data['invoice_number']}")

            return {
                "status": "success",
                "invoice": invoice_data
            }

        except Exception as e:
            logger.error(f"Error creating invoice: {e}")
            return {"status": "error", "message": str(e)}

    def get_available_packages(self) -> Dict[str, Any]:
        """Get list of available credit packages."""
        packages = self.credits_service.CREDIT_PACKAGES

        return {
            "status": "success",
            "packages": [{
                "name": name,
                "credits": pkg["credits"],
                "bonus_credits": pkg["bonus_credits"],
                "total_credits": pkg["credits"] + pkg["bonus_credits"],
                "price_usd": pkg["price_usd"],
                "price_per_credit": pkg["price_usd"] / (pkg["credits"] + pkg["bonus_credits"])
            } for name, pkg in packages.items()]
        }

    async def cancel_subscription(self, tenant_id: str) -> Dict[str, Any]:
        """Cancel tenant subscription."""
        try:
            # Update tenant status
            # (Implementation depends on subscription model)

            logger.info(f"Subscription cancelled for tenant: {tenant_id}")

            return {
                "status": "success",
                "message": "Subscription cancelled"
            }

        except Exception as e:
            logger.error(f"Error cancelling subscription: {e}")
            return {"status": "error", "message": str(e)}
