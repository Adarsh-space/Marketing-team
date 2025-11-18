"""
Test script to verify social media credentials are saved properly to both MongoDB and Zoho CRM.
This script simulates the OAuth flow and tests credential storage.
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from unified_social_service import UnifiedSocialService
from zoho_auth_service import ZohoAuthService
from zoho_crm_service import ZohoCRMService
from dotenv import load_dotenv
import os
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_credential_flow():
    """
    Test the credential saving flow for all social platforms.
    """
    logger.info("=" * 80)
    logger.info("Starting Social Media Credentials Test")
    logger.info("=" * 80)

    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    if "mongodb+srv://" in mongo_url:
        import certifi
        client = AsyncIOMotorClient(
            mongo_url,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=20000
        )
    else:
        client = AsyncIOMotorClient(mongo_url)

    db = client[os.environ['DB_NAME']]

    # Initialize Zoho services
    zoho_auth = ZohoAuthService(db)
    zoho_crm = ZohoCRMService(zoho_auth)

    # Initialize UnifiedSocialService with Zoho CRM
    unified_social = UnifiedSocialService(db, zoho_crm_service=zoho_crm)

    # Test user
    test_user_id = "test_user_123"

    logger.info("\n" + "=" * 80)
    logger.info("Test 1: Check Zoho CRM Integration Status")
    logger.info("=" * 80)

    if unified_social.zoho_crm_service:
        logger.info("✅ Zoho CRM service is properly initialized")
    else:
        logger.warning("❌ Zoho CRM service is NOT initialized")

    logger.info("\n" + "=" * 80)
    logger.info("Test 2: Verify Social Platform Configurations")
    logger.info("=" * 80)

    platforms = ["facebook", "instagram", "twitter", "linkedin"]

    for platform in platforms:
        config = unified_social.platforms.get(platform)
        if config:
            logger.info(f"\n{platform.upper()}:")

            # Check credentials
            if platform in ["facebook", "instagram"]:
                app_id = config.get("app_id")
                app_secret = config.get("app_secret")
                if app_id and app_secret:
                    logger.info(f"  ✅ Credentials configured (App ID: {app_id[:10]}...)")
                else:
                    logger.warning(f"  ❌ Credentials NOT configured")

            elif platform == "twitter":
                api_key = config.get("api_key")
                api_secret = config.get("api_secret")
                if api_key and api_secret:
                    logger.info(f"  ✅ Credentials configured (API Key: {api_key[:10]}...)")
                else:
                    logger.warning(f"  ❌ Credentials NOT configured")

            elif platform == "linkedin":
                client_id = config.get("client_id")
                client_secret = config.get("client_secret")
                if client_id and client_secret:
                    logger.info(f"  ✅ Credentials configured (Client ID: {client_id[:10]}...)")
                else:
                    logger.warning(f"  ❌ Credentials NOT configured")
        else:
            logger.warning(f"❌ {platform.upper()} configuration not found")

    logger.info("\n" + "=" * 80)
    logger.info("Test 3: Check MongoDB Collections")
    logger.info("=" * 80)

    required_collections = ["oauth_states", "social_accounts", "social_posts"]
    existing_collections = await db.list_collection_names()

    for collection in required_collections:
        if collection in existing_collections:
            logger.info(f"✅ Collection '{collection}' exists")
        else:
            logger.warning(f"❌ Collection '{collection}' NOT found")

    logger.info("\n" + "=" * 80)
    logger.info("Test 4: Check Existing Connected Accounts")
    logger.info("=" * 80)

    result = await unified_social.get_connected_accounts(user_id=test_user_id)

    if result.get("status") == "success":
        accounts = result.get("accounts", [])
        logger.info(f"Found {len(accounts)} connected account(s) for user '{test_user_id}'")

        for account in accounts:
            platform = account.get("platform", "unknown")
            account_name = account.get("account_name", "N/A")
            account_id = account.get("account_id", "N/A")
            status = account.get("status", "unknown")

            logger.info(f"\n  Platform: {platform.upper()}")
            logger.info(f"  Account Name: {account_name}")
            logger.info(f"  Account ID: {account_id}")
            logger.info(f"  Status: {status}")
    else:
        logger.warning(f"Failed to get accounts: {result.get('error')}")

    logger.info("\n" + "=" * 80)
    logger.info("Test 5: Verify Zoho CRM Credential Storage")
    logger.info("=" * 80)

    # Try to search for credentials in Zoho CRM
    try:
        zoho_result = await zoho_crm.search_records(
            module_name="Social_Media_Credentials",
            search_criteria=f"User_ID = '{test_user_id}'",
            user_id=test_user_id
        )

        if zoho_result.get("status") == "success":
            records = zoho_result.get("records", [])
            logger.info(f"✅ Found {len(records)} credential record(s) in Zoho CRM")

            for record in records:
                platform = record.get("Platform", "N/A")
                account_name = record.get("Account_Name", "N/A")
                status = record.get("Status", "N/A")
                connected_at = record.get("Connected_At", "N/A")

                logger.info(f"\n  Platform: {platform}")
                logger.info(f"  Account Name: {account_name}")
                logger.info(f"  Status: {status}")
                logger.info(f"  Connected At: {connected_at}")
        else:
            logger.warning(f"⚠️  Zoho CRM search returned: {zoho_result.get('message', 'Unknown status')}")
    except Exception as e:
        logger.error(f"❌ Error querying Zoho CRM: {str(e)}")

    logger.info("\n" + "=" * 80)
    logger.info("Test 6: OAuth URL Generation Test")
    logger.info("=" * 80)

    redirect_uri = "http://localhost:8000/api/social/callback/facebook"

    for platform in ["facebook", "instagram", "twitter", "linkedin"]:
        try:
            auth_result = await unified_social.get_auth_url(
                platform=platform,
                user_id=test_user_id,
                redirect_uri=redirect_uri
            )

            if auth_result.get("status") == "success":
                auth_url = auth_result.get("authorization_url", "")
                logger.info(f"✅ {platform.upper()}: OAuth URL generated ({len(auth_url)} chars)")
            else:
                error = auth_result.get("error", "Unknown error")
                logger.warning(f"⚠️  {platform.upper()}: {error}")
        except Exception as e:
            logger.error(f"❌ {platform.upper()}: {str(e)}")

    logger.info("\n" + "=" * 80)
    logger.info("Test Summary")
    logger.info("=" * 80)

    logger.info("\n✅ = Working correctly")
    logger.info("⚠️  = Warning (may need configuration)")
    logger.info("❌ = Error (needs attention)")

    logger.info("\nTo connect accounts, use the frontend or call:")
    logger.info("GET /api/social/connect/{platform}?user_id=your_user_id")
    logger.info("\nSupported platforms: facebook, instagram, twitter, linkedin")

    logger.info("\n" + "=" * 80)
    logger.info("Test Complete!")
    logger.info("=" * 80)

    # Close connection
    client.close()

if __name__ == "__main__":
    asyncio.run(test_credential_flow())
