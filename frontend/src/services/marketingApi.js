/**
 * Marketing Minds AI - Complete API Service
 * Integrates with all backend endpoints including:
 * - Social Media OAuth & Management
 * - Multi-Platform Posting & Scheduling
 * - Unified Analytics
 * - Zoho Integration
 * - Job Scheduler
 * - Dashboard
 */

import { api, DEFAULT_USER_ID } from "@/lib/api";

// ==================== Social Media OAuth & Connection ====================

/**
 * Get OAuth authorization URL for a social media platform
 * @param {string} platform - facebook, instagram, twitter, linkedin
 * @param {string} userId - User ID
 * @returns {Promise<{success: boolean, auth_url: string, state: string}>}
 */
export const getSocialOAuthUrl = async (platform, userId = DEFAULT_USER_ID) => {
  return api.get(`/social/connect/${platform}`, {
    params: { user_id: userId }
  });
};

/**
 * Get all connected social media accounts
 * @param {string} userId - User ID
 * @param {string} platform - Optional platform filter
 * @returns {Promise<{success: boolean, accounts: Array}>}
 */
export const getConnectedAccounts = async (userId = DEFAULT_USER_ID, platform = null) => {
  const params = { user_id: userId };
  if (platform) params.platform = platform;
  return api.get('/social/accounts', { params });
};

/**
 * Disconnect a social media account
 * @param {string} accountId - Account ID to disconnect
 * @param {string} userId - User ID
 * @returns {Promise<{success: boolean, message: string}>}
 */
export const disconnectAccount = async (accountId, userId = DEFAULT_USER_ID) => {
  return api.delete(`/social/accounts/${accountId}`, {
    params: { user_id: userId }
  });
};

// ==================== Social Media Posting ====================

/**
 * Post to a single social media account
 * @param {string} accountId - Account ID
 * @param {Object} content - Post content {text, image_url, video_url, link}
 * @param {string} userId - User ID
 * @returns {Promise<{success: boolean, post_id: string, post_url: string}>}
 */
export const postToSocialMedia = async (accountId, content, userId = DEFAULT_USER_ID) => {
  return api.post('/social/post', {
    account_id: accountId,
    content,
    user_id: userId
  });
};

/**
 * Post to multiple social media accounts simultaneously
 * @param {Array<string>} accountIds - Array of account IDs
 * @param {Object} content - Post content
 * @param {string} userId - User ID
 * @returns {Promise<{success: boolean, results: Object, summary: Object}>}
 */
export const postToMultipleAccounts = async (accountIds, content, userId = DEFAULT_USER_ID) => {
  return api.post('/social/post/multiple', {
    account_ids: accountIds,
    content,
    user_id: userId
  });
};

/**
 * Schedule a post for later publication
 * @param {Array<string>} accountIds - Array of account IDs
 * @param {Object} content - Post content
 * @param {string} scheduledTime - ISO datetime string
 * @param {string} userId - User ID
 * @param {Object} metadata - Optional metadata
 * @returns {Promise<{success: boolean, job_id: string, scheduled_time: string}>}
 */
export const schedulePost = async (accountIds, content, scheduledTime, userId = DEFAULT_USER_ID, metadata = null) => {
  return api.post('/social/post/schedule', {
    account_ids: accountIds,
    content,
    scheduled_time: scheduledTime,
    user_id: userId,
    metadata
  });
};

// ==================== Social Media Analytics ====================

/**
 * Get analytics for a specific social media platform/account
 * @param {string} platform - facebook, instagram, twitter, linkedin
 * @param {string} accountId - Account ID
 * @param {string} postId - Optional specific post ID
 * @param {string} dateFrom - Optional start date (ISO format)
 * @param {string} dateTo - Optional end date (ISO format)
 * @returns {Promise<{success: boolean, insights: Object}>}
 */
export const getSocialAnalytics = async (platform, accountId, postId = null, dateFrom = null, dateTo = null) => {
  const params = {};
  if (postId) params.post_id = postId;
  if (dateFrom) params.date_from = dateFrom;
  if (dateTo) params.date_to = dateTo;

  return api.get(`/social/analytics/${platform}/${accountId}`, { params });
};

/**
 * Get aggregated analytics from all connected platforms
 * @param {string} userId - User ID
 * @param {string} dateFrom - Optional start date
 * @param {string} dateTo - Optional end date
 * @returns {Promise<{success: boolean, data: Object}>}
 */
export const getAggregatedAnalytics = async (userId = DEFAULT_USER_ID, dateFrom = null, dateTo = null) => {
  const params = { user_id: userId };
  if (dateFrom) params.date_from = dateFrom;
  if (dateTo) params.date_to = dateTo;

  return api.get('/social/analytics/aggregate', { params });
};

/**
 * Get historical analytics data
 * @param {string} userId - User ID
 * @param {string} platform - Optional platform filter
 * @param {number} days - Number of days of history
 * @returns {Promise<{success: boolean, by_date: Object}>}
 */
export const getAnalyticsHistory = async (userId = DEFAULT_USER_ID, platform = null, days = 30) => {
  const params = { user_id: userId, days };
  if (platform) params.platform = platform;

  return api.get('/social/analytics/history', { params });
};

// ==================== Job Scheduler ====================

/**
 * Get status of a scheduled job
 * @param {string} jobId - Job ID
 * @returns {Promise<{success: boolean, job: Object}>}
 */
export const getJobStatus = async (jobId) => {
  return api.get(`/jobs/status/${jobId}`);
};

/**
 * Get all jobs for a user
 * @param {string} userId - User ID
 * @param {string} status - Optional status filter (pending, processing, completed, failed, cancelled)
 * @param {string} jobType - Optional job type filter (scheduled_post, email_campaign)
 * @returns {Promise<{success: boolean, total: number, jobs: Array}>}
 */
export const getUserJobs = async (userId = DEFAULT_USER_ID, status = null, jobType = null) => {
  const params = { user_id: userId };
  if (status) params.status = status;
  if (jobType) params.job_type = jobType;

  return api.get('/jobs/user', { params });
};

/**
 * Cancel a scheduled job
 * @param {string} jobId - Job ID to cancel
 * @returns {Promise<{success: boolean, message: string}>}
 */
export const cancelJob = async (jobId) => {
  return api.delete(`/jobs/${jobId}`);
};

/**
 * Get job scheduler status
 * @returns {Promise<{success: boolean, is_running: boolean, active_jobs: number, jobs: Array, statistics: Object}>}
 */
export const getSchedulerStatus = async () => {
  return api.get('/jobs/scheduler/status');
};

/**
 * Start the job scheduler
 * @returns {Promise<{success: boolean, message: string}>}
 */
export const startScheduler = async () => {
  return api.post('/jobs/scheduler/start');
};

/**
 * Stop the job scheduler
 * @returns {Promise<{success: boolean, message: string}>}
 */
export const stopScheduler = async () => {
  return api.post('/jobs/scheduler/stop');
};

// ==================== Dashboard & Tokens ====================

/**
 * Get complete dashboard overview with all metrics
 * @param {string} userId - User ID
 * @returns {Promise<{success: boolean, token_status: Object, connected_accounts: Array, pending_jobs: Array, analytics: Object}>}
 */
export const getDashboardOverview = async (userId = DEFAULT_USER_ID) => {
  return api.get('/dashboard/overview', {
    params: { user_id: userId }
  });
};

/**
 * Manually refresh access tokens
 * @param {string} userId - User ID
 * @param {string} platform - Optional platform to refresh (if not specified, refreshes all expiring tokens)
 * @returns {Promise<{success: boolean, access_token?: string, expires_in?: number}>}
 */
export const refreshTokens = async (userId = DEFAULT_USER_ID, platform = null) => {
  const params = { user_id: userId };
  if (platform) params.platform = platform;

  return api.post('/tokens/refresh', null, { params });
};

/**
 * Get status of all tokens for a user
 * @param {string} userId - User ID
 * @returns {Promise<{user_id: string, social_accounts: Array, zoho: Object}>}
 */
export const getTokenStatus = async (userId = DEFAULT_USER_ID) => {
  return api.get('/tokens/status', {
    params: { user_id: userId }
  });
};

// ==================== Zoho Integration ====================

/**
 * Get Zoho OAuth authorization URL
 * @param {string} userId - User ID
 * @returns {Promise<{authorization_url: string}>}
 */
export const getZohoOAuthUrl = async (userId = DEFAULT_USER_ID) => {
  return api.get('/zoho/authorize', {
    params: { user_id: userId }
  });
};

/**
 * Get Zoho connection status
 * @param {string} userId - User ID
 * @returns {Promise<{connected: boolean, expires_at?: string}>}
 */
export const getZohoStatus = async (userId = DEFAULT_USER_ID) => {
  return api.get('/zoho/status', {
    params: { user_id: userId }
  });
};

/**
 * Disconnect Zoho account
 * @param {string} userId - User ID
 * @returns {Promise<{success: boolean, message: string}>}
 */
export const disconnectZoho = async (userId = DEFAULT_USER_ID) => {
  return api.post('/zoho/disconnect', { user_id: userId });
};

// ==================== Zoho CRM ====================

/**
 * Get CRM modules (Leads, Contacts, Deals, etc.)
 * @param {string} userId - User ID
 * @returns {Promise<{modules: Array}>}
 */
export const getCRMModules = async (userId = DEFAULT_USER_ID) => {
  return api.get('/zoho/crm/modules', {
    params: { user_id: userId }
  });
};

/**
 * Get records from a CRM module
 * @param {string} module - Module name (Leads, Contacts, Deals, etc.)
 * @param {string} userId - User ID
 * @param {number} page - Page number
 * @param {number} perPage - Records per page
 * @returns {Promise<{data: Array, info: Object}>}
 */
export const getCRMRecords = async (module, userId = DEFAULT_USER_ID, page = 1, perPage = 200) => {
  return api.get(`/zoho/crm/${module}`, {
    params: { user_id: userId, page, per_page: perPage }
  });
};

/**
 * Create a new CRM record
 * @param {string} module - Module name
 * @param {Object} data - Record data
 * @param {string} userId - User ID
 * @returns {Promise<{data: Array, info: Object}>}
 */
export const createCRMRecord = async (module, data, userId = DEFAULT_USER_ID) => {
  return api.post(`/zoho/crm/${module}`, {
    data,
    user_id: userId
  });
};

// ==================== Zoho Email & Campaigns ====================

/**
 * Send email via Zoho Mail
 * @param {Object} emailData - Email data {to, subject, body, from_email}
 * @param {string} userId - User ID
 * @returns {Promise<{success: boolean, message: string}>}
 */
export const sendZohoEmail = async (emailData, userId = DEFAULT_USER_ID) => {
  return api.post('/zoho/mail/send', {
    ...emailData,
    user_id: userId
  });
};

/**
 * Get Zoho Campaigns lists
 * @param {string} userId - User ID
 * @returns {Promise<{list_of_details: Array}>}
 */
export const getCampaignLists = async (userId = DEFAULT_USER_ID) => {
  return api.get('/zoho/campaigns/lists', {
    params: { user_id: userId }
  });
};

/**
 * Create email campaign
 * @param {Object} campaignData - Campaign data
 * @param {string} userId - User ID
 * @returns {Promise<{success: boolean, campaign_key: string}>}
 */
export const createEmailCampaign = async (campaignData, userId = DEFAULT_USER_ID) => {
  return api.post('/zoho/campaigns/create', {
    ...campaignData,
    user_id: userId
  });
};

// ==================== Helper Functions ====================

/**
 * Build ISO datetime string for scheduling
 * @param {Date} date - Date object
 * @param {string} time - Time string (HH:MM)
 * @returns {string} ISO datetime string
 */
export const buildScheduleTime = (date, time) => {
  const [hours, minutes] = time.split(':');
  const scheduleDate = new Date(date);
  scheduleDate.setHours(parseInt(hours), parseInt(minutes), 0, 0);
  return scheduleDate.toISOString();
};

/**
 * Format date range for analytics
 * @param {number} days - Number of days back
 * @returns {{dateFrom: string, dateTo: string}}
 */
export const getDateRange = (days) => {
  const dateTo = new Date();
  const dateFrom = new Date();
  dateFrom.setDate(dateFrom.getDate() - days);

  return {
    dateFrom: dateFrom.toISOString().split('T')[0],
    dateTo: dateTo.toISOString().split('T')[0]
  };
};

/**
 * Check if token is expiring soon (within 24 hours)
 * @param {string} expiresAt - ISO datetime string
 * @returns {boolean}
 */
export const isTokenExpiringSoon = (expiresAt) => {
  if (!expiresAt) return false;
  const expiry = new Date(expiresAt);
  const now = new Date();
  const hoursUntilExpiry = (expiry - now) / (1000 * 60 * 60);
  return hoursUntilExpiry < 24;
};

/**
 * Check if token is expired
 * @param {string} expiresAt - ISO datetime string
 * @returns {boolean}
 */
export const isTokenExpired = (expiresAt) => {
  if (!expiresAt) return false;
  return new Date(expiresAt) < new Date();
};

// ==================== Authentication ====================

/**
 * User signup
 * @param {Object} userData - {email, password, full_name, company_name}
 * @returns {Promise<{status: string, token: string, user_id: string, tenant_id: string}>}
 */
export const signup = async (userData) => {
  return api.post('/auth/signup', userData);
};

/**
 * User login
 * @param {string} email - User email
 * @param {string} password - User password
 * @returns {Promise<{status: string, token: string, user_id: string, tenant_id: string}>}
 */
export const login = async (email, password) => {
  return api.post('/auth/login', { email, password });
};

/**
 * User logout
 * @param {string} token - Auth token
 * @returns {Promise<{status: string}>}
 */
export const logout = async (token) => {
  return api.post('/auth/logout', { token });
};

/**
 * Verify JWT token
 * @param {string} token - Auth token
 * @returns {Promise<{status: string, user_id: string, tenant_id: string}>}
 */
export const verifyToken = async (token) => {
  return api.post('/auth/verify', { token });
};

/**
 * Change password
 * @param {string} userId - User ID
 * @param {string} oldPassword - Current password
 * @param {string} newPassword - New password
 * @returns {Promise<{status: string}>}
 */
export const changePassword = async (userId, oldPassword, newPassword) => {
  return api.put('/auth/change-password', {
    user_id: userId,
    old_password: oldPassword,
    new_password: newPassword
  });
};

// ==================== Credits Management ====================

/**
 * Get credits balance
 * @param {string} tenantId - Tenant ID
 * @returns {Promise<{status: string, credits_balance: number, plan_type: string}>}
 */
export const getCreditsBalance = async (tenantId) => {
  return api.get('/credits/balance', {
    params: { tenant_id: tenantId }
  });
};

/**
 * Get usage summary
 * @param {string} tenantId - Tenant ID
 * @param {number} days - Number of days (default 30)
 * @returns {Promise<{status: string, summary: Object}>}
 */
export const getUsageSummary = async (tenantId, days = 30) => {
  return api.get('/credits/usage', {
    params: { tenant_id: tenantId, days }
  });
};

/**
 * Get transaction history
 * @param {string} tenantId - Tenant ID
 * @returns {Promise<{status: string, transactions: Array}>}
 */
export const getTransactionHistory = async (tenantId) => {
  return api.get('/credits/history', {
    params: { tenant_id: tenantId }
  });
};

/**
 * Get pricing information
 * @returns {Promise<{status: string, pricing: Object, packages: Object}>}
 */
export const getPricingInfo = async () => {
  return api.get('/credits/pricing');
};

// ==================== Payment ====================

/**
 * Create Stripe checkout session
 * @param {string} tenantId - Tenant ID
 * @param {string} packageName - Package name (starter, professional, enterprise)
 * @param {string} successUrl - Success redirect URL
 * @param {string} cancelUrl - Cancel redirect URL
 * @returns {Promise<{status: string, session_id: string, checkout_url: string}>}
 */
export const createCheckoutSession = async (tenantId, packageName, successUrl, cancelUrl) => {
  return api.post('/payment/checkout', {
    tenant_id: tenantId,
    package_name: packageName,
    success_url: successUrl,
    cancel_url: cancelUrl
  });
};

/**
 * Get available credit packages
 * @returns {Promise<{status: string, packages: Array}>}
 */
export const getPaymentPackages = async () => {
  return api.get('/payment/packages');
};

/**
 * Get payment history
 * @param {string} tenantId - Tenant ID
 * @returns {Promise<{status: string, transactions: Array}>}
 */
export const getPaymentHistory = async (tenantId) => {
  return api.get('/payment/history', {
    params: { tenant_id: tenantId }
  });
};

// ==================== Data Scraping ====================

/**
 * Scrape Google Maps businesses
 * @param {string} tenantId - Tenant ID
 * @param {string} query - Search query
 * @param {string} location - Location
 * @param {number} maxResults - Maximum results (default 20)
 * @returns {Promise<{status: string, count: number, data: Array}>}
 */
export const scrapeGoogleMaps = async (tenantId, query, location, maxResults = 20) => {
  return api.post('/scraping/google-maps', {
    tenant_id: tenantId,
    query,
    location,
    max_results: maxResults
  });
};

/**
 * Scrape website data
 * @param {string} tenantId - Tenant ID
 * @param {string} url - Website URL
 * @param {boolean} extractEmails - Extract emails
 * @param {boolean} extractPhones - Extract phones
 * @param {boolean} extractLinks - Extract links
 * @returns {Promise<{status: string, data: Object}>}
 */
export const scrapeWebsite = async (tenantId, url, extractEmails = true, extractPhones = true, extractLinks = false) => {
  return api.post('/scraping/website', {
    tenant_id: tenantId,
    url,
    extract_emails: extractEmails,
    extract_phones: extractPhones,
    extract_links: extractLinks
  });
};

/**
 * Get scraped data
 * @param {string} tenantId - Tenant ID
 * @param {string} source - Data source (google_maps, linkedin, website, all)
 * @param {number} limit - Maximum records
 * @returns {Promise<{status: string, data: Array}>}
 */
export const getScrapedData = async (tenantId, source = 'all', limit = 50) => {
  return api.get('/scraping/data', {
    params: { tenant_id: tenantId, source, limit }
  });
};

export default {
  // Authentication
  signup,
  login,
  logout,
  verifyToken,
  changePassword,

  // Credits
  getCreditsBalance,
  getUsageSummary,
  getTransactionHistory,
  getPricingInfo,

  // Payment
  createCheckoutSession,
  getPaymentPackages,
  getPaymentHistory,

  // Scraping
  scrapeGoogleMaps,
  scrapeWebsite,
  getScrapedData,

  // Social Media
  getSocialOAuthUrl,
  getConnectedAccounts,
  disconnectAccount,
  postToSocialMedia,
  postToMultipleAccounts,
  schedulePost,

  // Analytics
  getSocialAnalytics,
  getAggregatedAnalytics,
  getAnalyticsHistory,

  // Jobs
  getJobStatus,
  getUserJobs,
  cancelJob,
  getSchedulerStatus,
  startScheduler,
  stopScheduler,

  // Dashboard
  getDashboardOverview,
  refreshTokens,
  getTokenStatus,

  // Zoho
  getZohoOAuthUrl,
  getZohoStatus,
  disconnectZoho,
  getCRMModules,
  getCRMRecords,
  createCRMRecord,
  sendZohoEmail,
  getCampaignLists,
  createEmailCampaign,

  // Helpers
  buildScheduleTime,
  getDateRange,
  isTokenExpiringSoon,
  isTokenExpired
};
