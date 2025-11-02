"""
OAuth Manager Service
Centralized OAuth state management and token refresh for all platforms
Supports: Zoho, Facebook, Instagram, Twitter, LinkedIn

Author: Marketing Minds AI
"""

import os
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OAuthManager:
    """
    Centralized OAuth Manager for all platform integrations.
    Handles state generation, validation, token refresh, and expiration.
    """

    def __init__(self, mongo_client: AsyncIOMotorClient):
        """
        Initialize OAuth Manager

        Args:
            mongo_client: MongoDB client instance
        """
        self.mongo_client = mongo_client
        self.db = mongo_client.marketing_minds
        self.oauth_states = self.db.oauth_states
        self.social_accounts = self.db.social_accounts
        self.zoho_tokens = self.db.zoho_tokens

        # Platform configurations
        self.platform_configs = {
            'facebook': {
                'client_id': os.getenv('FACEBOOK_APP_ID'),
                'client_secret': os.getenv('FACEBOOK_APP_SECRET'),
                'token_url': 'https://graph.facebook.com/v18.0/oauth/access_token',
                'token_lifetime': 5184000,  # 60 days in seconds
            },
            'instagram': {
                'client_id': os.getenv('FACEBOOK_APP_ID'),  # Instagram uses Facebook app
                'client_secret': os.getenv('FACEBOOK_APP_SECRET'),
                'token_url': 'https://graph.facebook.com/v18.0/oauth/access_token',
                'token_lifetime': 5184000,  # 60 days in seconds
            },
            'twitter': {
                'client_id': os.getenv('TWITTER_CLIENT_ID'),
                'client_secret': os.getenv('TWITTER_CLIENT_SECRET'),
                'token_url': 'https://api.twitter.com/2/oauth2/token',
                'token_lifetime': 7200,  # 2 hours in seconds
            },
            'linkedin': {
                'client_id': os.getenv('LINKEDIN_CLIENT_ID'),
                'client_secret': os.getenv('LINKEDIN_CLIENT_SECRET'),
                'token_url': 'https://www.linkedin.com/oauth/v2/accessToken',
                'token_lifetime': 5184000,  # 60 days in seconds
            },
            'zoho': {
                'client_id': os.getenv('ZOHO_CLIENT_ID'),
                'client_secret': os.getenv('ZOHO_CLIENT_SECRET'),
                'data_center': os.getenv('ZOHO_DATA_CENTER', 'com'),
                'token_lifetime': 3600,  # 1 hour in seconds
            }
        }

    # ==================== State Management ====================

    async def generate_state(
        self,
        user_id: str,
        platform: str,
        redirect_uri: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate secure OAuth state parameter

        Args:
            user_id: User ID initiating OAuth
            platform: Platform name (facebook, twitter, etc.)
            redirect_uri: OAuth redirect URI
            metadata: Optional additional metadata

        Returns:
            str: Secure state token
        """
        try:
            # Generate cryptographically secure random state
            state_token = secrets.token_urlsafe(32)

            # Store state in database with expiration
            state_doc = {
                'state': state_token,
                'user_id': user_id,
                'platform': platform,
                'redirect_uri': redirect_uri,
                'metadata': metadata or {},
                'created_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(minutes=10),  # 10 min expiration
                'used': False
            }

            await self.oauth_states.insert_one(state_doc)

            logger.info(f"Generated OAuth state for user {user_id}, platform {platform}")
            return state_token

        except Exception as e:
            logger.error(f"Error generating OAuth state: {str(e)}")
            raise

    async def validate_state(
        self,
        state: str,
        platform: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate OAuth state parameter

        Args:
            state: State token to validate
            platform: Platform name
            user_id: Optional user ID for additional validation

        Returns:
            dict: Validation result with state data
        """
        try:
            # Find state in database
            query = {
                'state': state,
                'platform': platform,
                'used': False,
                'expires_at': {'$gt': datetime.utcnow()}
            }

            if user_id:
                query['user_id'] = user_id

            state_doc = await self.oauth_states.find_one(query)

            if not state_doc:
                logger.warning(f"Invalid or expired OAuth state: {state}")
                return {
                    'valid': False,
                    'error': 'Invalid or expired state'
                }

            # Mark state as used
            await self.oauth_states.update_one(
                {'_id': state_doc['_id']},
                {'$set': {'used': True, 'used_at': datetime.utcnow()}}
            )

            logger.info(f"Validated OAuth state for user {state_doc['user_id']}, platform {platform}")

            return {
                'valid': True,
                'user_id': state_doc['user_id'],
                'redirect_uri': state_doc['redirect_uri'],
                'metadata': state_doc.get('metadata', {})
            }

        except Exception as e:
            logger.error(f"Error validating OAuth state: {str(e)}")
            return {
                'valid': False,
                'error': str(e)
            }

    async def cleanup_expired_states(self) -> int:
        """
        Clean up expired OAuth states

        Returns:
            int: Number of deleted states
        """
        try:
            result = await self.oauth_states.delete_many({
                'expires_at': {'$lt': datetime.utcnow()}
            })

            count = result.deleted_count
            logger.info(f"Cleaned up {count} expired OAuth states")
            return count

        except Exception as e:
            logger.error(f"Error cleaning up OAuth states: {str(e)}")
            return 0

    # ==================== Token Refresh ====================

    async def refresh_social_token(
        self,
        account_id: str,
        platform: str
    ) -> Dict[str, Any]:
        """
        Refresh access token for a social media account

        Args:
            account_id: Social account ID
            platform: Platform name

        Returns:
            dict: Refresh result
        """
        try:
            # Get account from database
            account = await self.social_accounts.find_one({'account_id': account_id})

            if not account:
                return {
                    'success': False,
                    'error': 'Account not found'
                }

            if account['platform'] != platform:
                return {
                    'success': False,
                    'error': 'Platform mismatch'
                }

            # Platform-specific refresh logic
            if platform in ['facebook', 'instagram']:
                return await self._refresh_facebook_token(account)
            elif platform == 'twitter':
                return await self._refresh_twitter_token(account)
            elif platform == 'linkedin':
                return await self._refresh_linkedin_token(account)
            else:
                return {
                    'success': False,
                    'error': f'Token refresh not supported for {platform}'
                }

        except Exception as e:
            logger.error(f"Error refreshing token for {platform}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _refresh_facebook_token(self, account: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refresh Facebook/Instagram access token
        Facebook uses long-lived tokens that can be extended

        Args:
            account: Account document from database

        Returns:
            dict: Refresh result
        """
        try:
            config = self.platform_configs['facebook']

            params = {
                'grant_type': 'fb_exchange_token',
                'client_id': config['client_id'],
                'client_secret': config['client_secret'],
                'fb_exchange_token': account['access_token']
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(config['token_url'], params=params)
                response.raise_for_status()
                data = response.json()

            # Update account with new token
            new_token = data.get('access_token')
            expires_in = data.get('expires_in', config['token_lifetime'])

            await self.social_accounts.update_one(
                {'_id': account['_id']},
                {
                    '$set': {
                        'access_token': new_token,
                        'token_expires_at': datetime.utcnow() + timedelta(seconds=expires_in),
                        'last_token_refresh': datetime.utcnow()
                    }
                }
            )

            logger.info(f"Refreshed Facebook token for account {account['account_id']}")

            return {
                'success': True,
                'access_token': new_token,
                'expires_in': expires_in
            }

        except Exception as e:
            logger.error(f"Error refreshing Facebook token: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _refresh_twitter_token(self, account: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refresh Twitter access token using refresh token

        Args:
            account: Account document from database

        Returns:
            dict: Refresh result
        """
        try:
            config = self.platform_configs['twitter']

            if 'refresh_token' not in account:
                return {
                    'success': False,
                    'error': 'No refresh token available'
                }

            data = {
                'grant_type': 'refresh_token',
                'refresh_token': account['refresh_token'],
                'client_id': config['client_id']
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    config['token_url'],
                    data=data,
                    auth=(config['client_id'], config['client_secret'])
                )
                response.raise_for_status()
                token_data = response.json()

            # Update account with new tokens
            new_access_token = token_data.get('access_token')
            new_refresh_token = token_data.get('refresh_token')
            expires_in = token_data.get('expires_in', config['token_lifetime'])

            update_data = {
                'access_token': new_access_token,
                'token_expires_at': datetime.utcnow() + timedelta(seconds=expires_in),
                'last_token_refresh': datetime.utcnow()
            }

            if new_refresh_token:
                update_data['refresh_token'] = new_refresh_token

            await self.social_accounts.update_one(
                {'_id': account['_id']},
                {'$set': update_data}
            )

            logger.info(f"Refreshed Twitter token for account {account['account_id']}")

            return {
                'success': True,
                'access_token': new_access_token,
                'expires_in': expires_in
            }

        except Exception as e:
            logger.error(f"Error refreshing Twitter token: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _refresh_linkedin_token(self, account: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refresh LinkedIn access token using refresh token

        Args:
            account: Account document from database

        Returns:
            dict: Refresh result
        """
        try:
            config = self.platform_configs['linkedin']

            if 'refresh_token' not in account:
                return {
                    'success': False,
                    'error': 'No refresh token available'
                }

            data = {
                'grant_type': 'refresh_token',
                'refresh_token': account['refresh_token'],
                'client_id': config['client_id'],
                'client_secret': config['client_secret']
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(config['token_url'], data=data)
                response.raise_for_status()
                token_data = response.json()

            # Update account with new tokens
            new_access_token = token_data.get('access_token')
            new_refresh_token = token_data.get('refresh_token')
            expires_in = token_data.get('expires_in', config['token_lifetime'])

            update_data = {
                'access_token': new_access_token,
                'token_expires_at': datetime.utcnow() + timedelta(seconds=expires_in),
                'last_token_refresh': datetime.utcnow()
            }

            if new_refresh_token:
                update_data['refresh_token'] = new_refresh_token

            await self.social_accounts.update_one(
                {'_id': account['_id']},
                {'$set': update_data}
            )

            logger.info(f"Refreshed LinkedIn token for account {account['account_id']}")

            return {
                'success': True,
                'access_token': new_access_token,
                'expires_in': expires_in
            }

        except Exception as e:
            logger.error(f"Error refreshing LinkedIn token: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def refresh_zoho_token(self, user_id: str) -> Dict[str, Any]:
        """
        Refresh Zoho access token using refresh token

        Args:
            user_id: User ID

        Returns:
            dict: Refresh result
        """
        try:
            # Get Zoho tokens from database
            token_doc = await self.zoho_tokens.find_one({'user_id': user_id})

            if not token_doc:
                return {
                    'success': False,
                    'error': 'No Zoho tokens found'
                }

            if 'refresh_token' not in token_doc:
                return {
                    'success': False,
                    'error': 'No refresh token available'
                }

            config = self.platform_configs['zoho']
            data_center = config['data_center']

            # Refresh token endpoint
            token_url = f"https://accounts.zoho.{data_center}/oauth/v2/token"

            data = {
                'grant_type': 'refresh_token',
                'client_id': config['client_id'],
                'client_secret': config['client_secret'],
                'refresh_token': token_doc['refresh_token']
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data)
                response.raise_for_status()
                token_data = response.json()

            # Update tokens in database
            new_access_token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', config['token_lifetime'])

            await self.zoho_tokens.update_one(
                {'_id': token_doc['_id']},
                {
                    '$set': {
                        'access_token': new_access_token,
                        'expires_at': datetime.utcnow() + timedelta(seconds=expires_in),
                        'last_refresh': datetime.utcnow()
                    }
                }
            )

            logger.info(f"Refreshed Zoho token for user {user_id}")

            return {
                'success': True,
                'access_token': new_access_token,
                'expires_in': expires_in
            }

        except Exception as e:
            logger.error(f"Error refreshing Zoho token: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== Token Validation & Auto-Refresh ====================

    async def get_valid_social_token(
        self,
        account_id: str,
        platform: str
    ) -> Dict[str, Any]:
        """
        Get valid access token, refreshing if necessary

        Args:
            account_id: Social account ID
            platform: Platform name

        Returns:
            dict: Token data or error
        """
        try:
            # Get account from database
            account = await self.social_accounts.find_one({'account_id': account_id})

            if not account:
                return {
                    'success': False,
                    'error': 'Account not found'
                }

            # Check if token is expired or about to expire (within 5 minutes)
            expires_at = account.get('token_expires_at')

            if expires_at:
                time_until_expiry = (expires_at - datetime.utcnow()).total_seconds()

                # Refresh if expired or expiring soon
                if time_until_expiry < 300:  # 5 minutes
                    logger.info(f"Token expiring soon for {account_id}, refreshing...")
                    refresh_result = await self.refresh_social_token(account_id, platform)

                    if refresh_result['success']:
                        return {
                            'success': True,
                            'access_token': refresh_result['access_token'],
                            'refreshed': True
                        }
                    else:
                        return {
                            'success': False,
                            'error': 'Token expired and refresh failed',
                            'details': refresh_result.get('error')
                        }

            # Token is still valid
            return {
                'success': True,
                'access_token': account['access_token'],
                'refreshed': False
            }

        except Exception as e:
            logger.error(f"Error getting valid token: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def get_valid_zoho_token(self, user_id: str) -> Dict[str, Any]:
        """
        Get valid Zoho access token, refreshing if necessary

        Args:
            user_id: User ID

        Returns:
            dict: Token data or error
        """
        try:
            # Get tokens from database
            token_doc = await self.zoho_tokens.find_one({'user_id': user_id})

            if not token_doc:
                return {
                    'success': False,
                    'error': 'No Zoho tokens found'
                }

            # Check if token is expired or about to expire (within 5 minutes)
            expires_at = token_doc.get('expires_at')

            if expires_at:
                time_until_expiry = (expires_at - datetime.utcnow()).total_seconds()

                # Refresh if expired or expiring soon
                if time_until_expiry < 300:  # 5 minutes
                    logger.info(f"Zoho token expiring soon for user {user_id}, refreshing...")
                    refresh_result = await self.refresh_zoho_token(user_id)

                    if refresh_result['success']:
                        return {
                            'success': True,
                            'access_token': refresh_result['access_token'],
                            'refreshed': True
                        }
                    else:
                        return {
                            'success': False,
                            'error': 'Token expired and refresh failed',
                            'details': refresh_result.get('error')
                        }

            # Token is still valid
            return {
                'success': True,
                'access_token': token_doc['access_token'],
                'refreshed': False
            }

        except Exception as e:
            logger.error(f"Error getting valid Zoho token: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== Batch Operations ====================

    async def refresh_expiring_tokens(self, hours_threshold: int = 24) -> Dict[str, Any]:
        """
        Batch refresh all tokens expiring within threshold

        Args:
            hours_threshold: Refresh tokens expiring within this many hours

        Returns:
            dict: Refresh summary
        """
        try:
            threshold_time = datetime.utcnow() + timedelta(hours=hours_threshold)

            # Find expiring social accounts
            expiring_accounts = await self.social_accounts.find({
                'token_expires_at': {
                    '$lt': threshold_time,
                    '$gt': datetime.utcnow()
                }
            }).to_list(length=None)

            # Find expiring Zoho tokens
            expiring_zoho = await self.zoho_tokens.find({
                'expires_at': {
                    '$lt': threshold_time,
                    '$gt': datetime.utcnow()
                }
            }).to_list(length=None)

            results = {
                'social_accounts': {
                    'total': len(expiring_accounts),
                    'success': 0,
                    'failed': 0
                },
                'zoho_tokens': {
                    'total': len(expiring_zoho),
                    'success': 0,
                    'failed': 0
                }
            }

            # Refresh social accounts
            for account in expiring_accounts:
                result = await self.refresh_social_token(
                    account['account_id'],
                    account['platform']
                )
                if result['success']:
                    results['social_accounts']['success'] += 1
                else:
                    results['social_accounts']['failed'] += 1

            # Refresh Zoho tokens
            for token_doc in expiring_zoho:
                result = await self.refresh_zoho_token(token_doc['user_id'])
                if result['success']:
                    results['zoho_tokens']['success'] += 1
                else:
                    results['zoho_tokens']['failed'] += 1

            logger.info(f"Batch token refresh completed: {results}")
            return results

        except Exception as e:
            logger.error(f"Error in batch token refresh: {str(e)}")
            return {
                'error': str(e)
            }

    async def get_token_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get status of all tokens for a user

        Args:
            user_id: User ID

        Returns:
            dict: Token status summary
        """
        try:
            # Get all social accounts
            social_accounts = await self.social_accounts.find({
                'user_id': user_id
            }).to_list(length=None)

            # Get Zoho token
            zoho_token = await self.zoho_tokens.find_one({'user_id': user_id})

            status = {
                'user_id': user_id,
                'social_accounts': [],
                'zoho': None
            }

            # Process social accounts
            for account in social_accounts:
                expires_at = account.get('token_expires_at')
                if expires_at:
                    time_until_expiry = (expires_at - datetime.utcnow()).total_seconds()
                    is_expired = time_until_expiry < 0
                    is_expiring_soon = 0 < time_until_expiry < 86400  # 24 hours
                else:
                    time_until_expiry = None
                    is_expired = False
                    is_expiring_soon = False

                status['social_accounts'].append({
                    'platform': account['platform'],
                    'account_id': account['account_id'],
                    'account_name': account.get('account_name', 'Unknown'),
                    'expires_at': expires_at.isoformat() if expires_at else None,
                    'time_until_expiry_seconds': time_until_expiry,
                    'is_expired': is_expired,
                    'is_expiring_soon': is_expiring_soon,
                    'last_refresh': account.get('last_token_refresh')
                })

            # Process Zoho token
            if zoho_token:
                expires_at = zoho_token.get('expires_at')
                if expires_at:
                    time_until_expiry = (expires_at - datetime.utcnow()).total_seconds()
                    is_expired = time_until_expiry < 0
                    is_expiring_soon = 0 < time_until_expiry < 3600  # 1 hour
                else:
                    time_until_expiry = None
                    is_expired = False
                    is_expiring_soon = False

                status['zoho'] = {
                    'expires_at': expires_at.isoformat() if expires_at else None,
                    'time_until_expiry_seconds': time_until_expiry,
                    'is_expired': is_expired,
                    'is_expiring_soon': is_expiring_soon,
                    'last_refresh': zoho_token.get('last_refresh')
                }

            return status

        except Exception as e:
            logger.error(f"Error getting token status: {str(e)}")
            return {
                'error': str(e)
            }
