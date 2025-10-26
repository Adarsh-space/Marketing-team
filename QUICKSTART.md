# Canva OAuth 2.0 - Quick Start Guide

Get up and running with Canva's OAuth 2.0 integration in 5 minutes!

## Prerequisites

- Canva account
- Canva app credentials (Client ID & Secret)
- Node.js 20+ OR Python 3.8+

---

## Option 1: Node.js Quick Start

### 1. Install Dependencies

```bash
npm install
```

Or manually:
```bash
npm install express axios
```

### 2. Configure Credentials

Edit `canva-oauth-nodejs.js`:

```javascript
const CONFIG = {
  CLIENT_ID: 'YOUR_CANVA_CLIENT_ID',        // Replace this
  CLIENT_SECRET: 'YOUR_CANVA_CLIENT_SECRET', // Replace this
  REDIRECT_URI: 'http://localhost:3000/oauth/callback',
  // ... rest of config
};
```

### 3. Update Canva App Settings

In your [Canva Developer Portal](https://www.canva.com/developers/):

- Set **OAuth Redirect URI** to: `http://localhost:3000/oauth/callback`
- Enable scopes: `asset:read`, `design:meta:read`, `profile:read`

### 4. Run the Server

```bash
node canva-oauth-nodejs.js
```

### 5. Test the Integration

1. Visit: http://localhost:3000
2. Click "Connect to Canva"
3. Authorize the application
4. Test API calls!

---

## Option 2: Python Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install flask requests python-dotenv
```

### 2. Configure Credentials

Edit `canva-oauth-python.py`:

```python
class Config:
    CLIENT_ID = 'YOUR_CANVA_CLIENT_ID'        # Replace this
    CLIENT_SECRET = 'YOUR_CANVA_CLIENT_SECRET' # Replace this
    REDIRECT_URI = 'http://localhost:5000/oauth/callback'
    # ... rest of config
```

### 3. Update Canva App Settings

In your [Canva Developer Portal](https://www.canva.com/developers/):

- Set **OAuth Redirect URI** to: `http://localhost:5000/oauth/callback`
- Enable scopes: `asset:read`, `design:meta:read`, `profile:read`

### 4. Run the Server

```bash
python canva-oauth-python.py
```

### 5. Test the Integration

1. Visit: http://localhost:5000
2. Click "Connect to Canva"
3. Authorize the application
4. Test API calls!

---

## Sample Authorization URL

When you start the OAuth flow, you'll be redirected to a URL like this:

```
https://www.canva.com/api/oauth/authorize?
  client_id=OACxxxxxxxxxxxxxxxxxxxxx
  &redirect_uri=http://localhost:3000/oauth/callback
  &scope=asset:read%20design:meta:read%20profile:read
  &response_type=code
  &code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM
  &code_challenge_method=S256
  &state=af0ifjsldkj
```

---

## Sample API Requests

### Get User Profile

**Node.js:**
```javascript
const profile = await oauthClient.getUserProfile();
```

**Python:**
```python
profile = oauth_client.get_user_profile()
```

**Example Response:**
```json
{
  "id": "user_123",
  "display_name": "John Doe",
  "email": "john@example.com"
}
```

### List Designs

**Node.js:**
```javascript
const designs = await oauthClient.listDesigns(10);
```

**Python:**
```python
designs = oauth_client.list_designs(limit=10)
```

**Example Response:**
```json
{
  "items": [
    {
      "id": "design_789",
      "title": "My Design",
      "thumbnail": { "url": "https://..." },
      "created_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

---

## Testing with cURL

Once you have an access token, you can test the API directly:

```bash
# Get user profile
curl -X GET https://api.canva.com/rest/v1/users/me/profile \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"

# List designs
curl -X GET https://api.canva.com/rest/v1/designs?limit=10 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

---

## Common Issues

### Issue: "redirect_uri mismatch"

**Solution:** Ensure the redirect URI in your code exactly matches the one in Canva Developer Portal.

### Issue: "invalid_client"

**Solution:** Double-check your Client ID and Client Secret.

### Issue: "insufficient_scope"

**Solution:** Enable the required scopes in your Canva app settings and re-authenticate.

---

## Next Steps

- Read the full [CANVA_OAUTH_GUIDE.md](./CANVA_OAUTH_GUIDE.md) for detailed explanations
- Check out [Canva's official documentation](https://www.canva.dev/docs/connect/)
- Explore the [Canva Starter Kit](https://github.com/canva-sdks/canva-connect-api-starter-kit)

---

## Environment Variables (Optional)

For better security, use environment variables:

### Node.js (.env)
```bash
CANVA_CLIENT_ID=your_client_id_here
CANVA_CLIENT_SECRET=your_client_secret_here
```

Then load with:
```javascript
require('dotenv').config();
const CLIENT_ID = process.env.CANVA_CLIENT_ID;
```

### Python (.env)
```bash
export CANVA_CLIENT_ID=your_client_id_here
export CANVA_CLIENT_SECRET=your_client_secret_here
```

Or use python-dotenv:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## Available Scopes

| Scope | Description |
|-------|-------------|
| `asset:read` | Read user assets |
| `asset:write` | Upload and manage assets |
| `design:content:read` | Read design content |
| `design:content:write` | Create and modify designs |
| `design:meta:read` | Read design metadata |
| `profile:read` | Access user profile |
| `brandtemplate:meta:read` | Read brand templates |

---

**Ready to build? Start coding! 🚀**
