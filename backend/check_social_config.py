#!/usr/bin/env python3
"""
Quick script to check if social media OAuth credentials are configured.
Run this to diagnose "Failed to get authorization URL" errors.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

print("=" * 80)
print("SOCIAL MEDIA OAUTH CONFIGURATION CHECK")
print("=" * 80)

# Check each platform
platforms = {
    "Facebook/Instagram": {
        "required": ["FACEBOOK_APP_ID", "FACEBOOK_APP_SECRET"],
        "note": "Instagram uses Facebook OAuth"
    },
    "Twitter": {
        "required": ["TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_BEARER_TOKEN"],
        "note": "All three credentials are required"
    },
    "LinkedIn": {
        "required": ["LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET"],
        "note": "OAuth 2.0 credentials"
    }
}

all_configured = True

for platform_name, config in platforms.items():
    print(f"\n{platform_name}:")
    print(f"  Note: {config['note']}")

    platform_ok = True
    for var_name in config["required"]:
        value = os.getenv(var_name, "")

        if value and value.strip():
            # Credential is set
            masked_value = value[:8] + "..." if len(value) > 8 else "***"
            print(f"  ✅ {var_name}: {masked_value}")
        else:
            # Credential is missing
            print(f"  ❌ {var_name}: NOT SET")
            platform_ok = False
            all_configured = False

    if platform_ok:
        print(f"  → Status: READY ✅")
    else:
        print(f"  → Status: NOT CONFIGURED ❌")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

if all_configured:
    print("✅ All social media platforms are properly configured!")
    print("\nYou can now connect social media accounts.")
    print("Test with: curl 'http://localhost:8000/api/social/connect/facebook?user_id=test_user'")
else:
    print("❌ Some platforms are not configured.")
    print("\nTO FIX:")
    print("1. Register OAuth apps for each platform (see SOCIAL_MEDIA_SETUP_GUIDE.md)")
    print("2. Add credentials to backend/.env file")
    print("3. Restart the backend server")
    print("\nOR for development/testing:")
    print("- Use the mock endpoint (see guide for instructions)")

print("\n" + "=" * 80)
print("CONFIGURATION FILE LOCATION")
print("=" * 80)
print(f"File: {ROOT_DIR / '.env'}")
print("\nCurrent values in .env:")
print("-" * 80)

for platform_name, config in platforms.items():
    for var_name in config["required"]:
        value = os.getenv(var_name, "")
        status = "SET" if value and value.strip() else "EMPTY"
        print(f"{var_name}={repr(value)}  # {status}")

print("=" * 80)
