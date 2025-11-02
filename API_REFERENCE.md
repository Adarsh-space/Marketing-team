# Marketing Minds AI - API Reference

Quick reference for all social media, analytics, and job scheduler endpoints.

---

## 🔗 Social Media OAuth & Connection

### Connect Account
```http
GET /api/social/connect/{platform}?user_id={user_id}&redirect_uri={redirect_uri}
```

**Parameters**:
- `platform`: `facebook`, `instagram`, `twitter`, `linkedin`
- `user_id`: User identifier (default: "default_user")
- `redirect_uri`: Optional OAuth redirect URI

**Response**:
```json
{
  "success": true,
  "auth_url": "https://platform.com/oauth/authorize?...",
  "state": "secure_random_token"
}
```

**Example**:
```bash
curl "https://marketing-minds.preview.emergentagent.com/api/social/connect/facebook?user_id=user123"
```

---

### OAuth Callback (Automatic)
```http
GET /api/social/callback/{platform}?code={code}&state={state}
```

**Note**: This endpoint is called automatically by the OAuth provider after user authorization. Returns HTML page with redirect.

---

### Get Connected Accounts
```http
GET /api/social/accounts?user_id={user_id}&platform={platform}
```

**Parameters**:
- `user_id`: User identifier
- `platform`: Optional filter by platform

**Response**:
```json
{
  "success": true,
  "accounts": [
    {
      "account_id": "facebook_123",
      "platform": "facebook",
      "account_name": "My Business Page",
      "connected_at": "2025-01-15T10:00:00Z",
      "token_expires_at": "2025-03-15T10:00:00Z"
    }
  ]
}
```

**Example**:
```bash
curl "https://marketing-minds.preview.emergentagent.com/api/social/accounts?user_id=user123"
```

---

### Disconnect Account
```http
DELETE /api/social/accounts/{account_id}?user_id={user_id}
```

**Response**:
```json
{
  "success": true,
  "message": "Account disconnected successfully"
}
```

**Example**:
```bash
curl -X DELETE "https://marketing-minds.preview.emergentagent.com/api/social/accounts/facebook_123?user_id=user123"
```

---

## 📤 Social Media Posting

### Post to Single Account
```http
POST /api/social/post
Content-Type: application/json
```

**Request Body**:
```json
{
  "account_id": "facebook_123",
  "content": {
    "text": "Post text or caption",
    "image_url": "https://example.com/image.jpg",
    "video_url": "https://example.com/video.mp4",
    "link": "https://example.com/article"
  },
  "user_id": "user123"
}
```

**Response**:
```json
{
  "success": true,
  "platform": "facebook",
  "post_id": "12345_67890",
  "post_url": "https://facebook.com/12345/posts/67890",
  "message": "Posted successfully"
}
```

**Example**:
```bash
curl -X POST "https://marketing-minds.preview.emergentagent.com/api/social/post" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "facebook_123",
    "content": {
      "text": "Check out our new product!",
      "image_url": "https://example.com/product.jpg"
    },
    "user_id": "user123"
  }'
```

---

### Post to Multiple Accounts
```http
POST /api/social/post/multiple
Content-Type: application/json
```

**Request Body**:
```json
{
  "account_ids": [
    "facebook_123",
    "instagram_456",
    "twitter_789"
  ],
  "content": {
    "text": "Cross-platform post!",
    "image_url": "https://example.com/image.jpg"
  },
  "user_id": "user123"
}
```

**Response**:
```json
{
  "success": true,
  "results": {
    "facebook_123": {
      "success": true,
      "post_id": "12345_67890"
    },
    "instagram_456": {
      "success": true,
      "post_id": "ig_12345"
    },
    "twitter_789": {
      "success": true,
      "post_id": "1234567890123456789"
    }
  },
  "summary": {
    "total": 3,
    "successful": 3,
    "failed": 0
  }
}
```

**Example**:
```bash
curl -X POST "https://marketing-minds.preview.emergentagent.com/api/social/post/multiple" \
  -H "Content-Type: application/json" \
  -d '{
    "account_ids": ["facebook_123", "instagram_456"],
    "content": {"text": "Multi-platform announcement!"},
    "user_id": "user123"
  }'
```

---

### Schedule Post
```http
POST /api/social/post/schedule
Content-Type: application/json
```

**Request Body**:
```json
{
  "account_ids": ["facebook_123", "instagram_456"],
  "content": {
    "text": "Scheduled post for tomorrow!",
    "image_url": "https://example.com/image.jpg"
  },
  "scheduled_time": "2025-01-21T15:30:00Z",
  "user_id": "user123",
  "metadata": {
    "campaign_id": "campaign_123",
    "category": "product_launch"
  }
}
```

**Response**:
```json
{
  "success": true,
  "job_id": "job_abc123",
  "scheduled_time": "2025-01-21T15:30:00Z"
}
```

**Example**:
```bash
curl -X POST "https://marketing-minds.preview.emergentagent.com/api/social/post/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "account_ids": ["facebook_123"],
    "content": {"text": "Tomorrow at 3:30 PM!"},
    "scheduled_time": "2025-01-21T15:30:00Z",
    "user_id": "user123"
  }'
```

---

## 📊 Social Media Analytics

### Get Platform Analytics
```http
GET /api/social/analytics/{platform}/{account_id}?post_id={post_id}&date_from={date}&date_to={date}
```

**Parameters**:
- `platform`: `facebook`, `instagram`, `twitter`, `linkedin`
- `account_id`: Social account ID
- `post_id`: Optional specific post ID
- `date_from`: Optional start date (ISO format)
- `date_to`: Optional end date (ISO format)

**Response** (Facebook Example):
```json
{
  "success": true,
  "platform": "facebook",
  "account_id": "facebook_123",
  "insights": {
    "page_impressions": 15000,
    "page_engaged_users": 1200,
    "page_post_engagements": 800,
    "page_fans": 5000,
    "page_fan_adds": 50,
    "page_views_total": 3000
  }
}
```

**Example**:
```bash
curl "https://marketing-minds.preview.emergentagent.com/api/social/analytics/facebook/facebook_123?date_from=2025-01-01&date_to=2025-01-20"
```

---

### Get Aggregated Analytics
```http
GET /api/social/analytics/aggregate?user_id={user_id}&date_from={date}&date_to={date}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "user_id": "user123",
    "date_from": "2025-01-01T00:00:00Z",
    "date_to": "2025-01-20T00:00:00Z",
    "social_media": {
      "facebook": {
        "page_impressions": 15000,
        "page_engaged_users": 1200
      },
      "instagram": {
        "impressions": 8000,
        "engagement": 600,
        "follower_count": 3000
      },
      "twitter": {
        "total_tweets": 25,
        "total_likes": 450,
        "total_retweets": 120
      }
    },
    "zoho": {
      "crm_leads": {
        "total_records": 150,
        "by_status": {
          "New": 50,
          "Qualified": 75,
          "Converted": 25
        }
      },
      "email_campaigns": {
        "total_campaigns": 5,
        "total_sent": 5000,
        "total_opens": 1250,
        "avg_open_rate": 25.0
      }
    },
    "summary": {
      "total_social_impressions": 23000,
      "total_social_engagement": 1800,
      "total_social_followers": 8000,
      "total_email_sent": 5000,
      "total_email_opens": 1250,
      "email_open_rate": 25.0,
      "social_engagement_rate": 7.8,
      "platforms_connected": 3
    }
  }
}
```

**Example**:
```bash
curl "https://marketing-minds.preview.emergentagent.com/api/social/analytics/aggregate?user_id=user123&date_from=2025-01-01"
```

---

### Get Analytics History
```http
GET /api/social/analytics/history?user_id={user_id}&platform={platform}&days={days}
```

**Parameters**:
- `user_id`: User identifier
- `platform`: Optional platform filter
- `days`: Number of days of history (default: 30)

**Response**:
```json
{
  "success": true,
  "user_id": "user123",
  "platform": "facebook",
  "days": 30,
  "total_records": 120,
  "by_date": {
    "2025-01-20": [
      {
        "platform": "facebook",
        "insights": {
          "page_impressions": 500,
          "page_engaged_users": 40
        }
      }
    ],
    "2025-01-19": [...]
  }
}
```

**Example**:
```bash
curl "https://marketing-minds.preview.emergentagent.com/api/social/analytics/history?user_id=user123&platform=facebook&days=7"
```

---

## ⏰ Job Scheduler

### Get Job Status
```http
GET /api/jobs/status/{job_id}
```

**Response**:
```json
{
  "success": true,
  "job": {
    "job_id": "job_abc123",
    "job_type": "scheduled_post",
    "status": "pending",
    "scheduled_time": "2025-01-21T15:30:00Z",
    "created_at": "2025-01-20T10:00:00Z",
    "attempts": 0
  }
}
```

**Example**:
```bash
curl "https://marketing-minds.preview.emergentagent.com/api/jobs/status/job_abc123"
```

---

### Get User's Jobs
```http
GET /api/jobs/user?user_id={user_id}&status={status}&job_type={type}
```

**Parameters**:
- `user_id`: User identifier
- `status`: Optional filter (`pending`, `processing`, `completed`, `failed`, `cancelled`)
- `job_type`: Optional filter (`scheduled_post`, `email_campaign`)

**Response**:
```json
{
  "success": true,
  "total": 5,
  "jobs": [
    {
      "job_id": "job_abc123",
      "job_type": "scheduled_post",
      "status": "pending",
      "scheduled_time": "2025-01-21T15:30:00Z",
      "created_at": "2025-01-20T10:00:00Z"
    },
    ...
  ]
}
```

**Example**:
```bash
curl "https://marketing-minds.preview.emergentagent.com/api/jobs/user?user_id=user123&status=pending"
```

---

### Cancel Job
```http
DELETE /api/jobs/{job_id}
```

**Response**:
```json
{
  "success": true,
  "message": "Job cancelled successfully"
}
```

**Example**:
```bash
curl -X DELETE "https://marketing-minds.preview.emergentagent.com/api/jobs/job_abc123"
```

---

### Get Scheduler Status
```http
GET /api/jobs/scheduler/status
```

**Response**:
```json
{
  "success": true,
  "is_running": true,
  "active_jobs": 3,
  "jobs": [
    {
      "id": "token_refresh",
      "name": "_handle_token_refresh",
      "next_run_time": "2025-01-20T18:00:00Z"
    },
    {
      "id": "analytics_sync",
      "name": "_handle_analytics_sync",
      "next_run_time": "2025-01-21T02:00:00Z"
    },
    {
      "id": "cleanup",
      "name": "_handle_cleanup",
      "next_run_time": "2025-01-26T03:00:00Z"
    }
  ],
  "statistics": {
    "pending": 5,
    "processing": 0,
    "completed": 120,
    "failed": 2,
    "cancelled": 1
  }
}
```

**Example**:
```bash
curl "https://marketing-minds.preview.emergentagent.com/api/jobs/scheduler/status"
```

---

### Start Scheduler
```http
POST /api/jobs/scheduler/start
```

**Response**:
```json
{
  "success": true,
  "message": "Job scheduler started"
}
```

---

### Stop Scheduler
```http
POST /api/jobs/scheduler/stop
```

**Response**:
```json
{
  "success": true,
  "message": "Job scheduler stopped"
}
```

---

## 📈 Dashboard & Tokens

### Get Dashboard Overview
```http
GET /api/dashboard/overview?user_id={user_id}
```

**Response**:
```json
{
  "success": true,
  "user_id": "user123",
  "token_status": {
    "social_accounts": [
      {
        "platform": "facebook",
        "account_id": "facebook_123",
        "account_name": "My Business Page",
        "expires_at": "2025-03-15T10:00:00Z",
        "time_until_expiry_seconds": 5184000,
        "is_expired": false,
        "is_expiring_soon": false
      }
    ],
    "zoho": {
      "expires_at": "2025-01-20T11:00:00Z",
      "time_until_expiry_seconds": 3600,
      "is_expired": false,
      "is_expiring_soon": true
    }
  },
  "connected_accounts": [
    {
      "platform": "facebook",
      "account_name": "My Business Page"
    }
  ],
  "pending_jobs": [
    {
      "job_id": "job_abc123",
      "job_type": "scheduled_post",
      "scheduled_time": "2025-01-21T15:30:00Z"
    }
  ],
  "analytics": {
    "summary": {
      "total_social_impressions": 23000,
      "total_social_engagement": 1800,
      "platforms_connected": 3
    }
  }
}
```

**Example**:
```bash
curl "https://marketing-minds.preview.emergentagent.com/api/dashboard/overview?user_id=user123"
```

---

### Refresh Tokens
```http
POST /api/tokens/refresh?user_id={user_id}&platform={platform}
```

**Parameters**:
- `user_id`: User identifier
- `platform`: Optional platform to refresh (if not specified, refreshes all expiring tokens)

**Response**:
```json
{
  "success": true,
  "access_token": "new_token",
  "expires_in": 5184000
}
```

**Example**:
```bash
curl -X POST "https://marketing-minds.preview.emergentagent.com/api/tokens/refresh?user_id=user123&platform=facebook"
```

---

### Get Token Status
```http
GET /api/tokens/status?user_id={user_id}
```

**Response**: Same as token_status in dashboard overview

**Example**:
```bash
curl "https://marketing-minds.preview.emergentagent.com/api/tokens/status?user_id=user123"
```

---

## 🔍 Health & Status

### Health Check
```http
GET /api/health
```

**Response**:
```json
{
  "status": "healthy",
  "database": "connected",
  "agents": [
    "ConversationalAgent",
    "SocialMediaAgent",
    "ContentAgent",
    ...
  ]
}
```

---

### Root Endpoint
```http
GET /api/
```

**Response**:
```json
{
  "message": "AI Marketing Automation Platform API",
  "version": "1.0.0",
  "agents": [...]
}
```

---

## 📝 Common Use Cases

### 1. Connect Facebook and Post
```bash
# Step 1: Get OAuth URL
curl "https://marketing-minds.preview.emergentagent.com/api/social/connect/facebook?user_id=user123"

# Step 2: User authorizes (browser redirect)

# Step 3: Post to Facebook
curl -X POST "https://marketing-minds.preview.emergentagent.com/api/social/post" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "facebook_123",
    "content": {"text": "Hello Facebook!"},
    "user_id": "user123"
  }'
```

---

### 2. Cross-Platform Campaign
```bash
# Connect all platforms first (repeat for each)
curl "https://marketing-minds.preview.emergentagent.com/api/social/connect/facebook?user_id=user123"
curl "https://marketing-minds.preview.emergentagent.com/api/social/connect/instagram?user_id=user123"
curl "https://marketing-minds.preview.emergentagent.com/api/social/connect/twitter?user_id=user123"

# Post to all
curl -X POST "https://marketing-minds.preview.emergentagent.com/api/social/post/multiple" \
  -H "Content-Type: application/json" \
  -d '{
    "account_ids": ["facebook_123", "instagram_456", "twitter_789"],
    "content": {
      "text": "Big announcement! #Launch",
      "image_url": "https://example.com/announcement.jpg"
    },
    "user_id": "user123"
  }'
```

---

### 3. Schedule Weekly Posts
```bash
# Schedule Monday post
curl -X POST "https://marketing-minds.preview.emergentagent.com/api/social/post/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "account_ids": ["facebook_123", "instagram_456"],
    "content": {"text": "Monday motivation!"},
    "scheduled_time": "2025-01-27T09:00:00Z",
    "user_id": "user123"
  }'

# Schedule Wednesday post
curl -X POST "https://marketing-minds.preview.emergentagent.com/api/social/post/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "account_ids": ["facebook_123", "instagram_456"],
    "content": {"text": "Midweek update!"},
    "scheduled_time": "2025-01-29T14:00:00Z",
    "user_id": "user123"
  }'
```

---

### 4. Monitor Analytics
```bash
# Get weekly performance
curl "https://marketing-minds.preview.emergentagent.com/api/social/analytics/aggregate?user_id=user123&date_from=2025-01-14&date_to=2025-01-20"

# Check specific platform
curl "https://marketing-minds.preview.emergentagent.com/api/social/analytics/facebook/facebook_123?date_from=2025-01-14"

# View historical trends
curl "https://marketing-minds.preview.emergentagent.com/api/social/analytics/history?user_id=user123&days=30"
```

---

## 🔐 Authentication

All endpoints use `user_id` parameter for user identification. In production, you may want to add JWT or API key authentication.

---

## 📖 Response Codes

- `200 OK` - Request successful
- `400 Bad Request` - Invalid parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## 🔄 Rate Limits

Currently no rate limiting. Consider implementing for production:
- Social Media APIs have their own rate limits
- Respect platform-specific limits
- Implement backoff for failed requests

---

## 📞 Support

For detailed documentation, see:
- `DEPLOYMENT_COMPLETE.md` - Full deployment guide
- `DATABASE_SCHEMA.md` - Database structure
- `ZOHO_COMPLETE_INTEGRATION_PLAN.md` - Integration plan

---

**Base URL**: `https://marketing-minds.preview.emergentagent.com`
**API Prefix**: `/api`
**Version**: 1.0.0
