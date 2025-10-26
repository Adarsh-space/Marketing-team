"""
Canva OAuth 2.0 Integration - Python Example

This example demonstrates:
1. OAuth 2.0 authorization with PKCE (Proof Key for Code Exchange)
2. Token exchange
3. API calls to Canva Connect API
"""

import os
import secrets
import hashlib
import base64
from urllib.parse import urlencode, parse_qs, urlparse
from flask import Flask, request, redirect, jsonify, render_template_string
import requests
from datetime import datetime, timedelta

# ========================================
# CONFIGURATION
# ========================================

class Config:
    # Your Canva app credentials
    CLIENT_ID = os.getenv('CANVA_CLIENT_ID', 'YOUR_CANVA_CLIENT_ID')
    CLIENT_SECRET = os.getenv('CANVA_CLIENT_SECRET', 'YOUR_CANVA_CLIENT_SECRET')
    REDIRECT_URI = 'http://localhost:5000/oauth/callback'

    # Canva OAuth endpoints
    AUTHORIZE_URL = 'https://www.canva.com/api/oauth/authorize'
    TOKEN_URL = 'https://api.canva.com/rest/v1/oauth/token'

    # API endpoints
    API_BASE_URL = 'https://api.canva.com/rest/v1'

    # Required scopes (space-separated)
    SCOPES = 'asset:read asset:write design:content:read design:meta:read profile:read'

    PORT = 5000


# ========================================
# PKCE HELPER FUNCTIONS
# ========================================

def generate_code_verifier(length=128):
    """
    Generate a cryptographically random code verifier (43-128 characters)
    """
    return base64.urlsafe_b64encode(secrets.token_bytes(length)).decode('utf-8').rstrip('=')[:length]


def generate_code_challenge(verifier):
    """
    Generate code challenge from verifier using SHA-256
    """
    digest = hashlib.sha256(verifier.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')


def generate_state():
    """
    Generate random state parameter for CSRF protection
    """
    return secrets.token_urlsafe(32)


# ========================================
# OAUTH CLIENT CLASS
# ========================================

class CanvaOAuthClient:
    """
    Canva OAuth 2.0 client with PKCE support
    """

    def __init__(self, config):
        self.config = config
        self.session_store = {}  # In production, use Redis or database
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None

    def get_authorization_url(self):
        """
        STEP 1: Generate authorization URL

        This URL is used to redirect the user to Canva for authorization
        """
        code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(code_verifier)
        state = generate_state()

        # Store verifier and state for later validation
        self.session_store[state] = {
            'code_verifier': code_verifier,
            'timestamp': datetime.now()
        }

        params = {
            'client_id': self.config.CLIENT_ID,
            'redirect_uri': self.config.REDIRECT_URI,
            'scope': self.config.SCOPES,
            'response_type': 'code',
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'state': state
        }

        auth_url = f"{self.config.AUTHORIZE_URL}?{urlencode(params)}"

        print('\n🔐 Authorization URL generated:')
        print(auth_url)
        print(f'\n📝 State: {state}')
        print(f'📝 Code Verifier: {code_verifier}')
        print(f'📝 Code Challenge: {code_challenge}')

        return auth_url

    def exchange_code_for_token(self, code, state):
        """
        STEP 2: Exchange authorization code for access token

        Args:
            code: Authorization code from callback
            state: State parameter for validation
        """
        # Validate state to prevent CSRF attacks
        session = self.session_store.get(state)

        if not session:
            raise ValueError('Invalid state parameter - possible CSRF attack')

        # Clean up used state
        del self.session_store[state]

        code_verifier = session['code_verifier']

        # Prepare Basic Authentication
        auth_string = f"{self.config.CLIENT_ID}:{self.config.CLIENT_SECRET}"
        auth_bytes = auth_string.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')

        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.config.REDIRECT_URI,
            'code_verifier': code_verifier
        }

        try:
            print('\n🔄 Exchanging authorization code for tokens...')

            response = requests.post(
                self.config.TOKEN_URL,
                headers=headers,
                data=data
            )
            response.raise_for_status()

            token_data = response.json()

            # Store tokens
            self.access_token = token_data['access_token']
            self.refresh_token = token_data.get('refresh_token')
            expires_in = token_data.get('expires_in', 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)

            print('✅ Tokens obtained successfully!')
            print(f"📝 Token Type: {token_data.get('token_type')}")
            print(f"📝 Expires In: {expires_in} seconds")
            print(f"📝 Scopes: {token_data.get('scope')}")
            print(f"📝 Access Token: {self.access_token[:20]}...")

            return {
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'expires_in': expires_in,
                'token_type': token_data.get('token_type'),
                'scope': token_data.get('scope')
            }

        except requests.exceptions.RequestException as e:
            print(f'❌ Token exchange failed: {e}')
            if hasattr(e.response, 'text'):
                print(f'Response: {e.response.text}')
            raise

    def refresh_access_token(self, refresh_token=None):
        """
        STEP 3: Refresh access token using refresh token
        """
        token_to_refresh = refresh_token or self.refresh_token

        if not token_to_refresh:
            raise ValueError('No refresh token available')

        # Prepare Basic Authentication
        auth_string = f"{self.config.CLIENT_ID}:{self.config.CLIENT_SECRET}"
        auth_bytes = auth_string.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')

        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'grant_type': 'refresh_token',
            'refresh_token': token_to_refresh
        }

        try:
            print('\n🔄 Refreshing access token...')

            response = requests.post(
                self.config.TOKEN_URL,
                headers=headers,
                data=data
            )
            response.raise_for_status()

            token_data = response.json()

            self.access_token = token_data['access_token']
            self.refresh_token = token_data.get('refresh_token', self.refresh_token)
            expires_in = token_data.get('expires_in', 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)

            print('✅ Token refreshed successfully!')

            return {
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'expires_in': expires_in
            }

        except requests.exceptions.RequestException as e:
            print(f'❌ Token refresh failed: {e}')
            if hasattr(e.response, 'text'):
                print(f'Response: {e.response.text}')
            raise

    def _ensure_valid_token(self):
        """
        Internal method to ensure token is valid before API calls
        """
        if not self.access_token:
            raise ValueError('No access token available. Please authenticate first.')

        # Auto-refresh if token is expired
        if self.token_expiry and datetime.now() >= self.token_expiry:
            if self.refresh_token:
                print('⚠️  Token expired, refreshing...')
                self.refresh_access_token()
            else:
                raise ValueError('Token expired and no refresh token available')

    def get_user_profile(self):
        """
        EXAMPLE API CALL: Get user profile
        """
        self._ensure_valid_token()

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        try:
            print('\n📡 Fetching user profile...')

            response = requests.get(
                f"{self.config.API_BASE_URL}/users/me/profile",
                headers=headers
            )
            response.raise_for_status()

            data = response.json()
            print('✅ User profile retrieved:')
            print(data)

            return data

        except requests.exceptions.RequestException as e:
            print(f'❌ API call failed: {e}')
            if hasattr(e.response, 'text'):
                print(f'Response: {e.response.text}')
            raise

    def list_designs(self, limit=10):
        """
        EXAMPLE API CALL: List user designs
        """
        self._ensure_valid_token()

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        params = {
            'limit': limit
        }

        try:
            print('\n📡 Fetching user designs...')

            response = requests.get(
                f"{self.config.API_BASE_URL}/designs",
                headers=headers,
                params=params
            )
            response.raise_for_status()

            data = response.json()
            print('✅ Designs retrieved:')
            print(data)

            return data

        except requests.exceptions.RequestException as e:
            print(f'❌ API call failed: {e}')
            if hasattr(e.response, 'text'):
                print(f'Response: {e.response.text}')
            raise

    def create_design(self, title=None):
        """
        EXAMPLE API CALL: Create a design
        """
        self._ensure_valid_token()

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            'title': title or 'Design created via API'
        }

        try:
            print('\n📡 Creating new design...')

            response = requests.post(
                f"{self.config.API_BASE_URL}/designs",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            print('✅ Design created:')
            print(data)

            return data

        except requests.exceptions.RequestException as e:
            print(f'❌ API call failed: {e}')
            if hasattr(e.response, 'text'):
                print(f'Response: {e.response.text}')
            raise

    def list_assets(self, limit=10):
        """
        EXAMPLE API CALL: List user assets
        """
        self._ensure_valid_token()

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        params = {
            'limit': limit
        }

        try:
            print('\n📡 Fetching user assets...')

            response = requests.get(
                f"{self.config.API_BASE_URL}/assets",
                headers=headers,
                params=params
            )
            response.raise_for_status()

            data = response.json()
            print('✅ Assets retrieved:')
            print(data)

            return data

        except requests.exceptions.RequestException as e:
            print(f'❌ API call failed: {e}')
            if hasattr(e.response, 'text'):
                print(f'Response: {e.response.text}')
            raise


# ========================================
# FLASK WEB SERVER
# ========================================

app = Flask(__name__)
oauth_client = CanvaOAuthClient(Config)

# HTML Templates
HOME_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Canva OAuth Example</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 40px; max-width: 600px; margin: 0 auto; }
        .btn { display: inline-block; padding: 12px 24px; background: #00C4CC; color: white;
               text-decoration: none; border-radius: 4px; font-weight: bold; margin-top: 20px; }
        .btn:hover { background: #00a8b0; }
        h1 { color: #333; }
        ul { line-height: 1.8; }
    </style>
</head>
<body>
    <h1>🎨 Canva OAuth 2.0 Integration</h1>
    <p>This example demonstrates OAuth 2.0 authentication with Canva's API using PKCE.</p>
    <a href="/auth/start" class="btn">Connect to Canva</a>

    <h2>Features:</h2>
    <ul>
        <li>✅ OAuth 2.0 with PKCE (SHA-256)</li>
        <li>✅ Secure token exchange</li>
        <li>✅ Access token refresh</li>
        <li>✅ Example API calls</li>
    </ul>
</body>
</html>
"""

SUCCESS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Authorization Successful</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 40px; max-width: 600px; margin: 0 auto; }
        .btn { display: inline-block; padding: 12px 24px; color: white; text-decoration: none;
               border-radius: 4px; margin-right: 10px; margin-top: 10px; }
        .btn-primary { background: #00C4CC; }
        .btn-secondary { background: #7D2AE8; }
        h1 { color: #28a745; }
        code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }
    </style>
</head>
<body>
    <h1>✅ Authorization Successful!</h1>
    <p>You've successfully connected to Canva.</p>

    <h2>Tokens Received:</h2>
    <ul>
        <li><strong>Access Token:</strong> <code>{{ access_token[:30] }}...</code></li>
        <li><strong>Expires In:</strong> {{ expires_in }} seconds</li>
        <li><strong>Scopes:</strong> {{ scope }}</li>
    </ul>

    <div>
        <a href="/api/profile" class="btn btn-primary">Get User Profile</a>
        <a href="/api/designs" class="btn btn-secondary">List Designs</a>
        <a href="/api/assets" class="btn btn-secondary">List Assets</a>
    </div>
</body>
</html>
"""

ERROR_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Error</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 40px; max-width: 600px; margin: 0 auto; }
        h1 { color: #dc3545; }
        .btn { display: inline-block; padding: 12px 24px; background: #00C4CC; color: white;
               text-decoration: none; border-radius: 4px; margin-top: 20px; }
    </style>
</head>
<body>
    <h1>❌ {{ title }}</h1>
    <p>{{ message }}</p>
    <a href="/" class="btn">Try Again</a>
</body>
</html>
"""


@app.route('/')
def home():
    """Home page - Start OAuth flow"""
    return HOME_TEMPLATE


@app.route('/auth/start')
def auth_start():
    """Start OAuth flow - Redirect to Canva"""
    auth_url = oauth_client.get_authorization_url()
    return redirect(auth_url)


@app.route('/oauth/callback')
def oauth_callback():
    """OAuth callback - Handle authorization response"""
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')

    if error:
        return render_template_string(
            ERROR_TEMPLATE,
            title='Authorization Failed',
            message=f'Error: {error}'
        )

    if not code or not state:
        return render_template_string(
            ERROR_TEMPLATE,
            title='Invalid Callback',
            message='Missing code or state parameter'
        )

    try:
        # Exchange code for tokens
        tokens = oauth_client.exchange_code_for_token(code, state)

        return render_template_string(
            SUCCESS_TEMPLATE,
            access_token=tokens['access_token'],
            expires_in=tokens['expires_in'],
            scope=tokens['scope']
        )

    except Exception as e:
        return render_template_string(
            ERROR_TEMPLATE,
            title='Token Exchange Failed',
            message=str(e)
        )


@app.route('/api/profile')
def api_profile():
    """Get user profile"""
    try:
        profile = oauth_client.get_user_profile()
        return jsonify(profile)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/designs')
def api_designs():
    """List user designs"""
    try:
        designs = oauth_client.list_designs()
        return jsonify(designs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/assets')
def api_assets():
    """List user assets"""
    try:
        assets = oauth_client.list_assets()
        return jsonify(assets)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ========================================
# MAIN EXECUTION
# ========================================

if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║         🎨 Canva OAuth 2.0 Integration Server            ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

✅ Server running at: http://localhost:{}

📝 Configuration:
   - Client ID: {}
   - Redirect URI: {}
   - Scopes: {}

🚀 Next steps:
   1. Update CLIENT_ID and CLIENT_SECRET in the config
   2. Visit http://localhost:{}
   3. Click "Connect to Canva"
   4. Authorize the application
   5. Test API calls!

📚 Documentation: https://www.canva.dev/docs/connect/
    """.format(
        Config.PORT,
        Config.CLIENT_ID,
        Config.REDIRECT_URI,
        Config.SCOPES,
        Config.PORT
    ))

    app.run(host='0.0.0.0', port=Config.PORT, debug=True)


# ========================================
# STANDALONE USAGE EXAMPLE (without Flask)
# ========================================

"""
Uncomment this section to test the OAuth flow programmatically:

def main():
    client = CanvaOAuthClient(Config)

    # Step 1: Generate auth URL and visit it manually
    print('Visit this URL to authorize:')
    auth_url = client.get_authorization_url()
    print(auth_url)

    # Step 2: After authorization, paste the code and state from callback URL
    # code = input('Enter authorization code: ')
    # state = input('Enter state parameter: ')

    # tokens = client.exchange_code_for_token(code, state)
    # print('Tokens:', tokens)

    # Step 3: Make API calls
    # profile = client.get_user_profile()
    # designs = client.list_designs()
    # assets = client.list_assets()

if __name__ == '__main__':
    main()
"""
