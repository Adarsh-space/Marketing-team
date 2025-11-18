# Social Media OAuth Setup Guide

## Current Issue
**Error:** "Failed to get facebook authorization URL" (and same for all platforms)

**Root Cause:** Social media API credentials are not configured in `.env` file.

## Required Environment Variables

Your `.env` file currently has empty values:
```env
FACEBOOK_APP_ID=""
FACEBOOK_APP_SECRET=""
TWITTER_API_KEY=""
TWITTER_API_SECRET=""
TWITTER_BEARER_TOKEN=""
LINKEDIN_CLIENT_ID=""
LINKEDIN_CLIENT_SECRET=""
```

---

## Setup Instructions

### 1️⃣ Facebook & Instagram OAuth Setup

Facebook and Instagram share the same OAuth app (Instagram uses Facebook Graph API).

#### Steps:

1. **Go to:** https://developers.facebook.com/
2. **Create an App:**
   - Click "Create App"
   - Select "Business" type
   - Fill in app details
3. **Add Products:**
   - Add "Facebook Login"
   - Add "Instagram Basic Display" (or "Instagram Graph API" for business accounts)
4. **Configure OAuth Settings:**
   - Go to "Facebook Login" → "Settings"
   - Add **Valid OAuth Redirect URIs:**
     ```
     http://localhost:8000/api/social/callback/facebook
     http://localhost:8000/api/social/callback/instagram
     https://your-production-domain.com/api/social/callback/facebook
     https://your-production-domain.com/api/social/callback/instagram
     ```
5. **Get Credentials:**
   - Go to "Settings" → "Basic"
   - Copy **App ID** and **App Secret**
6. **Update `.env`:**
   ```env
   FACEBOOK_APP_ID="your_app_id_here"
   FACEBOOK_APP_SECRET="your_app_secret_here"
   ```

#### Required Permissions:
- `pages_manage_posts`
- `pages_read_engagement`
- `pages_show_list`
- `instagram_basic`
- `instagram_content_publish`
- `public_profile`

---

### 2️⃣ Twitter OAuth Setup

#### Steps:

1. **Go to:** https://developer.twitter.com/en/portal/dashboard
2. **Create a Project & App:**
   - Create a new project
   - Create an app under that project
3. **Enable OAuth 2.0:**
   - Go to your app settings
   - Under "User authentication settings", click "Set up"
   - Select **OAuth 2.0**
   - Set "Type of App" to **Web App**
4. **Configure Callback URLs:**
   - Add Redirect URI:
     ```
     http://localhost:8000/api/social/callback/twitter
     https://your-production-domain.com/api/social/callback/twitter
     ```
   - Website URL: `http://localhost:8000` (or your domain)
5. **Get Credentials:**
   - Copy **API Key** (Client ID)
   - Copy **API Secret** (Client Secret)
   - Copy **Bearer Token** (from "Keys and tokens" tab)
6. **Update `.env`:**
   ```env
   TWITTER_API_KEY="your_api_key_here"
   TWITTER_API_SECRET="your_api_secret_here"
   TWITTER_BEARER_TOKEN="your_bearer_token_here"
   ```

#### Required Scopes:
- `tweet.read`
- `tweet.write`
- `users.read`
- `offline.access`

---

### 3️⃣ LinkedIn OAuth Setup

#### Steps:

1. **Go to:** https://www.linkedin.com/developers/apps
2. **Create an App:**
   - Click "Create app"
   - Fill in required details
   - Verify your app
3. **Add Products:**
   - Request access to "Sign In with LinkedIn"
   - Request access to "Share on LinkedIn"
4. **Configure OAuth Settings:**
   - Go to "Auth" tab
   - Add **Authorized Redirect URLs:**
     ```
     http://localhost:8000/api/social/callback/linkedin
     https://your-production-domain.com/api/social/callback/linkedin
     ```
5. **Get Credentials:**
   - On "Auth" tab, copy:
     - **Client ID**
     - **Client Secret**
6. **Update `.env`:**
   ```env
   LINKEDIN_CLIENT_ID="your_client_id_here"
   LINKEDIN_CLIENT_SECRET="your_client_secret_here"
   ```

#### Required Scopes:
- `w_member_social` (Share on LinkedIn)
- `r_liteprofile` (Read profile)
- `r_emailaddress` (Read email)

---

## Quick Start for Development/Testing

If you want to test the system without setting up real OAuth apps, you can:

### Option 1: Use Mock/Test Mode

Create a test endpoint that bypasses OAuth (for development only):

```python
# In server.py - DEVELOPMENT ONLY
@api_router.post("/social/connect/mock/{platform}")
async def mock_connect_social(platform: str, user_id: str = "test_user"):
    """
    Mock social connection for testing (DEVELOPMENT ONLY)
    """
    mock_account = {
        "user_id": user_id,
        "platform": platform,
        "account_id": f"{platform[:2]}_{uuid.uuid4().hex[:8]}",
        "account_name": f"Test {platform.title()} Account",
        "account_username": f"test_{platform}_user",
        "status": "active",
        "auth_type": "mock",
        "credentials": {
            "access_token": f"mock_token_{uuid.uuid4().hex}",
            "mock": True
        },
        "connected_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    await db.social_accounts.update_one(
        {"user_id": user_id, "account_id": mock_account["account_id"]},
        {"$set": mock_account},
        upsert=True
    )

    return {"status": "success", "account": mock_account}
```

### Option 2: Skip Credential Validation (Temporary)

Modify the validation in `unified_social_service.py` to allow empty credentials:

```python
# TEMPORARY - for development/testing only
# Comment out lines 86-104 in unified_social_service.py
```

⚠️ **WARNING:** Do not use these options in production!

---

## After Configuration

Once you've updated the `.env` file:

1. **Restart the backend server:**
   ```bash
   # Stop the current server
   # Restart it to load new environment variables
   ```

2. **Test the connection:**
   ```bash
   curl "http://localhost:8000/api/social/connect/facebook?user_id=test_user"
   ```

3. **You should get a response like:**
   ```json
   {
     "status": "success",
     "authorization_url": "https://www.facebook.com/v18.0/dialog/oauth?...",
     "state": "...",
     "platform": "facebook"
   }
   ```

---

## Troubleshooting

### Error: "Credentials not configured"
- Check that `.env` file has non-empty values
- Restart the backend server after updating `.env`
- Verify environment variables are loaded: `echo $FACEBOOK_APP_ID`

### Error: "Invalid redirect URI"
- Make sure redirect URIs in developer portal match exactly:
  - `http://localhost:8000/api/social/callback/{platform}`
- Include the protocol (`http://` or `https://`)
- No trailing slashes

### Error: "Invalid client credentials"
- Double-check App ID/Secret from developer portal
- Make sure there are no extra spaces in `.env` file
- Regenerate credentials if needed

### Error: "App not approved"
- Some platforms require app review before going live
- Use test accounts during development
- Submit for review when ready for production

---

## Production Checklist

Before deploying to production:

- [ ] Replace `localhost` URLs with production domain
- [ ] Enable HTTPS for all redirect URIs
- [ ] Store credentials securely (use secret management service)
- [ ] Complete app review process for each platform
- [ ] Set up proper error handling and logging
- [ ] Configure rate limiting
- [ ] Add token refresh logic for expired tokens
- [ ] Test with real user accounts
- [ ] Monitor Zoho CRM integration

---

## Need Help?

If you encounter issues:

1. Check backend logs for detailed error messages
2. Verify credentials in developer portals
3. Test OAuth URLs manually
4. Check network/firewall settings
5. Review platform-specific documentation:
   - Facebook: https://developers.facebook.com/docs/facebook-login
   - Twitter: https://developer.twitter.com/en/docs/authentication/oauth-2-0
   - LinkedIn: https://docs.microsoft.com/en-us/linkedin/shared/authentication/authentication

---

**Last Updated:** 2025-11-18
**Status:** Configuration Required ⚠️
