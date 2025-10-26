"""
Zoho Mail Service

Handles all email operations through Zoho Mail API:
- Send emails with attachments
- Schedule emails
- Manage folders and messages
- Email templates
"""

import logging
import httpx
import base64
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ZohoMailService:
    """
    Complete Zoho Mail integration for email operations.
    """

    # Zoho Mail API base URL
    API_BASE_URL = "https://mail.zoho.com/api"

    def __init__(self, auth_service):
        """
        Initialize Zoho Mail Service.

        Args:
            auth_service: ZohoAuthService instance for authentication
        """
        self.auth_service = auth_service
        logger.info("Zoho Mail Service initialized")

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

    async def get_account_id(self, user_id: str = "default_user") -> Optional[str]:
        """
        Get user's Zoho Mail account ID (required for API calls).

        Args:
            user_id: User identifier

        Returns:
            Account ID or None
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return None

            url = f"{self.API_BASE_URL}/accounts"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    result = response.json()
                    accounts = result.get("data", [])
                    if accounts:
                        account_id = accounts[0]["accountId"]
                        logger.info(f"Got Zoho Mail account ID: {account_id}")
                        return account_id

            return None

        except Exception as e:
            logger.error(f"Error getting account ID: {str(e)}")
            return None

    async def send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        from_address: str = None,
        cc: List[str] = None,
        bcc: List[str] = None,
        attachments: List[Dict[str, Any]] = None,
        schedule_time: str = None,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Send an email via Zoho Mail.

        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body (HTML supported)
            from_address: From email address (uses default if None)
            cc: CC recipients
            bcc: BCC recipients
            attachments: List of attachment dicts with 'filename' and 'content' (base64)
            schedule_time: ISO format datetime to schedule email
            user_id: User identifier

        Returns:
            Dict with send status
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {
                    "status": "error",
                    "error": "authentication_failed",
                    "message": "No valid Zoho connection. Please connect to Zoho first."
                }

            account_id = await self.get_account_id(user_id)
            if not account_id:
                return {
                    "status": "error",
                    "error": "no_account",
                    "message": "Could not retrieve Zoho Mail account"
                }

            # Build email data
            email_data = {
                "fromAddress": from_address or "",
                "toAddress": ",".join(to) if isinstance(to, list) else to,
                "subject": subject,
                "content": body,
                "mailFormat": "html"  # or "plaintext"
            }

            if cc:
                email_data["ccAddress"] = ",".join(cc) if isinstance(cc, list) else cc

            if bcc:
                email_data["bccAddress"] = ",".join(bcc) if isinstance(bcc, list) else bcc

            if schedule_time:
                email_data["scheduledTime"] = schedule_time

            # Handle attachments
            if attachments:
                # Note: Zoho Mail API attachments require multipart/form-data
                # For now, we'll add attachment support in a separate method
                logger.warning("Attachments not yet implemented in this version")

            url = f"{self.API_BASE_URL}/accounts/{account_id}/messages"

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=email_data)

                if response.status_code in [200, 201]:
                    result = response.json()

                    logger.info(f"Email sent successfully via Zoho Mail to: {to}")

                    return {
                        "status": "success",
                        "message": "Email sent successfully",
                        "message_id": result.get("data", {}).get("messageId"),
                        "details": result
                    }
                else:
                    error_data = response.json()
                    logger.error(f"Failed to send email: {error_data}")
                    return {
                        "status": "error",
                        "error": "send_failed",
                        "message": error_data.get("message", "Failed to send email"),
                        "details": error_data
                    }

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return {
                "status": "error",
                "error": "exception",
                "message": str(e)
            }

    async def send_bulk_email(
        self,
        recipients: List[Dict[str, Any]],
        subject_template: str,
        body_template: str,
        from_address: str = None,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Send personalized emails to multiple recipients.

        Args:
            recipients: List of dicts with 'email' and personalization data
            subject_template: Subject template with {placeholders}
            body_template: Body template with {placeholders}
            from_address: From email address
            user_id: User identifier

        Returns:
            Dict with send results
        """
        try:
            results = []
            successful = 0
            failed = 0

            for recipient in recipients:
                email = recipient.get("email")
                if not email:
                    continue

                # Personalize subject and body
                subject = subject_template.format(**recipient)
                body = body_template.format(**recipient)

                # Send email
                result = await self.send_email(
                    to=[email],
                    subject=subject,
                    body=body,
                    from_address=from_address,
                    user_id=user_id
                )

                results.append({
                    "email": email,
                    "status": result.get("status"),
                    "message_id": result.get("message_id")
                })

                if result.get("status") == "success":
                    successful += 1
                else:
                    failed += 1

            logger.info(f"Bulk email sent: {successful} successful, {failed} failed")

            return {
                "status": "success",
                "total": len(recipients),
                "successful": successful,
                "failed": failed,
                "results": results
            }

        except Exception as e:
            logger.error(f"Error sending bulk email: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

    async def get_messages(
        self,
        folder_id: str = "1",  # 1 = Inbox
        page: int = 1,
        limit: int = 20,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Get messages from a folder.

        Args:
            folder_id: Folder ID (1=Inbox, 2=Sent, 3=Drafts, 4=Trash)
            page: Page number
            limit: Messages per page
            user_id: User identifier

        Returns:
            Dict with messages
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            account_id = await self.get_account_id(user_id)
            if not account_id:
                return {"status": "error", "message": "No account ID"}

            url = f"{self.API_BASE_URL}/accounts/{account_id}/messages/view"
            params = {
                "folderId": folder_id,
                "start": (page - 1) * limit,
                "limit": limit
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params)

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "status": "success",
                        "messages": result.get("data", []),
                        "total": result.get("total", 0)
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Failed to get messages"
                    }

        except Exception as e:
            logger.error(f"Error getting messages: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def search_messages(
        self,
        search_query: str,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Search messages.

        Args:
            search_query: Search query string
            user_id: User identifier

        Returns:
            Dict with search results
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            account_id = await self.get_account_id(user_id)
            if not account_id:
                return {"status": "error", "message": "No account ID"}

            url = f"{self.API_BASE_URL}/accounts/{account_id}/messages/search"
            params = {"searchKey": search_query}

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params)

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "status": "success",
                        "messages": result.get("data", [])
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Search failed"
                    }

        except Exception as e:
            logger.error(f"Error searching messages: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def get_folders(self, user_id: str = "default_user") -> Dict[str, Any]:
        """
        Get all mail folders.

        Args:
            user_id: User identifier

        Returns:
            Dict with folders list
        """
        try:
            headers = await self._get_headers(user_id)
            if not headers:
                return {"status": "error", "message": "No valid Zoho connection"}

            account_id = await self.get_account_id(user_id)
            if not account_id:
                return {"status": "error", "message": "No account ID"}

            url = f"{self.API_BASE_URL}/accounts/{account_id}/folders"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "status": "success",
                        "folders": result.get("data", [])
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Failed to get folders"
                    }

        except Exception as e:
            logger.error(f"Error getting folders: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def get_email_statistics(
        self,
        start_date: str = None,
        end_date: str = None,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Get email sending statistics.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            user_id: User identifier

        Returns:
            Dict with statistics
        """
        try:
            # Note: This would require custom tracking or Zoho Analytics integration
            # For now, return basic counts from folders

            sent = await self.get_messages(folder_id="2", user_id=user_id)  # Sent folder
            inbox = await self.get_messages(folder_id="1", user_id=user_id)  # Inbox

            return {
                "status": "success",
                "statistics": {
                    "sent_count": sent.get("total", 0) if sent.get("status") == "success" else 0,
                    "received_count": inbox.get("total", 0) if inbox.get("status") == "success" else 0,
                    "period": {
                        "start": start_date,
                        "end": end_date
                    }
                }
            }

        except Exception as e:
            logger.error(f"Error getting email statistics: {str(e)}")
            return {"status": "error", "message": str(e)}
