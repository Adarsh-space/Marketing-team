"""
User Authentication Service

Handles user authentication via Zoho:
- Login/Signup using Zoho CRM
- Session management
- JWT token generation
- Password hashing (stored in Zoho)
"""

import logging
import hashlib
import secrets
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import jwt

logger = logging.getLogger(__name__)


class AuthService:
    """
    User authentication using Zoho CRM as user database.
    """

    def __init__(self, zoho_crm_service, tenant_service, db, jwt_secret: str):
        """
        Initialize Auth Service.

        Args:
            zoho_crm_service: ZohoCRMService instance
            tenant_service: TenantService instance
            db: MongoDB database
            jwt_secret: Secret key for JWT signing
        """
        self.zoho_crm = zoho_crm_service
        self.tenant_service = tenant_service
        self.db = db
        self.users_collection = db.users
        self.sessions_collection = db.sessions
        self.jwt_secret = jwt_secret
        logger.info("Auth Service initialized")

    async def initialize_users_module(self):
        """
        Create custom Zoho module for users.
        """
        try:
            users_module = {
                "api_name": "App_Users",
                "module_name": "App Users",
                "fields": [
                    {
                        "api_name": "User_ID",
                        "field_label": "User ID",
                        "data_type": "text",
                        "unique": True
                    },
                    {
                        "api_name": "Email",
                        "field_label": "Email",
                        "data_type": "email",
                        "required": True,
                        "unique": True
                    },
                    {
                        "api_name": "Full_Name",
                        "field_label": "Full Name",
                        "data_type": "text"
                    },
                    {
                        "api_name": "Password_Hash",
                        "field_label": "Password Hash",
                        "data_type": "text"
                    },
                    {
                        "api_name": "Tenant_ID",
                        "field_label": "Tenant ID",
                        "data_type": "text"
                    },
                    {
                        "api_name": "Role",
                        "field_label": "Role",
                        "data_type": "picklist",
                        "pick_list_values": [
                            {"display_value": "Admin"},
                            {"display_value": "User"},
                            {"display_value": "Viewer"}
                        ]
                    },
                    {
                        "api_name": "Status",
                        "field_label": "Status",
                        "data_type": "picklist",
                        "pick_list_values": [
                            {"display_value": "Active"},
                            {"display_value": "Inactive"},
                            {"display_value": "Suspended"}
                        ]
                    }
                ]
            }

            logger.info("Users module schema ready")
            return {"status": "success"}

        except Exception as e:
            logger.error(f"Error initializing users module: {e}")
            return {"status": "error", "message": str(e)}

    async def signup(
        self,
        email: str,
        password: str,
        full_name: str,
        company_name: str = None
    ) -> Dict[str, Any]:
        """
        Register a new user and create tenant.

        Args:
            email: User email
            password: User password
            full_name: User's full name
            company_name: Company name (optional)

        Returns:
            Dict with user details and JWT token
        """
        try:
            # Check if user already exists
            existing_user = await self.users_collection.find_one({"email": email})
            if existing_user:
                return {
                    "status": "error",
                    "message": "User with this email already exists"
                }

            # Create tenant first
            tenant_result = await self.tenant_service.create_tenant(
                email=email,
                name=full_name,
                company_name=company_name,
                plan_type="Free"
            )

            if tenant_result["status"] != "success":
                return {
                    "status": "error",
                    "message": "Failed to create tenant"
                }

            tenant_id = tenant_result["tenant_id"]

            # Hash password
            password_hash = self._hash_password(password)

            # Generate user ID
            import uuid
            user_id = str(uuid.uuid4())

            # Create user in Zoho CRM
            user_data = {
                "User_ID": user_id,
                "Email": email,
                "Full_Name": full_name,
                "Password_Hash": password_hash,
                "Tenant_ID": tenant_id,
                "Role": "Admin",
                "Status": "Active"
            }

            zoho_result = await self.zoho_crm.create_record(
                module="App_Users",
                data=user_data
            )

            # Store in local MongoDB
            await self.users_collection.insert_one({
                "user_id": user_id,
                "email": email,
                "full_name": full_name,
                "password_hash": password_hash,
                "tenant_id": tenant_id,
                "role": "admin",
                "status": "active",
                "created_at": datetime.now(timezone.utc),
                "zoho_record_id": zoho_result.get("record_id") if zoho_result["status"] == "success" else None
            })

            # Generate JWT token
            token = self._generate_jwt_token(user_id, email, tenant_id)

            # Create session
            await self._create_session(user_id, token)

            logger.info(f"User signup successful: {email}")

            return {
                "status": "success",
                "user_id": user_id,
                "email": email,
                "tenant_id": tenant_id,
                "token": token,
                "full_name": full_name,
                "role": "admin"
            }

        except Exception as e:
            logger.error(f"Error during signup: {e}")
            return {"status": "error", "message": str(e)}

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user with email and password.

        Args:
            email: User email
            password: User password

        Returns:
            Dict with user details and JWT token
        """
        try:
            # Find user
            user = await self.users_collection.find_one({"email": email})

            if not user:
                return {
                    "status": "error",
                    "message": "Invalid email or password"
                }

            # Verify password
            if not self._verify_password(password, user["password_hash"]):
                return {
                    "status": "error",
                    "message": "Invalid email or password"
                }

            # Check if user is active
            if user["status"] != "active":
                return {
                    "status": "error",
                    "message": f"Account is {user['status']}"
                }

            # Generate new JWT token
            token = self._generate_jwt_token(
                user["user_id"],
                user["email"],
                user["tenant_id"]
            )

            # Create session
            await self._create_session(user["user_id"], token)

            logger.info(f"User login successful: {email}")

            return {
                "status": "success",
                "user_id": user["user_id"],
                "email": user["email"],
                "tenant_id": user["tenant_id"],
                "token": token,
                "full_name": user["full_name"],
                "role": user["role"]
            }

        except Exception as e:
            logger.error(f"Error during login: {e}")
            return {"status": "error", "message": str(e)}

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token and return user data.

        Args:
            token: JWT token

        Returns:
            User data if valid, None otherwise
        """
        try:
            # Decode JWT
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])

            user_id = payload.get("user_id")
            email = payload.get("email")
            tenant_id = payload.get("tenant_id")

            # Check if session exists
            session = await self.sessions_collection.find_one({
                "user_id": user_id,
                "token": token,
                "active": True
            })

            if not session:
                return None

            # Check if session expired
            if session["expires_at"] < datetime.now(timezone.utc):
                await self._deactivate_session(token)
                return None

            return {
                "user_id": user_id,
                "email": email,
                "tenant_id": tenant_id
            }

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None

    async def logout(self, token: str) -> Dict[str, Any]:
        """Deactivate user session."""
        try:
            await self._deactivate_session(token)

            return {
                "status": "success",
                "message": "Logged out successfully"
            }

        except Exception as e:
            logger.error(f"Error during logout: {e}")
            return {"status": "error", "message": str(e)}

    async def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str
    ) -> Dict[str, Any]:
        """Change user password."""
        try:
            user = await self.users_collection.find_one({"user_id": user_id})

            if not user:
                return {"status": "error", "message": "User not found"}

            # Verify old password
            if not self._verify_password(old_password, user["password_hash"]):
                return {"status": "error", "message": "Current password is incorrect"}

            # Hash new password
            new_hash = self._hash_password(new_password)

            # Update in MongoDB
            await self.users_collection.update_one(
                {"user_id": user_id},
                {"$set": {"password_hash": new_hash}}
            )

            # Update in Zoho CRM
            if user.get("zoho_record_id"):
                await self.zoho_crm.update_record(
                    module="App_Users",
                    record_id=user["zoho_record_id"],
                    data={"Password_Hash": new_hash}
                )

            logger.info(f"Password changed for user: {user_id}")

            return {
                "status": "success",
                "message": "Password changed successfully"
            }

        except Exception as e:
            logger.error(f"Error changing password: {e}")
            return {"status": "error", "message": str(e)}

    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt."""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}${pwd_hash}"

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash."""
        try:
            salt, pwd_hash = stored_hash.split("$")
            computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return computed_hash == pwd_hash
        except:
            return False

    def _generate_jwt_token(
        self,
        user_id: str,
        email: str,
        tenant_id: str
    ) -> str:
        """Generate JWT token."""
        payload = {
            "user_id": user_id,
            "email": email,
            "tenant_id": tenant_id,
            "exp": datetime.now(timezone.utc) + timedelta(days=30),
            "iat": datetime.now(timezone.utc)
        }

        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        return token

    async def _create_session(self, user_id: str, token: str):
        """Create user session."""
        await self.sessions_collection.insert_one({
            "user_id": user_id,
            "token": token,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
            "active": True
        })

    async def _deactivate_session(self, token: str):
        """Deactivate session."""
        await self.sessions_collection.update_one(
            {"token": token},
            {"$set": {"active": False}}
        )
