# Canva OAuth 2.0 Integration Guide

Complete guide to integrating Canva's Developer API using OAuth 2.0 with PKCE (Proof Key for Code Exchange).

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Setting Up Your Canva App](#setting-up-your-canva-app)
4. [Installation & Setup](#installation--setup)
5. [Understanding the OAuth Flow](#understanding-the-oauth-flow)
6. [Implementation Guide](#implementation-guide)
7. [API Examples](#api-examples)
8. [Troubleshooting](#troubleshooting)
9. [Security Best Practices](#security-best-practices)

---

## Overview

This repository contains complete, production-ready examples for integrating with Canva's API using OAuth 2.0:

- **Node.js Example** (`canva-oauth-nodejs.js`) - Express.js server with full OAuth implementation
- **Python Example** (`canva-oauth-python.py`) - Flask server with full OAuth implementation

### Features

✅ **OAuth 2.0 with PKCE** - Secure authorization flow with SHA-256 code challenge
✅ **Token Management** - Automatic token refresh and expiry handling
✅ **CSRF Protection** - State parameter validation
✅ **Example API Calls** - User profile, designs, assets endpoints
✅ **Production Ready** - Error handling, logging, and best practices

---

## Prerequisites

### Required Accounts & Access

- **Canva Account** - Free or paid Canva account
- **Canva Developer Portal Access** - Create at [canva.dev](https://www.canva.dev/)
- **Canva Enterprise Plan** (for private integrations) - Optional, required for team-specific integrations

### Technical Requirements

#### For Node.js:
- Node.js v20.14.0 or higher
- npm v9 or v10

#### For Python:
- Python 3.8 or higher
- pip

---

## Setting Up Your Canva App

### Step 1: Create Your Integration

1. Go to the [Canva Developer Portal](https://www.canva.com/developers/)
2. Click **"Create Integration"** or **"New App"**
3. Choose integration type:
   - **Public Integration**: Available to all Canva users (requires Canva review)
   - **Private Integration**: Only for your team (requires Canva Enterprise plan)

### Step 2: Get Your Credentials

After creating your app, you'll receive:

```
Client ID: OACxxxxxxxxxxxxxxxxxxxxx
Client Secret: OASxxxxxxxxxxxxxxxxxxxxx
```

⚠️ **IMPORTANT**: Keep your Client Secret secure! Never commit it to version control.

### Step 3: Configure OAuth Settings

In your Canva app settings, configure:

#### Development Environment:
```
OAuth Redirect URI: http://localhost:3000/oauth/callback  (Node.js)
                    http://localhost:5000/oauth/callback  (Python)
```

#### Production Environment:
```
OAuth Redirect URI: https://yourdomain.com/oauth/callback
```

### Step 4: Enable Scopes

Enable the following scopes in your app settings:

| Scope | Description |
|-------|-------------|
| `asset:read` | Read user assets |
| `asset:write` | Upload and manage assets |
| `design:content:read` | Read design content |
| `design:meta:read` | Read design metadata |
| `profile:read` | Access user profile information |
| `brandtemplate:meta:read` | Read brand template metadata (optional) |

---

## Installation & Setup

### Node.js Setup

#### 1. Install Dependencies

```bash
npm install express axios
```

Or using the provided `package.json`:

```bash
npm install
```

#### 2. Configure Environment Variables

Create a `.env` file (or edit the config in the code):

```bash
CANVA_CLIENT_ID=your_client_id_here
CANVA_CLIENT_SECRET=your_client_secret_here
```

#### 3. Update Configuration

Edit `canva-oauth-nodejs.js`:

```javascript
const CONFIG = {
  CLIENT_ID: process.env.CANVA_CLIENT_ID || 'YOUR_CANVA_CLIENT_ID',
  CLIENT_SECRET: process.env.CANVA_CLIENT_SECRET || 'YOUR_CANVA_CLIENT_SECRET',
  REDIRECT_URI: 'http://localhost:3000/oauth/callback',
  // ... rest of config
};
```

#### 4. Run the Server

```bash
node canva-oauth-nodejs.js
```

Visit: http://localhost:3000

---

### Python Setup

#### 1. Install Dependencies

```bash
pip install flask requests
```

Or using the provided `requirements.txt`:

```bash
pip install -r requirements.txt
```

#### 2. Configure Environment Variables

Create a `.env` file or set environment variables:

```bash
export CANVA_CLIENT_ID=your_client_id_here
export CANVA_CLIENT_SECRET=your_client_secret_here
```

Or edit the Config class in `canva-oauth-python.py`:

```python
class Config:
    CLIENT_ID = 'YOUR_CANVA_CLIENT_ID'
    CLIENT_SECRET = 'YOUR_CANVA_CLIENT_SECRET'
    REDIRECT_URI = 'http://localhost:5000/oauth/callback'
    # ... rest of config
```

#### 3. Run the Server

```bash
python canva-oauth-python.py
```

Visit: http://localhost:5000

---

## Understanding the OAuth Flow

### OAuth 2.0 with PKCE Flow Diagram

```
┌──────────┐                                   ┌──────────┐                                   ┌──────────┐
│          │                                   │          │                                   │          │
│  User    │                                   │  Your    │                                   │  Canva   │
│ Browser  │                                   │  Server  │                                   │   API    │
│          │                                   │          │                                   │          │
└────┬─────┘                                   └────┬─────┘                                   └────┬─────┘
     │                                              │                                              │
     │  1. Click "Connect to Canva"                 │                                              │
     ├─────────────────────────────────────────────>│                                              │
     │                                              │                                              │
     │                                              │  2. Generate PKCE params:                    │
     │                                              │     - code_verifier (random)                 │
     │                                              │     - code_challenge (SHA256)                │
     │                                              │     - state (random, CSRF protection)        │
     │                                              │                                              │
     │  3. Redirect to Canva authorization URL      │                                              │
     │     with code_challenge & state              │                                              │
     │<─────────────────────────────────────────────┤                                              │
     │                                              │                                              │
     │  4. User authorizes app                      │                                              │
     ├──────────────────────────────────────────────┼─────────────────────────────────────────────>│
     │                                              │                                              │
     │  5. Redirect back with auth code & state     │                                              │
     │<─────────────────────────────────────────────┼──────────────────────────────────────────────┤
     │                                              │                                              │
     │  6. Send code & state to your server         │                                              │
     ├─────────────────────────────────────────────>│                                              │
     │                                              │                                              │
     │                                              │  7. Validate state (CSRF check)              │
     │                                              │                                              │
     │                                              │  8. Exchange code for token                  │
     │                                              │     POST with code_verifier                  │
     │                                              ├─────────────────────────────────────────────>│
     │                                              │                                              │
     │                                              │  9. Return access_token & refresh_token      │
     │                                              │<─────────────────────────────────────────────┤
     │                                              │                                              │
     │  10. Success! Show user interface            │                                              │
     │<─────────────────────────────────────────────┤                                              │
     │                                              │                                              │
     │  11. Make API calls with access_token        │                                              │
     ├─────────────────────────────────────────────>│  12. Forward API request                     │
     │                                              ├─────────────────────────────────────────────>│
     │                                              │                                              │
     │                                              │  13. Return API response                     │
     │  14. Display results                         │<─────────────────────────────────────────────┤
     │<─────────────────────────────────────────────┤                                              │
     │                                              │                                              │
```

### Detailed Step-by-Step Process

#### **STEP 1: Authorization Request**

Your server generates a secure authorization URL with PKCE parameters:

```
https://www.canva.com/api/oauth/authorize?
  client_id=YOUR_CLIENT_ID
  &redirect_uri=http://localhost:3000/oauth/callback
  &scope=asset:read%20design:content:read%20profile:read
  &response_type=code
  &code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM
  &code_challenge_method=S256
  &state=af0ifjsldkj
```

**Key Parameters:**
- `code_challenge`: SHA-256 hash of `code_verifier` (Base64 URL encoded)
- `code_verifier`: Random 43-128 character string (stored securely on server)
- `state`: Random token for CSRF protection

#### **STEP 2: User Authorization**

User is redirected to Canva and logs in (if not already logged in), then authorizes your app to access their data.

#### **STEP 3: Authorization Callback**

Canva redirects back to your redirect URI with:

```
http://localhost:3000/oauth/callback?
  code=AUTHORIZATIONxxxxx
  &state=af0ifjsldkj
```

#### **STEP 4: Token Exchange**

Your server exchanges the authorization code for tokens:

**Request:**
```http
POST https://api.canva.com/rest/v1/oauth/token
Authorization: Basic base64(CLIENT_ID:CLIENT_SECRET)
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code
&code=AUTHORIZATIONxxxxx
&redirect_uri=http://localhost:3000/oauth/callback
&code_verifier=dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk
```

**Response:**
```json
{
  "access_token": "ACCESS_TOKEN_xxx",
  "refresh_token": "REFRESH_TOKEN_xxx",
  "expires_in": 3600,
  "token_type": "Bearer",
  "scope": "asset:read design:content:read profile:read"
}
```

#### **STEP 5: API Calls**

Use the access token to make authenticated API requests:

```http
GET https://api.canva.com/rest/v1/users/me/profile
Authorization: Bearer ACCESS_TOKEN_xxx
Content-Type: application/json
```

---

## Implementation Guide

### Node.js Implementation Highlights

#### Generating PKCE Parameters

```javascript
// Generate code verifier (43-128 characters)
function generateCodeVerifier() {
  return crypto
    .randomBytes(64)
    .toString('base64url')
    .slice(0, 128);
}

// Generate code challenge (SHA-256 hash)
function generateCodeChallenge(verifier) {
  return crypto
    .createHash('sha256')
    .update(verifier)
    .digest('base64url');
}
```

#### Token Exchange

```javascript
const authHeader = Buffer.from(
  `${CLIENT_ID}:${CLIENT_SECRET}`
).toString('base64');

const response = await axios.post(
  TOKEN_URL,
  new URLSearchParams({
    grant_type: 'authorization_code',
    code: authorizationCode,
    redirect_uri: REDIRECT_URI,
    code_verifier: codeVerifier
  }),
  {
    headers: {
      'Authorization': `Basic ${authHeader}`,
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  }
);
```

#### Making API Calls

```javascript
const response = await axios.get(
  'https://api.canva.com/rest/v1/users/me/profile',
  {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    }
  }
);
```

### Python Implementation Highlights

#### Generating PKCE Parameters

```python
def generate_code_verifier(length=128):
    return base64.urlsafe_b64encode(
        secrets.token_bytes(length)
    ).decode('utf-8').rstrip('=')[:length]

def generate_code_challenge(verifier):
    digest = hashlib.sha256(verifier.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')
```

#### Token Exchange

```python
auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')

response = requests.post(
    TOKEN_URL,
    headers={
        'Authorization': f'Basic {auth_b64}',
        'Content-Type': 'application/x-www-form-urlencoded'
    },
    data={
        'grant_type': 'authorization_code',
        'code': authorization_code,
        'redirect_uri': REDIRECT_URI,
        'code_verifier': code_verifier
    }
)
```

#### Making API Calls

```python
response = requests.get(
    'https://api.canva.com/rest/v1/users/me/profile',
    headers={
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
)
```

---

## API Examples

### 1. Get User Profile

**Endpoint:** `GET /users/me/profile`

**Scope Required:** `profile:read`

**Example:**

```javascript
// Node.js
const profile = await oauthClient.getUserProfile();
console.log(profile);
```

```python
# Python
profile = oauth_client.get_user_profile()
print(profile)
```

**Response:**

```json
{
  "id": "user_123",
  "display_name": "John Doe",
  "email": "john@example.com",
  "team_id": "team_456"
}
```

---

### 2. List User Designs

**Endpoint:** `GET /designs`

**Scope Required:** `design:meta:read`

**Example:**

```javascript
// Node.js
const designs = await oauthClient.listDesigns(10);
console.log(designs);
```

```python
# Python
designs = oauth_client.list_designs(limit=10)
print(designs)
```

**Response:**

```json
{
  "items": [
    {
      "id": "design_789",
      "title": "My Awesome Design",
      "thumbnail": {
        "url": "https://..."
      },
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T14:20:00Z"
    }
  ],
  "continuation": "next_page_token"
}
```

---

### 3. Create a Design

**Endpoint:** `POST /designs`

**Scope Required:** `design:content:write`

**Example:**

```javascript
// Node.js
const newDesign = await oauthClient.createDesign('My New Design');
console.log(newDesign);
```

```python
# Python
new_design = oauth_client.create_design(title='My New Design')
print(new_design)
```

**Response:**

```json
{
  "id": "design_101",
  "title": "My New Design",
  "edit_url": "https://www.canva.com/design/design_101/edit",
  "created_at": "2025-01-20T09:15:00Z"
}
```

---

### 4. List User Assets

**Endpoint:** `GET /assets`

**Scope Required:** `asset:read`

**Example:**

```javascript
// Node.js
const assets = await oauthClient.listAssets(10);
console.log(assets);
```

```python
# Python
assets = oauth_client.list_assets(limit=10)
print(assets)
```

**Response:**

```json
{
  "items": [
    {
      "id": "asset_202",
      "name": "logo.png",
      "type": "image",
      "thumbnail": {
        "url": "https://..."
      },
      "created_at": "2025-01-10T08:00:00Z"
    }
  ],
  "continuation": "next_page_token"
}
```

---

### 5. Upload an Asset

**Endpoint:** `POST /assets/upload`

**Scope Required:** `asset:write`

**Example (Node.js):**

```javascript
const FormData = require('form-data');
const fs = require('fs');

async function uploadAsset(filePath) {
  const form = new FormData();
  form.append('file', fs.createReadStream(filePath));
  form.append('name', 'my-image.png');

  const response = await axios.post(
    'https://api.canva.com/rest/v1/assets/upload',
    form,
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        ...form.getHeaders()
      }
    }
  );

  return response.data;
}
```

---

## Troubleshooting

### Common Issues

#### 1. **Invalid Redirect URI**

**Error:**
```json
{
  "error": "invalid_request",
  "error_description": "redirect_uri mismatch"
}
```

**Solution:**
- Ensure the `redirect_uri` in your code exactly matches the one configured in Canva Developer Portal
- Check for trailing slashes, http vs https, localhost vs 127.0.0.1

---

#### 2. **Invalid Client Credentials**

**Error:**
```json
{
  "error": "invalid_client"
}
```

**Solution:**
- Verify your `CLIENT_ID` and `CLIENT_SECRET` are correct
- Ensure you're using the correct encoding for Basic Authentication
- Check that your credentials haven't been revoked

---

#### 3. **Insufficient Scope**

**Error:**
```json
{
  "error": "insufficient_scope",
  "error_description": "The access token does not have the required scope"
}
```

**Solution:**
- Add the required scope to your authorization request
- Ensure the scope is enabled in your Canva app settings
- Re-authenticate to get a token with the new scope

---

#### 4. **Token Expired**

**Error:**
```json
{
  "error": "invalid_token",
  "error_description": "The access token has expired"
}
```

**Solution:**
- Use the refresh token to obtain a new access token
- Implement automatic token refresh in your application

---

#### 5. **PKCE Verification Failed**

**Error:**
```json
{
  "error": "invalid_grant",
  "error_description": "code verifier does not match code challenge"
}
```

**Solution:**
- Ensure you're using the correct `code_verifier` that corresponds to the `code_challenge`
- Verify SHA-256 hashing and Base64 URL encoding is correct
- Check that the `code_verifier` is stored properly between authorization and token exchange

---

## Security Best Practices

### 1. **Never Expose Client Secret**

❌ **DON'T:**
```javascript
// Don't hardcode in frontend code
const CLIENT_SECRET = 'your_secret_here';
```

✅ **DO:**
```javascript
// Store in environment variables, server-side only
const CLIENT_SECRET = process.env.CANVA_CLIENT_SECRET;
```

---

### 2. **Always Use PKCE**

PKCE (Proof Key for Code Exchange) protects against authorization code interception attacks.

✅ **Always generate secure random values:**
```javascript
const codeVerifier = crypto.randomBytes(64).toString('base64url');
```

---

### 3. **Validate State Parameter**

Protect against CSRF attacks by validating the `state` parameter:

```javascript
if (receivedState !== storedState) {
  throw new Error('CSRF attack detected');
}
```

---

### 4. **Store Tokens Securely**

✅ **DO:**
- Encrypt tokens in database
- Use secure, HTTP-only cookies
- Store in secure session management system

❌ **DON'T:**
- Store in localStorage (vulnerable to XSS)
- Log tokens in console/files
- Transmit over insecure connections

---

### 5. **Handle Token Expiry**

Implement automatic token refresh:

```javascript
if (isTokenExpired(accessToken)) {
  accessToken = await refreshAccessToken(refreshToken);
}
```

---

### 6. **Minimum Required Scopes**

Only request scopes you actually need:

```javascript
// ❌ Don't request unnecessary scopes
const SCOPES = 'asset:read asset:write design:content:read design:content:write profile:read';

// ✅ Only request what you need
const SCOPES = 'profile:read design:meta:read';
```

---

### 7. **Use HTTPS in Production**

Always use HTTPS for:
- Redirect URIs
- API requests
- Token exchange

```javascript
// ❌ Development
REDIRECT_URI: 'http://localhost:3000/oauth/callback'

// ✅ Production
REDIRECT_URI: 'https://yourdomain.com/oauth/callback'
```

---

## Additional Resources

### Official Documentation

- [Canva Connect API Docs](https://www.canva.dev/docs/connect/)
- [Authentication Guide](https://www.canva.dev/docs/connect/authentication/)
- [API Reference](https://www.canva.dev/docs/connect/api-reference/)
- [Canva Developer Portal](https://www.canva.com/developers/)

### Code Examples

- [Canva Starter Kit (GitHub)](https://github.com/canva-sdks/canva-connect-api-starter-kit)
- [OpenAPI Specification](https://www.canva.dev/sources/connect/api/latest/api.yml)

### OAuth 2.0 Standards

- [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [PKCE RFC 7636](https://tools.ietf.org/html/rfc7636)

---

## Support

### Getting Help

- **GitHub Issues**: Report bugs or request features
- **Canva Community**: Join the [Canva Developers Community](https://www.canva.dev/community/)
- **Email Support**: Contact Canva developer support

---

## License

These code examples are provided as-is for educational and integration purposes.

---

## Changelog

### Version 1.0.0 (2025-01-26)
- Initial release
- Node.js and Python examples
- Complete OAuth 2.0 with PKCE implementation
- Example API calls for user profile, designs, and assets
- Comprehensive documentation

---

**Happy Coding! 🎨**
