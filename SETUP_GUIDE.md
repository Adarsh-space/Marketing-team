# Complete Setup Guide - Marketing Minds AI Platform

## 🎯 Quick Start Checklist

- [ ] Get Zoho OAuth credentials
- [ ] Set up MongoDB database
- [ ] Get OpenAI API key
- [ ] Update `.env` file
- [ ] Configure Zoho Developer Console
- [ ] Test the setup

---

## Step 1: Get Zoho OAuth Credentials (India)

### 1.1 Access Zoho API Console (India)
👉 Go to: **https://api-console.zoho.in/** (India data center)

### 1.2 Create OAuth Application
1. Click **"Add Client"** or **"Get Started"**
2. Choose **"Server-based Applications"**
3. Fill in the details:
   - **Client Name**: Marketing Minds AI Platform
   - **Homepage URL**: `https://marketing-minds.preview.emergentagent.com`
   - **Authorized Redirect URIs**:
     ```
     https://marketing-minds.preview.emergentagent.com/api/zoho/callback
     ```
     ⚠️ **CRITICAL**: Must include `/api` prefix!

4. Click **"Create"**

### 1.3 Copy Your Credentials
After creating the app, you'll see:
- **Client ID** (looks like: `1000.XXXXXXXXXXXXX`)
- **Client Secret** (long string)

📋 **Copy these and paste them in `backend/.env`**:
```bash
ZOHO_CLIENT_ID=1000.XXXXXXXXXXXXX  # Your actual Client ID
ZOHO_CLIENT_SECRET=your_secret_here  # Your actual Client Secret
```

### 1.4 Configure Scopes
In the Zoho API Console, under "Scopes", ensure these are enabled:
- ✅ ZohoCRM.modules.ALL
- ✅ ZohoCRM.settings.ALL
- ✅ ZohoCRM.users.ALL
- ✅ ZohoMail.messages.ALL
- ✅ ZohoMail.accounts.ALL
- ✅ ZohoCampaigns.campaign.ALL
- ✅ ZohoCampaigns.contact.ALL

---

## Step 2: Set Up MongoDB

### Option A: MongoDB Atlas (Recommended - Free Tier Available)

1. **Create Account**
   - Go to: https://www.mongodb.com/cloud/atlas/register
   - Sign up for free

2. **Create Cluster**
   - Click **"Build a Database"**
   - Choose **"M0 Free"** tier
   - Select region closest to you (India recommended)
   - Click **"Create Cluster"**

3. **Create Database User**
   - Go to **Database Access** → **Add New Database User**
   - Username: `marketing_minds_user`
   - Password: Generate a strong password (save it!)
   - User Privileges: **Read and write to any database**
   - Click **"Add User"**

4. **Whitelist IP Address**
   - Go to **Network Access** → **Add IP Address**
   - For development: Click **"Allow Access from Anywhere"** (0.0.0.0/0)
   - For production: Add your server's IP address

5. **Get Connection String**
   - Go to **Database** → Click **"Connect"**
   - Choose **"Connect your application"**
   - Copy the connection string (looks like):
     ```
     mongodb+srv://marketing_minds_user:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
     ```
   - Replace `<password>` with your actual password

6. **Update `.env` file**:
   ```bash
   MONGO_URL=mongodb+srv://marketing_minds_user:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

### Option B: Local MongoDB

If you prefer local installation:
```bash
# Ubuntu/Debian
sudo apt-get install mongodb

# Start MongoDB
sudo systemctl start mongodb

# Connection string for .env
MONGO_URL=mongodb://localhost:27017/
```

---

## Step 3: Get OpenAI API Key

1. **Create OpenAI Account**
   - Go to: https://platform.openai.com/signup
   - Sign up or log in

2. **Add Payment Method**
   - Go to **Billing** → **Payment methods**
   - Add a credit/debit card (required even for free tier)

3. **Create API Key**
   - Go to: https://platform.openai.com/api-keys
   - Click **"Create new secret key"**
   - Name it: `Marketing Minds Backend`
   - **IMPORTANT**: Copy the key immediately (you won't see it again!)
   - Key format: `sk-proj-xxxxxxxxxxxxxxxxxxxxx`

4. **Update `.env` file**:
   ```bash
   OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
   ```

---

## Step 4: Update Your `.env` File

Open `backend/.env` and replace all placeholder values:

```bash
# ZOHO CONFIGURATION
ZOHO_CLIENT_ID=1000.ABCD1234EFGH5678      # ← Your actual Client ID
ZOHO_CLIENT_SECRET=abc123def456ghi789      # ← Your actual Client Secret
ZOHO_REDIRECT_URI=https://marketing-minds.preview.emergentagent.com/api/zoho/callback
ZOHO_DATA_CENTER=in                        # ← Already set for India

# FRONTEND
REACT_APP_FRONTEND_URL=https://marketing-minds.preview.emergentagent.com

# MONGODB
MONGO_URL=mongodb+srv://user:password@cluster.mongodb.net/  # ← Your MongoDB URL
DB_NAME=marketing_minds

# OPENAI
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx      # ← Your OpenAI key

# CORS
CORS_ORIGINS=https://marketing-minds.preview.emergentagent.com,http://localhost:3000
```

### Verification Command
Run this to verify your setup:
```bash
python verify_zoho_setup.py
```

---

## Step 5: Update Zoho Developer Console (Critical!)

⚠️ **This is the step that was causing your blank page!**

1. Go back to: https://api-console.zoho.in/
2. Open your application
3. Find **"Authorized Redirect URIs"**
4. Make sure it shows **EXACTLY**:
   ```
   https://marketing-minds.preview.emergentagent.com/api/zoho/callback
   ```

5. **Verify**:
   - ✅ Starts with `https://`
   - ✅ Contains `/api/zoho/callback`
   - ✅ No trailing slash
   - ✅ Matches `ZOHO_REDIRECT_URI` in `.env` exactly

---

## Step 6: Start the Backend Server

```bash
# Navigate to backend directory
cd backend

# Install dependencies (if not already done)
pip install -r requirements.txt

# Start the server
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
✅ Database initialization complete!
✅ MongoDB Atlas connection successful!
✅ Zoho Auth Service initialized
✅ Zoho data center resolved to accounts.zoho.in
```

---

## Step 7: Test Zoho OAuth Flow

### 7.1 Test Connection Endpoint

Open in browser or use curl:
```bash
curl http://localhost:8000/api/zoho/connect?user_id=default_user
```

You should get:
```json
{
  "status": "success",
  "authorization_url": "https://accounts.zoho.in/oauth/v2/auth?...",
  "state": "some-uuid"
}
```

### 7.2 Test OAuth Flow

1. Go to your frontend app
2. Navigate to **Settings** page
3. Click **"Connect Zoho CRM"**
4. You'll be redirected to Zoho authorization page
5. Click **"Accept"**
6. **Expected Result**:
   - ✅ See: "Zoho Connected Successfully!" message
   - ✅ Auto-redirect to settings after 1.5 seconds
   - ✅ Settings page shows "Zoho connected"

### 7.3 Verify Tokens Are Stored

Check MongoDB:
```bash
# If using MongoDB Atlas, use MongoDB Compass or Atlas UI
# If using local MongoDB:
mongosh
use marketing_minds
db.zoho_tokens.find()
```

You should see:
```json
{
  "user_id": "default_user",
  "access_token": "1000.xxxxx...",
  "refresh_token": "1000.xxxxx...",
  "expires_at": "2025-11-01T20:00:00+00:00",
  "scope": "ZohoCRM.modules.ALL,..."
}
```

---

## Troubleshooting

### Issue: "redirect_uri_mismatch"
**Solution**:
- Zoho Console URI and `.env` URI must match EXACTLY
- Check for `/api` prefix
- Check for trailing slashes

### Issue: "Invalid client"
**Solution**:
- Verify `ZOHO_CLIENT_ID` and `ZOHO_CLIENT_SECRET`
- Make sure you're using credentials from zoho.in (not zoho.com)

### Issue: Still seeing blank page
**Solution**:
- Check browser console for errors
- Check backend logs
- Run `python verify_zoho_setup.py`

### Issue: "Module not found" errors
**Solution**:
```bash
cd backend
pip install -r requirements.txt
```

### Issue: MongoDB connection failed
**Solution**:
- Check if IP is whitelisted in MongoDB Atlas
- Verify password in connection string (no special characters issues)
- Test connection: `mongosh "your_connection_string"`

---

## Verification Checklist

Run through this before testing:

- [ ] `.env` file exists in `backend/` folder
- [ ] All placeholder values replaced with actual credentials
- [ ] Zoho Console redirect URI includes `/api` and matches `.env`
- [ ] MongoDB connection string is correct
- [ ] OpenAI API key is valid
- [ ] Backend server starts without errors
- [ ] `/api/zoho/connect` endpoint returns authorization URL
- [ ] Authorization URL goes to `accounts.zoho.in` (India)

---

## Support

If you still have issues:

1. **Check Backend Logs**
   - Look for error messages
   - Check for "✅" success indicators

2. **Run Verification Script**
   ```bash
   python verify_zoho_setup.py
   ```

3. **Test Each Component**
   - MongoDB: Can you connect?
   - OpenAI: Does a test API call work?
   - Zoho: Does the authorization URL look correct?

4. **Common Log Messages**
   - ✅ Good: "Zoho OAuth successful, tokens stored"
   - ❌ Bad: "Zoho token exchange failed: invalid_client"
   - ❌ Bad: "redirect_uri_mismatch"

---

## Quick Reference

### Important URLs (India Data Center)
- Zoho API Console: https://api-console.zoho.in/
- Zoho Accounts: https://accounts.zoho.in/
- MongoDB Atlas: https://cloud.mongodb.com/
- OpenAI Platform: https://platform.openai.com/

### Your Callback URL
```
https://marketing-minds.preview.emergentagent.com/api/zoho/callback
```

### Backend Server
```bash
cd backend
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

---

**You're all set! Follow the steps above and your Zoho OAuth will work perfectly.** 🚀
