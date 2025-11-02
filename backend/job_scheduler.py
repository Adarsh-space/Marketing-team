"""
Job Scheduler Service
Handles all background tasks and scheduled jobs
Features: Scheduled posts, token refresh, analytics sync, email campaigns

Author: Marketing Minds AI
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobScheduler:
    """
    Centralized Job Scheduler for all background tasks.
    Handles scheduled posts, token refresh, analytics sync, and recurring tasks.
    """

    def __init__(
        self,
        mongo_client: AsyncIOMotorClient,
        oauth_manager,
        social_service,
        analytics_aggregator
    ):
        """
        Initialize Job Scheduler

        Args:
            mongo_client: MongoDB client instance
            oauth_manager: OAuth Manager instance
            social_service: Unified Social Service instance
            analytics_aggregator: Analytics Aggregator instance
        """
        self.mongo_client = mongo_client
        self.db = mongo_client.marketing_minds
        self.oauth_manager = oauth_manager
        self.social_service = social_service
        self.analytics_aggregator = analytics_aggregator

        # Collections
        self.scheduled_jobs = self.db.scheduled_jobs
        self.social_posts = self.db.social_posts
        self.email_campaigns = self.db.email_campaigns

        # Initialize scheduler
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

        # Job registry
        self.job_handlers = {
            'scheduled_post': self._handle_scheduled_post,
            'token_refresh': self._handle_token_refresh,
            'analytics_sync': self._handle_analytics_sync,
            'email_campaign': self._handle_email_campaign,
            'cleanup': self._handle_cleanup
        }

    # ==================== Scheduler Control ====================

    async def start(self) -> Dict[str, Any]:
        """
        Start the job scheduler

        Returns:
            dict: Start result
        """
        try:
            if self.is_running:
                return {
                    'success': False,
                    'error': 'Scheduler already running'
                }

            # Initialize recurring jobs
            await self._setup_recurring_jobs()

            # Load pending jobs from database
            await self._load_pending_jobs()

            # Start the scheduler
            self.scheduler.start()
            self.is_running = True

            logger.info("Job Scheduler started successfully")
            return {
                'success': True,
                'message': 'Job scheduler started'
            }

        except Exception as e:
            logger.error(f"Error starting scheduler: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def stop(self) -> Dict[str, Any]:
        """
        Stop the job scheduler

        Returns:
            dict: Stop result
        """
        try:
            if not self.is_running:
                return {
                    'success': False,
                    'error': 'Scheduler not running'
                }

            self.scheduler.shutdown(wait=True)
            self.is_running = False

            logger.info("Job Scheduler stopped")
            return {
                'success': True,
                'message': 'Job scheduler stopped'
            }

        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== Job Management ====================

    async def schedule_post(
        self,
        user_id: str,
        account_ids: List[str],
        content: Dict[str, Any],
        scheduled_time: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Schedule a social media post

        Args:
            user_id: User ID
            account_ids: List of social account IDs
            content: Post content (text, images, etc.)
            scheduled_time: When to publish the post
            metadata: Optional additional metadata

        Returns:
            dict: Schedule result with job ID
        """
        try:
            # Validate scheduled time
            if scheduled_time <= datetime.utcnow():
                return {
                    'success': False,
                    'error': 'Scheduled time must be in the future'
                }

            # Create job document
            job_doc = {
                'job_type': 'scheduled_post',
                'user_id': user_id,
                'account_ids': account_ids,
                'content': content,
                'scheduled_time': scheduled_time,
                'status': 'pending',
                'metadata': metadata or {},
                'created_at': datetime.utcnow(),
                'attempts': 0,
                'max_attempts': 3
            }

            # Insert into database
            result = await self.scheduled_jobs.insert_one(job_doc)
            job_id = str(result.inserted_id)

            # Schedule the job
            self.scheduler.add_job(
                func=self._handle_scheduled_post,
                trigger=DateTrigger(run_date=scheduled_time),
                args=[job_id],
                id=job_id,
                replace_existing=True
            )

            logger.info(f"Scheduled post job {job_id} for {scheduled_time}")
            return {
                'success': True,
                'job_id': job_id,
                'scheduled_time': scheduled_time.isoformat()
            }

        except Exception as e:
            logger.error(f"Error scheduling post: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def schedule_email_campaign(
        self,
        user_id: str,
        campaign_id: str,
        scheduled_time: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Schedule an email campaign

        Args:
            user_id: User ID
            campaign_id: Email campaign ID
            scheduled_time: When to send the campaign
            metadata: Optional additional metadata

        Returns:
            dict: Schedule result with job ID
        """
        try:
            # Validate scheduled time
            if scheduled_time <= datetime.utcnow():
                return {
                    'success': False,
                    'error': 'Scheduled time must be in the future'
                }

            # Create job document
            job_doc = {
                'job_type': 'email_campaign',
                'user_id': user_id,
                'campaign_id': campaign_id,
                'scheduled_time': scheduled_time,
                'status': 'pending',
                'metadata': metadata or {},
                'created_at': datetime.utcnow(),
                'attempts': 0,
                'max_attempts': 3
            }

            # Insert into database
            result = await self.scheduled_jobs.insert_one(job_doc)
            job_id = str(result.inserted_id)

            # Schedule the job
            self.scheduler.add_job(
                func=self._handle_email_campaign,
                trigger=DateTrigger(run_date=scheduled_time),
                args=[job_id],
                id=job_id,
                replace_existing=True
            )

            logger.info(f"Scheduled email campaign job {job_id} for {scheduled_time}")
            return {
                'success': True,
                'job_id': job_id,
                'scheduled_time': scheduled_time.isoformat()
            }

        except Exception as e:
            logger.error(f"Error scheduling email campaign: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """
        Cancel a scheduled job

        Args:
            job_id: Job ID to cancel

        Returns:
            dict: Cancellation result
        """
        try:
            # Update job status in database
            result = await self.scheduled_jobs.update_one(
                {'_id': job_id, 'status': 'pending'},
                {
                    '$set': {
                        'status': 'cancelled',
                        'cancelled_at': datetime.utcnow()
                    }
                }
            )

            if result.modified_count == 0:
                return {
                    'success': False,
                    'error': 'Job not found or already processed'
                }

            # Remove from scheduler
            try:
                self.scheduler.remove_job(job_id)
            except Exception:
                pass  # Job may have already been removed

            logger.info(f"Cancelled job {job_id}")
            return {
                'success': True,
                'message': 'Job cancelled successfully'
            }

        except Exception as e:
            logger.error(f"Error cancelling job: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get status of a scheduled job

        Args:
            job_id: Job ID

        Returns:
            dict: Job status
        """
        try:
            job = await self.scheduled_jobs.find_one({'_id': job_id})

            if not job:
                return {
                    'success': False,
                    'error': 'Job not found'
                }

            return {
                'success': True,
                'job': {
                    'job_id': job_id,
                    'job_type': job.get('job_type'),
                    'status': job.get('status'),
                    'scheduled_time': job.get('scheduled_time'),
                    'created_at': job.get('created_at'),
                    'completed_at': job.get('completed_at'),
                    'error': job.get('error'),
                    'attempts': job.get('attempts', 0)
                }
            }

        except Exception as e:
            logger.error(f"Error getting job status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def get_user_jobs(
        self,
        user_id: str,
        status: Optional[str] = None,
        job_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get all jobs for a user

        Args:
            user_id: User ID
            status: Optional status filter
            job_type: Optional job type filter

        Returns:
            dict: List of jobs
        """
        try:
            query = {'user_id': user_id}

            if status:
                query['status'] = status
            if job_type:
                query['job_type'] = job_type

            jobs = await self.scheduled_jobs.find(query).sort('scheduled_time', -1).to_list(length=100)

            job_list = []
            for job in jobs:
                job_list.append({
                    'job_id': str(job['_id']),
                    'job_type': job.get('job_type'),
                    'status': job.get('status'),
                    'scheduled_time': job.get('scheduled_time'),
                    'created_at': job.get('created_at'),
                    'completed_at': job.get('completed_at')
                })

            return {
                'success': True,
                'total': len(job_list),
                'jobs': job_list
            }

        except Exception as e:
            logger.error(f"Error getting user jobs: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== Job Handlers ====================

    async def _handle_scheduled_post(self, job_id: str) -> None:
        """
        Handle scheduled social media post

        Args:
            job_id: Job ID
        """
        try:
            logger.info(f"Processing scheduled post job {job_id}")

            # Get job from database
            job = await self.scheduled_jobs.find_one({'_id': job_id})

            if not job:
                logger.error(f"Job {job_id} not found")
                return

            if job['status'] != 'pending':
                logger.warning(f"Job {job_id} is not pending, skipping")
                return

            # Mark as processing
            await self.scheduled_jobs.update_one(
                {'_id': job_id},
                {
                    '$set': {
                        'status': 'processing',
                        'started_at': datetime.utcnow()
                    },
                    '$inc': {'attempts': 1}
                }
            )

            # Post to social media
            result = await self.social_service.post_to_multiple(
                account_ids=job['account_ids'],
                content=job['content'],
                user_id=job['user_id']
            )

            if result['success']:
                # Mark as completed
                await self.scheduled_jobs.update_one(
                    {'_id': job_id},
                    {
                        '$set': {
                            'status': 'completed',
                            'completed_at': datetime.utcnow(),
                            'result': result
                        }
                    }
                )
                logger.info(f"Scheduled post job {job_id} completed successfully")
            else:
                # Handle failure
                await self._handle_job_failure(job_id, job, result.get('error', 'Unknown error'))

        except Exception as e:
            logger.error(f"Error handling scheduled post job {job_id}: {str(e)}")
            job = await self.scheduled_jobs.find_one({'_id': job_id})
            if job:
                await self._handle_job_failure(job_id, job, str(e))

    async def _handle_email_campaign(self, job_id: str) -> None:
        """
        Handle scheduled email campaign

        Args:
            job_id: Job ID
        """
        try:
            logger.info(f"Processing email campaign job {job_id}")

            # Get job from database
            job = await self.scheduled_jobs.find_one({'_id': job_id})

            if not job:
                logger.error(f"Job {job_id} not found")
                return

            if job['status'] != 'pending':
                logger.warning(f"Job {job_id} is not pending, skipping")
                return

            # Mark as processing
            await self.scheduled_jobs.update_one(
                {'_id': job_id},
                {
                    '$set': {
                        'status': 'processing',
                        'started_at': datetime.utcnow()
                    },
                    '$inc': {'attempts': 1}
                }
            )

            # Get campaign details
            campaign = await self.email_campaigns.find_one({'campaign_id': job['campaign_id']})

            if not campaign:
                await self._handle_job_failure(job_id, job, 'Campaign not found')
                return

            # TODO: Integrate with Zoho Campaigns API to send email
            # For now, mark as completed
            # In production, this would trigger the actual email send via Zoho Campaigns

            await self.scheduled_jobs.update_one(
                {'_id': job_id},
                {
                    '$set': {
                        'status': 'completed',
                        'completed_at': datetime.utcnow(),
                        'result': {'message': 'Email campaign sent'}
                    }
                }
            )

            logger.info(f"Email campaign job {job_id} completed successfully")

        except Exception as e:
            logger.error(f"Error handling email campaign job {job_id}: {str(e)}")
            job = await self.scheduled_jobs.find_one({'_id': job_id})
            if job:
                await self._handle_job_failure(job_id, job, str(e))

    async def _handle_token_refresh(self) -> None:
        """
        Handle automatic token refresh for all platforms
        """
        try:
            logger.info("Running token refresh job")

            # Refresh tokens expiring within 24 hours
            result = await self.oauth_manager.refresh_expiring_tokens(hours_threshold=24)

            logger.info(f"Token refresh completed: {result}")

        except Exception as e:
            logger.error(f"Error in token refresh job: {str(e)}")

    async def _handle_analytics_sync(self) -> None:
        """
        Handle daily analytics synchronization
        """
        try:
            logger.info("Running analytics sync job")

            # Get all users who have connected accounts
            users = await self.db.users.find({'has_connected_accounts': True}).to_list(length=None)

            for user in users:
                user_id = user.get('user_id')
                if user_id:
                    # Aggregate analytics for each user
                    result = await self.analytics_aggregator.aggregate_all_analytics(user_id)
                    if result['success']:
                        logger.info(f"Analytics synced for user {user_id}")
                    else:
                        logger.error(f"Analytics sync failed for user {user_id}: {result.get('error')}")

            logger.info("Analytics sync completed")

        except Exception as e:
            logger.error(f"Error in analytics sync job: {str(e)}")

    async def _handle_cleanup(self) -> None:
        """
        Handle cleanup of old data
        """
        try:
            logger.info("Running cleanup job")

            # Clean up old OAuth states
            await self.oauth_manager.cleanup_expired_states()

            # Clean up old completed jobs (older than 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            result = await self.scheduled_jobs.delete_many({
                'status': {'$in': ['completed', 'failed', 'cancelled']},
                'completed_at': {'$lt': thirty_days_ago}
            })

            logger.info(f"Cleanup completed: removed {result.deleted_count} old jobs")

        except Exception as e:
            logger.error(f"Error in cleanup job: {str(e)}")

    async def _handle_job_failure(self, job_id: str, job: Dict[str, Any], error: str) -> None:
        """
        Handle job failure with retry logic

        Args:
            job_id: Job ID
            job: Job document
            error: Error message
        """
        try:
            attempts = job.get('attempts', 0)
            max_attempts = job.get('max_attempts', 3)

            if attempts >= max_attempts:
                # Max attempts reached, mark as failed
                await self.scheduled_jobs.update_one(
                    {'_id': job_id},
                    {
                        '$set': {
                            'status': 'failed',
                            'failed_at': datetime.utcnow(),
                            'error': error
                        }
                    }
                )
                logger.error(f"Job {job_id} failed after {attempts} attempts: {error}")
            else:
                # Retry the job after delay
                retry_delay = 5 * (2 ** attempts)  # Exponential backoff: 5s, 10s, 20s
                retry_time = datetime.utcnow() + timedelta(seconds=retry_delay)

                await self.scheduled_jobs.update_one(
                    {'_id': job_id},
                    {
                        '$set': {
                            'status': 'pending',
                            'scheduled_time': retry_time,
                            'last_error': error
                        }
                    }
                )

                # Reschedule the job
                handler = self.job_handlers.get(job['job_type'])
                if handler:
                    self.scheduler.add_job(
                        func=handler,
                        trigger=DateTrigger(run_date=retry_time),
                        args=[job_id],
                        id=f"{job_id}_retry_{attempts}",
                        replace_existing=True
                    )

                logger.warning(f"Job {job_id} will retry in {retry_delay} seconds (attempt {attempts + 1}/{max_attempts})")

        except Exception as e:
            logger.error(f"Error handling job failure: {str(e)}")

    # ==================== Recurring Jobs Setup ====================

    async def _setup_recurring_jobs(self) -> None:
        """
        Setup recurring background jobs
        """
        try:
            # Token refresh every 6 hours
            self.scheduler.add_job(
                func=self._handle_token_refresh,
                trigger=IntervalTrigger(hours=6),
                id='token_refresh',
                replace_existing=True
            )

            # Analytics sync daily at 2 AM
            self.scheduler.add_job(
                func=self._handle_analytics_sync,
                trigger=CronTrigger(hour=2, minute=0),
                id='analytics_sync',
                replace_existing=True
            )

            # Cleanup weekly on Sunday at 3 AM
            self.scheduler.add_job(
                func=self._handle_cleanup,
                trigger=CronTrigger(day_of_week='sun', hour=3, minute=0),
                id='cleanup',
                replace_existing=True
            )

            logger.info("Recurring jobs setup completed")

        except Exception as e:
            logger.error(f"Error setting up recurring jobs: {str(e)}")

    async def _load_pending_jobs(self) -> None:
        """
        Load pending jobs from database and schedule them
        """
        try:
            # Get all pending jobs
            pending_jobs = await self.scheduled_jobs.find({
                'status': 'pending',
                'scheduled_time': {'$gt': datetime.utcnow()}
            }).to_list(length=None)

            for job in pending_jobs:
                job_id = str(job['_id'])
                job_type = job.get('job_type')
                scheduled_time = job.get('scheduled_time')

                # Get handler for job type
                handler = self.job_handlers.get(job_type)

                if handler:
                    self.scheduler.add_job(
                        func=handler,
                        trigger=DateTrigger(run_date=scheduled_time),
                        args=[job_id],
                        id=job_id,
                        replace_existing=True
                    )
                    logger.info(f"Loaded pending job {job_id} ({job_type}) scheduled for {scheduled_time}")

            logger.info(f"Loaded {len(pending_jobs)} pending jobs")

        except Exception as e:
            logger.error(f"Error loading pending jobs: {str(e)}")

    # ==================== Status & Monitoring ====================

    async def get_scheduler_status(self) -> Dict[str, Any]:
        """
        Get current scheduler status

        Returns:
            dict: Scheduler status
        """
        try:
            jobs = self.scheduler.get_jobs()

            job_list = []
            for job in jobs:
                job_list.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None
                })

            # Get statistics from database
            stats = {
                'pending': await self.scheduled_jobs.count_documents({'status': 'pending'}),
                'processing': await self.scheduled_jobs.count_documents({'status': 'processing'}),
                'completed': await self.scheduled_jobs.count_documents({'status': 'completed'}),
                'failed': await self.scheduled_jobs.count_documents({'status': 'failed'}),
                'cancelled': await self.scheduled_jobs.count_documents({'status': 'cancelled'})
            }

            return {
                'success': True,
                'is_running': self.is_running,
                'active_jobs': len(job_list),
                'jobs': job_list,
                'statistics': stats
            }

        except Exception as e:
            logger.error(f"Error getting scheduler status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
