"""
Analytics Aggregator Service
Collects and aggregates analytics from all platforms
Supports: Social Media, Zoho CRM, Zoho Campaigns, Zoho Analytics

Author: Marketing Minds AI
"""

import os
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


class AnalyticsAggregator:
    """
    Centralized Analytics Aggregator for all platform integrations.
    Collects data from social media, Zoho services, and stores unified metrics.
    """

    def __init__(self, mongo_client: AsyncIOMotorClient, oauth_manager):
        """
        Initialize Analytics Aggregator

        Args:
            mongo_client: MongoDB client instance
            oauth_manager: OAuth Manager instance for token management
        """
        self.mongo_client = mongo_client
        self.db = mongo_client.marketing_minds
        self.oauth_manager = oauth_manager

        # Collections
        self.social_accounts = self.db.social_accounts
        self.social_posts = self.db.social_posts
        self.analytics_data = self.db.analytics_data
        self.campaigns = self.db.campaigns
        self.email_campaigns = self.db.email_campaigns
        self.zoho_crm_records = self.db.zoho_crm_records

    # ==================== Social Media Analytics ====================

    async def fetch_facebook_insights(
        self,
        account_id: str,
        post_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Fetch Facebook page or post insights

        Args:
            account_id: Facebook account ID
            post_id: Optional specific post ID
            date_from: Start date for metrics
            date_to: End date for metrics

        Returns:
            dict: Facebook insights data
        """
        try:
            # Get account
            account = await self.social_accounts.find_one({'account_id': account_id})
            if not account:
                return {'success': False, 'error': 'Account not found'}

            # Get valid token
            token_result = await self.oauth_manager.get_valid_social_token(account_id, 'facebook')
            if not token_result['success']:
                return {'success': False, 'error': 'Invalid token'}

            access_token = token_result['access_token']

            # Determine what insights to fetch
            if post_id:
                # Fetch specific post insights
                url = f"https://graph.facebook.com/v18.0/{post_id}/insights"
                metrics = [
                    'post_impressions',
                    'post_engaged_users',
                    'post_clicks',
                    'post_reactions_by_type_total'
                ]
            else:
                # Fetch page insights
                page_id = account.get('page_id', account_id)
                url = f"https://graph.facebook.com/v18.0/{page_id}/insights"
                metrics = [
                    'page_impressions',
                    'page_engaged_users',
                    'page_post_engagements',
                    'page_fans',
                    'page_fan_adds',
                    'page_views_total'
                ]

            params = {
                'access_token': access_token,
                'metric': ','.join(metrics)
            }

            # Add date range if provided
            if date_from:
                params['since'] = int(date_from.timestamp())
            if date_to:
                params['until'] = int(date_to.timestamp())

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            insights = {}
            for item in data.get('data', []):
                metric_name = item.get('name')
                values = item.get('values', [])
                if values:
                    insights[metric_name] = values[-1].get('value', 0)

            # Store in analytics collection
            await self._store_analytics('facebook', account_id, insights, post_id)

            logger.info(f"Fetched Facebook insights for account {account_id}")
            return {
                'success': True,
                'platform': 'facebook',
                'account_id': account_id,
                'post_id': post_id,
                'insights': insights
            }

        except Exception as e:
            logger.error(f"Error fetching Facebook insights: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def fetch_instagram_insights(
        self,
        account_id: str,
        post_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Fetch Instagram business account or post insights

        Args:
            account_id: Instagram account ID
            post_id: Optional specific post ID
            date_from: Start date for metrics
            date_to: End date for metrics

        Returns:
            dict: Instagram insights data
        """
        try:
            # Get account
            account = await self.social_accounts.find_one({'account_id': account_id})
            if not account:
                return {'success': False, 'error': 'Account not found'}

            # Get valid token
            token_result = await self.oauth_manager.get_valid_social_token(account_id, 'instagram')
            if not token_result['success']:
                return {'success': False, 'error': 'Invalid token'}

            access_token = token_result['access_token']

            # Determine what insights to fetch
            if post_id:
                # Fetch specific post insights
                url = f"https://graph.facebook.com/v18.0/{post_id}/insights"
                metrics = [
                    'impressions',
                    'reach',
                    'engagement',
                    'saved',
                    'likes',
                    'comments'
                ]
            else:
                # Fetch account insights
                instagram_id = account.get('instagram_business_account_id', account_id)
                url = f"https://graph.facebook.com/v18.0/{instagram_id}/insights"
                metrics = [
                    'impressions',
                    'reach',
                    'profile_views',
                    'follower_count',
                    'website_clicks'
                ]

            params = {
                'access_token': access_token,
                'metric': ','.join(metrics)
            }

            # Add date range if provided
            if date_from:
                params['since'] = int(date_from.timestamp())
            if date_to:
                params['until'] = int(date_to.timestamp())

            # Add period for account-level metrics
            if not post_id:
                params['period'] = 'day'

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            insights = {}
            for item in data.get('data', []):
                metric_name = item.get('name')
                values = item.get('values', [])
                if values:
                    insights[metric_name] = values[-1].get('value', 0)

            # Store in analytics collection
            await self._store_analytics('instagram', account_id, insights, post_id)

            logger.info(f"Fetched Instagram insights for account {account_id}")
            return {
                'success': True,
                'platform': 'instagram',
                'account_id': account_id,
                'post_id': post_id,
                'insights': insights
            }

        except Exception as e:
            logger.error(f"Error fetching Instagram insights: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def fetch_twitter_analytics(
        self,
        account_id: str,
        tweet_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch Twitter analytics for tweets

        Args:
            account_id: Twitter account ID
            tweet_id: Optional specific tweet ID

        Returns:
            dict: Twitter analytics data
        """
        try:
            # Get account
            account = await self.social_accounts.find_one({'account_id': account_id})
            if not account:
                return {'success': False, 'error': 'Account not found'}

            # Get valid token
            token_result = await self.oauth_manager.get_valid_social_token(account_id, 'twitter')
            if not token_result['success']:
                return {'success': False, 'error': 'Invalid token'}

            access_token = token_result['access_token']

            if tweet_id:
                # Fetch specific tweet metrics
                url = f"https://api.twitter.com/2/tweets/{tweet_id}"
                params = {
                    'tweet.fields': 'public_metrics,non_public_metrics,organic_metrics'
                }
            else:
                # Fetch user's recent tweets with metrics
                user_id = account.get('twitter_user_id', account_id)
                url = f"https://api.twitter.com/2/users/{user_id}/tweets"
                params = {
                    'tweet.fields': 'public_metrics',
                    'max_results': 10
                }

            headers = {
                'Authorization': f'Bearer {access_token}'
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()

            # Process metrics
            if tweet_id:
                tweet_data = data.get('data', {})
                metrics = tweet_data.get('public_metrics', {})
                insights = {
                    'retweet_count': metrics.get('retweet_count', 0),
                    'reply_count': metrics.get('reply_count', 0),
                    'like_count': metrics.get('like_count', 0),
                    'quote_count': metrics.get('quote_count', 0),
                    'impression_count': metrics.get('impression_count', 0)
                }
            else:
                # Aggregate metrics from recent tweets
                tweets = data.get('data', [])
                insights = {
                    'total_tweets': len(tweets),
                    'total_retweets': sum(t.get('public_metrics', {}).get('retweet_count', 0) for t in tweets),
                    'total_likes': sum(t.get('public_metrics', {}).get('like_count', 0) for t in tweets),
                    'total_replies': sum(t.get('public_metrics', {}).get('reply_count', 0) for t in tweets),
                    'total_quotes': sum(t.get('public_metrics', {}).get('quote_count', 0) for t in tweets)
                }

            # Store in analytics collection
            await self._store_analytics('twitter', account_id, insights, tweet_id)

            logger.info(f"Fetched Twitter analytics for account {account_id}")
            return {
                'success': True,
                'platform': 'twitter',
                'account_id': account_id,
                'tweet_id': tweet_id,
                'insights': insights
            }

        except Exception as e:
            logger.error(f"Error fetching Twitter analytics: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def fetch_linkedin_analytics(
        self,
        account_id: str,
        post_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch LinkedIn analytics

        Args:
            account_id: LinkedIn account ID
            post_id: Optional specific post ID (UGC post URN)

        Returns:
            dict: LinkedIn analytics data
        """
        try:
            # Get account
            account = await self.social_accounts.find_one({'account_id': account_id})
            if not account:
                return {'success': False, 'error': 'Account not found'}

            # Get valid token
            token_result = await self.oauth_manager.get_valid_social_token(account_id, 'linkedin')
            if not token_result['success']:
                return {'success': False, 'error': 'Invalid token'}

            access_token = token_result['access_token']

            headers = {
                'Authorization': f'Bearer {access_token}',
                'X-Restli-Protocol-Version': '2.0.0'
            }

            if post_id:
                # Fetch specific post statistics
                url = f"https://api.linkedin.com/v2/socialActions/{post_id}"

                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()
                    data = response.json()

                insights = {
                    'likes': data.get('likesSummary', {}).get('totalLikes', 0),
                    'comments': data.get('commentsSummary', {}).get('totalComments', 0),
                    'shares': data.get('sharesSummary', {}).get('totalShares', 0)
                }
            else:
                # Fetch organization statistics (if it's an organization page)
                org_id = account.get('linkedin_org_id')
                if not org_id:
                    return {'success': False, 'error': 'No organization ID found'}

                url = f"https://api.linkedin.com/v2/organizationalEntityShareStatistics"
                params = {
                    'q': 'organizationalEntity',
                    'organizationalEntity': org_id
                }

                async with httpx.AsyncClient() as client:
                    response = await client.get(url, params=params, headers=headers)
                    response.raise_for_status()
                    data = response.json()

                # Aggregate statistics
                elements = data.get('elements', [])
                insights = {
                    'total_share_count': sum(e.get('totalShareStatistics', {}).get('shareCount', 0) for e in elements),
                    'total_engagement': sum(e.get('totalShareStatistics', {}).get('engagement', 0) for e in elements),
                    'total_impressions': sum(e.get('totalShareStatistics', {}).get('impressionCount', 0) for e in elements)
                }

            # Store in analytics collection
            await self._store_analytics('linkedin', account_id, insights, post_id)

            logger.info(f"Fetched LinkedIn analytics for account {account_id}")
            return {
                'success': True,
                'platform': 'linkedin',
                'account_id': account_id,
                'post_id': post_id,
                'insights': insights
            }

        except Exception as e:
            logger.error(f"Error fetching LinkedIn analytics: {str(e)}")
            return {'success': False, 'error': str(e)}

    # ==================== Zoho Analytics ====================

    async def fetch_zoho_crm_analytics(
        self,
        user_id: str,
        module: str = 'Leads',
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Fetch Zoho CRM analytics

        Args:
            user_id: User ID
            module: CRM module (Leads, Contacts, Deals, etc.)
            date_from: Start date
            date_to: End date

        Returns:
            dict: CRM analytics data
        """
        try:
            # Get valid Zoho token
            token_result = await self.oauth_manager.get_valid_zoho_token(user_id)
            if not token_result['success']:
                return {'success': False, 'error': 'Invalid Zoho token'}

            access_token = token_result['access_token']
            data_center = os.getenv('ZOHO_DATA_CENTER', 'com')

            # Fetch records with filters
            url = f"https://www.zohoapis.{data_center}/crm/v2/{module}"

            headers = {
                'Authorization': f'Bearer {access_token}'
            }

            params = {}
            if date_from:
                params['criteria'] = f"(Created_Time:greater_equal:{date_from.isoformat()})"
            if date_to:
                if 'criteria' in params:
                    params['criteria'] += f" and (Created_Time:less_equal:{date_to.isoformat()})"
                else:
                    params['criteria'] = f"(Created_Time:less_equal:{date_to.isoformat()})"

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()

            records = data.get('data', [])

            # Calculate analytics
            insights = {
                'total_records': len(records),
                'module': module
            }

            # Module-specific analytics
            if module == 'Leads':
                status_counts = {}
                source_counts = {}
                for lead in records:
                    status = lead.get('Lead_Status', 'Unknown')
                    source = lead.get('Lead_Source', 'Unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                    source_counts[source] = source_counts.get(source, 0) + 1

                insights['by_status'] = status_counts
                insights['by_source'] = source_counts

            elif module == 'Deals':
                stage_counts = {}
                total_amount = 0
                for deal in records:
                    stage = deal.get('Stage', 'Unknown')
                    amount = deal.get('Amount', 0)
                    stage_counts[stage] = stage_counts.get(stage, 0) + 1
                    total_amount += amount

                insights['by_stage'] = stage_counts
                insights['total_deal_value'] = total_amount

            # Store in analytics collection
            await self._store_analytics('zoho_crm', user_id, insights, module)

            logger.info(f"Fetched Zoho CRM analytics for user {user_id}, module {module}")
            return {
                'success': True,
                'platform': 'zoho_crm',
                'user_id': user_id,
                'module': module,
                'insights': insights
            }

        except Exception as e:
            logger.error(f"Error fetching Zoho CRM analytics: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def fetch_zoho_campaigns_analytics(
        self,
        user_id: str,
        campaign_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch Zoho Campaigns email analytics

        Args:
            user_id: User ID
            campaign_key: Optional specific campaign key

        Returns:
            dict: Email campaign analytics
        """
        try:
            # Get valid Zoho token
            token_result = await self.oauth_manager.get_valid_zoho_token(user_id)
            if not token_result['success']:
                return {'success': False, 'error': 'Invalid Zoho token'}

            access_token = token_result['access_token']
            data_center = os.getenv('ZOHO_DATA_CENTER', 'com')

            headers = {
                'Authorization': f'Bearer {access_token}'
            }

            if campaign_key:
                # Fetch specific campaign stats
                url = f"https://campaigns.zoho.{data_center}/api/v1.1/getcampaignstats"
                params = {'campaignkey': campaign_key}

                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=headers, params=params)
                    response.raise_for_status()
                    data = response.json()

                stats = data.get('campaign_stats', {})
                insights = {
                    'campaign_key': campaign_key,
                    'sent': stats.get('sentcount', 0),
                    'opens': stats.get('uniqueopens', 0),
                    'clicks': stats.get('uniqueclicks', 0),
                    'bounces': stats.get('bouncecount', 0),
                    'unsubscribes': stats.get('unsubcount', 0),
                    'open_rate': stats.get('openrate', 0),
                    'click_rate': stats.get('clickrate', 0)
                }
            else:
                # Fetch all campaigns summary
                url = f"https://campaigns.zoho.{data_center}/api/v1.1/getallcampaigns"

                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()
                    data = response.json()

                campaigns = data.get('campaigns', [])
                insights = {
                    'total_campaigns': len(campaigns),
                    'total_sent': sum(c.get('sentcount', 0) for c in campaigns),
                    'total_opens': sum(c.get('uniqueopens', 0) for c in campaigns),
                    'total_clicks': sum(c.get('uniqueclicks', 0) for c in campaigns),
                    'total_bounces': sum(c.get('bouncecount', 0) for c in campaigns),
                    'total_unsubscribes': sum(c.get('unsubcount', 0) for c in campaigns)
                }

                if insights['total_sent'] > 0:
                    insights['avg_open_rate'] = (insights['total_opens'] / insights['total_sent']) * 100
                    insights['avg_click_rate'] = (insights['total_clicks'] / insights['total_sent']) * 100

            # Store in analytics collection
            await self._store_analytics('zoho_campaigns', user_id, insights, campaign_key)

            logger.info(f"Fetched Zoho Campaigns analytics for user {user_id}")
            return {
                'success': True,
                'platform': 'zoho_campaigns',
                'user_id': user_id,
                'campaign_key': campaign_key,
                'insights': insights
            }

        except Exception as e:
            logger.error(f"Error fetching Zoho Campaigns analytics: {str(e)}")
            return {'success': False, 'error': str(e)}

    # ==================== Unified Analytics ====================

    async def aggregate_all_analytics(
        self,
        user_id: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Aggregate analytics from all platforms for a user

        Args:
            user_id: User ID
            date_from: Start date
            date_to: End date

        Returns:
            dict: Unified analytics summary
        """
        try:
            if not date_from:
                date_from = datetime.utcnow() - timedelta(days=30)
            if not date_to:
                date_to = datetime.utcnow()

            # Fetch from all platforms
            results = {
                'user_id': user_id,
                'date_from': date_from.isoformat(),
                'date_to': date_to.isoformat(),
                'social_media': {},
                'zoho': {},
                'summary': {}
            }

            # Get all social accounts
            accounts = await self.social_accounts.find({'user_id': user_id}).to_list(length=None)

            for account in accounts:
                platform = account['platform']
                account_id = account['account_id']

                if platform == 'facebook':
                    fb_result = await self.fetch_facebook_insights(account_id, None, date_from, date_to)
                    if fb_result['success']:
                        results['social_media']['facebook'] = fb_result['insights']

                elif platform == 'instagram':
                    ig_result = await self.fetch_instagram_insights(account_id, None, date_from, date_to)
                    if ig_result['success']:
                        results['social_media']['instagram'] = ig_result['insights']

                elif platform == 'twitter':
                    tw_result = await self.fetch_twitter_analytics(account_id)
                    if tw_result['success']:
                        results['social_media']['twitter'] = tw_result['insights']

                elif platform == 'linkedin':
                    li_result = await self.fetch_linkedin_analytics(account_id)
                    if li_result['success']:
                        results['social_media']['linkedin'] = li_result['insights']

            # Fetch Zoho analytics
            crm_result = await self.fetch_zoho_crm_analytics(user_id, 'Leads', date_from, date_to)
            if crm_result['success']:
                results['zoho']['crm_leads'] = crm_result['insights']

            campaigns_result = await self.fetch_zoho_campaigns_analytics(user_id)
            if campaigns_result['success']:
                results['zoho']['email_campaigns'] = campaigns_result['insights']

            # Create summary
            results['summary'] = await self._create_unified_summary(results)

            # Store aggregated analytics
            await self.analytics_data.insert_one({
                'user_id': user_id,
                'type': 'unified_summary',
                'date_from': date_from,
                'date_to': date_to,
                'data': results,
                'created_at': datetime.utcnow()
            })

            logger.info(f"Aggregated all analytics for user {user_id}")
            return {
                'success': True,
                'data': results
            }

        except Exception as e:
            logger.error(f"Error aggregating analytics: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def _create_unified_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create unified summary from all analytics data

        Args:
            results: Analytics results from all platforms

        Returns:
            dict: Unified summary
        """
        summary = {
            'total_social_impressions': 0,
            'total_social_engagement': 0,
            'total_social_followers': 0,
            'total_email_sent': 0,
            'total_email_opens': 0,
            'total_leads': 0,
            'platforms_connected': len(results.get('social_media', {}))
        }

        # Aggregate social media metrics
        social = results.get('social_media', {})

        # Facebook
        if 'facebook' in social:
            fb = social['facebook']
            summary['total_social_impressions'] += fb.get('page_impressions', 0)
            summary['total_social_engagement'] += fb.get('page_post_engagements', 0)
            summary['total_social_followers'] += fb.get('page_fans', 0)

        # Instagram
        if 'instagram' in social:
            ig = social['instagram']
            summary['total_social_impressions'] += ig.get('impressions', 0)
            summary['total_social_engagement'] += ig.get('engagement', 0)
            summary['total_social_followers'] += ig.get('follower_count', 0)

        # Twitter
        if 'twitter' in social:
            tw = social['twitter']
            summary['total_social_engagement'] += (
                tw.get('total_likes', 0) +
                tw.get('total_retweets', 0) +
                tw.get('total_replies', 0)
            )

        # LinkedIn
        if 'linkedin' in social:
            li = social['linkedin']
            summary['total_social_impressions'] += li.get('total_impressions', 0)
            summary['total_social_engagement'] += li.get('total_engagement', 0)

        # Aggregate Zoho metrics
        zoho = results.get('zoho', {})

        # Email campaigns
        if 'email_campaigns' in zoho:
            email = zoho['email_campaigns']
            summary['total_email_sent'] = email.get('total_sent', 0)
            summary['total_email_opens'] = email.get('total_opens', 0)

        # CRM leads
        if 'crm_leads' in zoho:
            crm = zoho['crm_leads']
            summary['total_leads'] = crm.get('total_records', 0)

        # Calculate rates
        if summary['total_email_sent'] > 0:
            summary['email_open_rate'] = (summary['total_email_opens'] / summary['total_email_sent']) * 100

        if summary['total_social_impressions'] > 0:
            summary['social_engagement_rate'] = (summary['total_social_engagement'] / summary['total_social_impressions']) * 100

        return summary

    # ==================== Helper Methods ====================

    async def _store_analytics(
        self,
        platform: str,
        identifier: str,
        insights: Dict[str, Any],
        context_id: Optional[str] = None
    ) -> None:
        """
        Store analytics data in database

        Args:
            platform: Platform name
            identifier: Account ID or user ID
            insights: Analytics insights
            context_id: Optional context (post_id, campaign_id, etc.)
        """
        try:
            doc = {
                'platform': platform,
                'identifier': identifier,
                'context_id': context_id,
                'insights': insights,
                'created_at': datetime.utcnow(),
                'date': datetime.utcnow().date().isoformat()
            }

            await self.analytics_data.insert_one(doc)

        except Exception as e:
            logger.error(f"Error storing analytics: {str(e)}")

    async def get_analytics_history(
        self,
        user_id: str,
        platform: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get historical analytics data

        Args:
            user_id: User ID
            platform: Optional platform filter
            days: Number of days of history

        Returns:
            dict: Historical analytics
        """
        try:
            date_from = datetime.utcnow() - timedelta(days=days)

            query = {
                'created_at': {'$gte': date_from}
            }

            if platform:
                query['platform'] = platform

            # Get all analytics records
            records = await self.analytics_data.find(query).sort('created_at', -1).to_list(length=None)

            # Group by date
            by_date = {}
            for record in records:
                date_key = record['date']
                if date_key not in by_date:
                    by_date[date_key] = []
                by_date[date_key].append(record)

            return {
                'success': True,
                'user_id': user_id,
                'platform': platform,
                'days': days,
                'total_records': len(records),
                'by_date': by_date
            }

        except Exception as e:
            logger.error(f"Error getting analytics history: {str(e)}")
            return {'success': False, 'error': str(e)}
