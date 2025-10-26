/**
 * Canva OAuth 2.0 Integration - Node.js Example
 *
 * This example demonstrates:
 * 1. OAuth 2.0 authorization with PKCE (Proof Key for Code Exchange)
 * 2. Token exchange
 * 3. API calls to Canva Connect API
 */

const express = require('express');
const crypto = require('crypto');
const axios = require('axios');

// ========================================
// CONFIGURATION
// ========================================

const CONFIG = {
  CLIENT_ID: 'YOUR_CANVA_CLIENT_ID',
  CLIENT_SECRET: 'YOUR_CANVA_CLIENT_SECRET',
  REDIRECT_URI: 'http://localhost:3000/oauth/callback',

  // Canva OAuth endpoints
  AUTHORIZE_URL: 'https://www.canva.com/api/oauth/authorize',
  TOKEN_URL: 'https://api.canva.com/rest/v1/oauth/token',

  // API endpoints
  API_BASE_URL: 'https://api.canva.com/rest/v1',

  // Required scopes (space-separated)
  SCOPES: 'asset:read asset:write design:content:read design:meta:read profile:read',

  PORT: 3000
};

// ========================================
// PKCE HELPER FUNCTIONS
// ========================================

/**
 * Generate a cryptographically random code verifier (43-128 characters)
 */
function generateCodeVerifier() {
  return crypto
    .randomBytes(64)
    .toString('base64url')
    .slice(0, 128);
}

/**
 * Generate code challenge from verifier using SHA-256
 */
function generateCodeChallenge(verifier) {
  return crypto
    .createHash('sha256')
    .update(verifier)
    .digest('base64url');
}

/**
 * Generate random state parameter for CSRF protection
 */
function generateState() {
  return crypto.randomBytes(32).toString('hex');
}

// ========================================
// OAUTH FLOW IMPLEMENTATION
// ========================================

class CanvaOAuthClient {
  constructor(config) {
    this.config = config;
    this.sessionStore = new Map(); // In production, use Redis or similar
    this.accessToken = null;
    this.refreshToken = null;
  }

  /**
   * STEP 1: Generate authorization URL
   *
   * This URL is used to redirect the user to Canva for authorization
   */
  getAuthorizationUrl() {
    const codeVerifier = generateCodeVerifier();
    const codeChallenge = generateCodeChallenge(codeVerifier);
    const state = generateState();

    // Store verifier and state for later validation
    this.sessionStore.set(state, {
      codeVerifier,
      timestamp: Date.now()
    });

    const params = new URLSearchParams({
      client_id: this.config.CLIENT_ID,
      redirect_uri: this.config.REDIRECT_URI,
      scope: this.config.SCOPES,
      response_type: 'code',
      code_challenge: codeChallenge,
      code_challenge_method: 'S256',
      state: state
    });

    const authUrl = `${this.config.AUTHORIZE_URL}?${params.toString()}`;

    console.log('\n🔐 Authorization URL generated:');
    console.log(authUrl);
    console.log('\n📝 State:', state);
    console.log('📝 Code Verifier:', codeVerifier);
    console.log('📝 Code Challenge:', codeChallenge);

    return authUrl;
  }

  /**
   * STEP 2: Exchange authorization code for access token
   *
   * @param {string} code - Authorization code from callback
   * @param {string} state - State parameter for validation
   */
  async exchangeCodeForToken(code, state) {
    // Validate state to prevent CSRF attacks
    const session = this.sessionStore.get(state);

    if (!session) {
      throw new Error('Invalid state parameter - possible CSRF attack');
    }

    // Clean up used state
    this.sessionStore.delete(state);

    const { codeVerifier } = session;

    // Prepare Basic Authentication header
    const authHeader = Buffer.from(
      `${this.config.CLIENT_ID}:${this.config.CLIENT_SECRET}`
    ).toString('base64');

    const tokenData = {
      grant_type: 'authorization_code',
      code: code,
      redirect_uri: this.config.REDIRECT_URI,
      code_verifier: codeVerifier
    };

    try {
      console.log('\n🔄 Exchanging authorization code for tokens...');

      const response = await axios.post(
        this.config.TOKEN_URL,
        new URLSearchParams(tokenData),
        {
          headers: {
            'Authorization': `Basic ${authHeader}`,
            'Content-Type': 'application/x-www-form-urlencoded'
          }
        }
      );

      const { access_token, refresh_token, expires_in, token_type, scope } = response.data;

      // Store tokens
      this.accessToken = access_token;
      this.refreshToken = refresh_token;

      console.log('✅ Tokens obtained successfully!');
      console.log('📝 Token Type:', token_type);
      console.log('📝 Expires In:', expires_in, 'seconds');
      console.log('📝 Scopes:', scope);
      console.log('📝 Access Token:', access_token.substring(0, 20) + '...');

      return {
        accessToken: access_token,
        refreshToken: refresh_token,
        expiresIn: expires_in,
        tokenType: token_type,
        scope: scope
      };

    } catch (error) {
      console.error('❌ Token exchange failed:', error.response?.data || error.message);
      throw error;
    }
  }

  /**
   * STEP 3: Refresh access token using refresh token
   */
  async refreshAccessToken(refreshToken) {
    const authHeader = Buffer.from(
      `${this.config.CLIENT_ID}:${this.config.CLIENT_SECRET}`
    ).toString('base64');

    try {
      console.log('\n🔄 Refreshing access token...');

      const response = await axios.post(
        this.config.TOKEN_URL,
        new URLSearchParams({
          grant_type: 'refresh_token',
          refresh_token: refreshToken || this.refreshToken
        }),
        {
          headers: {
            'Authorization': `Basic ${authHeader}`,
            'Content-Type': 'application/x-www-form-urlencoded'
          }
        }
      );

      const { access_token, refresh_token, expires_in } = response.data;

      this.accessToken = access_token;
      this.refreshToken = refresh_token;

      console.log('✅ Token refreshed successfully!');

      return {
        accessToken: access_token,
        refreshToken: refresh_token,
        expiresIn: expires_in
      };

    } catch (error) {
      console.error('❌ Token refresh failed:', error.response?.data || error.message);
      throw error;
    }
  }

  /**
   * EXAMPLE API CALL: Get user profile
   */
  async getUserProfile() {
    if (!this.accessToken) {
      throw new Error('No access token available. Please authenticate first.');
    }

    try {
      console.log('\n📡 Fetching user profile...');

      const response = await axios.get(
        `${this.config.API_BASE_URL}/users/me/profile`,
        {
          headers: {
            'Authorization': `Bearer ${this.accessToken}`,
            'Content-Type': 'application/json'
          }
        }
      );

      console.log('✅ User profile retrieved:');
      console.log(JSON.stringify(response.data, null, 2));

      return response.data;

    } catch (error) {
      console.error('❌ API call failed:', error.response?.data || error.message);
      throw error;
    }
  }

  /**
   * EXAMPLE API CALL: List user designs
   */
  async listDesigns(limit = 10) {
    if (!this.accessToken) {
      throw new Error('No access token available. Please authenticate first.');
    }

    try {
      console.log('\n📡 Fetching user designs...');

      const response = await axios.get(
        `${this.config.API_BASE_URL}/designs`,
        {
          headers: {
            'Authorization': `Bearer ${this.accessToken}`,
            'Content-Type': 'application/json'
          },
          params: {
            limit: limit
          }
        }
      );

      console.log('✅ Designs retrieved:');
      console.log(JSON.stringify(response.data, null, 2));

      return response.data;

    } catch (error) {
      console.error('❌ API call failed:', error.response?.data || error.message);
      throw error;
    }
  }

  /**
   * EXAMPLE API CALL: Create a design from a template
   */
  async createDesign(title) {
    if (!this.accessToken) {
      throw new Error('No access token available. Please authenticate first.');
    }

    try {
      console.log('\n📡 Creating new design...');

      const response = await axios.post(
        `${this.config.API_BASE_URL}/designs`,
        {
          title: title || 'Design created via API'
        },
        {
          headers: {
            'Authorization': `Bearer ${this.accessToken}`,
            'Content-Type': 'application/json'
          }
        }
      );

      console.log('✅ Design created:');
      console.log(JSON.stringify(response.data, null, 2));

      return response.data;

    } catch (error) {
      console.error('❌ API call failed:', error.response?.data || error.message);
      throw error;
    }
  }
}

// ========================================
// EXPRESS SERVER SETUP
// ========================================

const app = express();
const oauthClient = new CanvaOAuthClient(CONFIG);

/**
 * ROUTE: Home page - Start OAuth flow
 */
app.get('/', (req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html>
      <head><title>Canva OAuth Example</title></head>
      <body style="font-family: Arial; padding: 40px; max-width: 600px; margin: 0 auto;">
        <h1>🎨 Canva OAuth 2.0 Integration</h1>
        <p>This example demonstrates OAuth 2.0 authentication with Canva's API using PKCE.</p>
        <a href="/auth/start" style="display: inline-block; padding: 12px 24px; background: #00C4CC; color: white; text-decoration: none; border-radius: 4px; font-weight: bold;">
          Connect to Canva
        </a>
        <h2>Features:</h2>
        <ul>
          <li>✅ OAuth 2.0 with PKCE (SHA-256)</li>
          <li>✅ Secure token exchange</li>
          <li>✅ Access token refresh</li>
          <li>✅ Example API calls</li>
        </ul>
      </body>
    </html>
  `);
});

/**
 * ROUTE: Start OAuth flow - Redirect to Canva
 */
app.get('/auth/start', (req, res) => {
  const authUrl = oauthClient.getAuthorizationUrl();
  res.redirect(authUrl);
});

/**
 * ROUTE: OAuth callback - Handle authorization response
 */
app.get('/oauth/callback', async (req, res) => {
  const { code, state, error } = req.query;

  if (error) {
    return res.send(`
      <h1>❌ Authorization Failed</h1>
      <p>Error: ${error}</p>
      <a href="/">Try Again</a>
    `);
  }

  if (!code || !state) {
    return res.send(`
      <h1>❌ Invalid Callback</h1>
      <p>Missing code or state parameter</p>
      <a href="/">Try Again</a>
    `);
  }

  try {
    // Exchange code for tokens
    const tokens = await oauthClient.exchangeCodeForToken(code, state);

    res.send(`
      <!DOCTYPE html>
      <html>
        <head><title>Authorization Successful</title></head>
        <body style="font-family: Arial; padding: 40px; max-width: 600px; margin: 0 auto;">
          <h1>✅ Authorization Successful!</h1>
          <p>You've successfully connected to Canva.</p>
          <h2>Tokens Received:</h2>
          <ul>
            <li><strong>Access Token:</strong> ${tokens.accessToken.substring(0, 30)}...</li>
            <li><strong>Expires In:</strong> ${tokens.expiresIn} seconds</li>
            <li><strong>Scopes:</strong> ${tokens.scope}</li>
          </ul>
          <div style="margin-top: 30px;">
            <a href="/api/profile" style="display: inline-block; padding: 12px 24px; background: #00C4CC; color: white; text-decoration: none; border-radius: 4px; margin-right: 10px;">
              Get User Profile
            </a>
            <a href="/api/designs" style="display: inline-block; padding: 12px 24px; background: #7D2AE8; color: white; text-decoration: none; border-radius: 4px;">
              List Designs
            </a>
          </div>
        </body>
      </html>
    `);

  } catch (error) {
    res.send(`
      <h1>❌ Token Exchange Failed</h1>
      <p>Error: ${error.message}</p>
      <a href="/">Try Again</a>
    `);
  }
});

/**
 * ROUTE: Get user profile
 */
app.get('/api/profile', async (req, res) => {
  try {
    const profile = await oauthClient.getUserProfile();
    res.json(profile);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * ROUTE: List user designs
 */
app.get('/api/designs', async (req, res) => {
  try {
    const designs = await oauthClient.listDesigns();
    res.json(designs);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * Start the server
 */
app.listen(CONFIG.PORT, () => {
  console.log(`
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║         🎨 Canva OAuth 2.0 Integration Server            ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

✅ Server running at: http://localhost:${CONFIG.PORT}

📝 Configuration:
   - Client ID: ${CONFIG.CLIENT_ID}
   - Redirect URI: ${CONFIG.REDIRECT_URI}
   - Scopes: ${CONFIG.SCOPES}

🚀 Next steps:
   1. Update CLIENT_ID and CLIENT_SECRET in the config
   2. Visit http://localhost:${CONFIG.PORT}
   3. Click "Connect to Canva"
   4. Authorize the application
   5. Test API calls!

📚 Documentation: https://www.canva.dev/docs/connect/
  `);
});

// ========================================
// STANDALONE USAGE EXAMPLE (without server)
// ========================================

/**
 * Uncomment this section to test the OAuth flow programmatically
 */
/*
async function main() {
  const client = new CanvaOAuthClient(CONFIG);

  // Step 1: Generate auth URL and visit it manually
  console.log('Visit this URL to authorize:');
  const authUrl = client.getAuthorizationUrl();
  console.log(authUrl);

  // Step 2: After authorization, paste the code and state from callback URL
  // const code = 'PASTE_CODE_HERE';
  // const state = 'PASTE_STATE_HERE';

  // const tokens = await client.exchangeCodeForToken(code, state);
  // console.log('Tokens:', tokens);

  // Step 3: Make API calls
  // const profile = await client.getUserProfile();
  // const designs = await client.listDesigns();
}

// main().catch(console.error);
*/
