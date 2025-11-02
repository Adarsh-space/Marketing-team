# Marketing Minds AI - Complete Database Schema

## MongoDB Collections

### 1. `users`
**Purpose:** User account management

```javascript
{
  _id: ObjectId,
  user_id: String (unique),
  email: String (unique),
  name: String,
  company: String,
  role: String, // "admin", "user", "viewer"
  created_at: ISODate,
  updated_at: ISODate,
  last_login: ISODate,
  preferences: {
    language: String,
    timezone: String,
    notifications: Boolean
  },
  subscription: {
    plan: String, // "free", "basic", "pro", "enterprise"
    status: String, // "active", "suspended", "cancelled"
    expires_at: ISODate
  }
}
```

**Indexes:**
- `user_id`: unique
- `email`: unique

---

### 2. `conversations`
**Purpose:** Chat history and conversational interface state

```javascript
{
  _id: ObjectId,
  conversation_id: String (unique),
  user_id: String,
  created_at: ISODate,
  updated_at: ISODate,
  messages: [
    {
      role: String, // "user", "assistant", "system"
      content: String,
      timestamp: ISODate,
      metadata: Object // optional
    }
  ],
  context: {
    campaign_brief: Object,
    collected_info: Object,
    ready_to_plan: Boolean
  }
}
```

**Indexes:**
- `conversation_id`: unique
- `user_id`
- `updated_at`: descending

---

### 3. `campaigns`
**Purpose:** Marketing campaign management

```javascript
{
  _id: ObjectId,
  campaign_id: String (unique),
  user_id: String,
  conversation_id: String,
  name: String,
  brief: {
    product: String,
    target_audience: String,
    objective: String,
    budget: String,
    timeline: String,
    channels: [String],
    additional_context: String
  },
  status: String, // "draft", "planning", "executing", "completed", "failed"
  plan: {
    strategy: String,
    tasks: [
      {
        task_id: String,
        agent_assigned: String,
        description: String,
        requirements: [String],
        dependencies: [String],
        status: String, // "pending", "in_progress", "completed", "failed"
        estimated_duration: String
      }
    ],
    timeline: Object,
    kpis: [Object]
  },
  results: {
    task_results: Object,
    analytics: Object,
    roi: Number,
    performance_summary: String
  },
  created_at: ISODate,
  updated_at: ISODate,
  completed_at: ISODate
}
```

**Indexes:**
- `campaign_id`: unique
- `user_id`
- `status`
- `created_at`: descending

---

### 4. `zoho_tokens`
**Purpose:** Zoho OAuth credentials

```javascript
{
  _id: ObjectId,
  user_id: String (unique),
  access_token: String,
  refresh_token: String,
  token_type: String, // "Bearer"
  expires_in: Number,
  expires_at: ISODate,
  scope: String,
  data_center: String, // "com", "in", "eu", "com.au"
  created_at: ISODate,
  updated_at: ISODate
}
```

**Indexes:**
- `user_id`: unique
- `expires_at`

---

### 5. `social_accounts`
**Purpose:** Connected social media accounts

```javascript
{
  _id: ObjectId,
  user_id: String,
  platform: String, // "facebook", "instagram", "twitter", "linkedin"
  account_id: String, // Platform-specific account ID
  account_name: String,
  account_username: String,
  profile_picture: String,
  auth_type: String, // "oauth", "api_token"
  credentials: {
    access_token: String,
    refresh_token: String,
    token_expires_at: ISODate,
    // Platform-specific fields
    page_id: String, // For Facebook
    instagram_business_id: String, // For Instagram
    api_key: String, // For Twitter
    api_secret: String
  },
  account_info: {
    followers: Number,
    following: Number,
    posts_count: Number,
    verified: Boolean,
    business_account: Boolean
  },
  status: String, // "active", "expired", "disconnected"
  connected_at: ISODate,
  updated_at: ISODate,
  last_used: ISODate
}
```

**Indexes:**
- `user_id`
- `platform`
- `account_id`
- Compound: `user_id, platform`

---

### 6. `social_posts`
**Purpose:** Published and scheduled social media posts

```javascript
{
  _id: ObjectId,
  post_id: String (unique),
  user_id: String,
  campaign_id: String, // optional
  platforms: [
    {
      platform: String, // "facebook", "instagram", "twitter", "linkedin"
      account_id: String,
      platform_post_id: String, // ID returned by platform
      status: String, // "published", "failed", "scheduled"
      published_at: ISODate,
      error: String // if failed
    }
  ],
  content: {
    message: String,
    images: [String], // URLs
    videos: [String], // URLs
    link: String,
    hashtags: [String]
  },
  schedule: {
    scheduled: Boolean,
    publish_at: ISODate
  },
  analytics: {
    impressions: Number,
    reach: Number,
    engagement: Number,
    likes: Number,
    comments: Number,
    shares: Number,
    clicks: Number,
    last_synced: ISODate
  },
  created_at: ISODate,
  updated_at: ISODate
}
```

**Indexes:**
- `post_id`: unique
- `user_id`
- `campaign_id`
- `schedule.publish_at`
- `created_at`: descending

---

### 7. `zoho_crm_records`
**Purpose:** Cached CRM data from Zoho

```javascript
{
  _id: ObjectId,
  user_id: String,
  module: String, // "Contacts", "Leads", "Deals", "Accounts", "Campaigns"
  record_id: String, // Zoho record ID
  data: Object, // Full record data from Zoho
  synced_at: ISODate,
  created_at: ISODate,
  updated_at: ISODate
}
```

**Indexes:**
- Compound: `user_id, module`
- `record_id`
- `synced_at`: descending

---

### 8. `email_campaigns`
**Purpose:** Email marketing campaigns via Zoho

```javascript
{
  _id: ObjectId,
  campaign_id: String (unique),
  user_id: String,
  marketing_campaign_id: String, // Link to main campaign
  name: String,
  type: String, // "one_time", "drip", "automated"
  status: String, // "draft", "scheduled", "sent", "cancelled"
  recipients: {
    list_key: String, // Zoho mailing list
    segment: Object,
    count: Number
  },
  content: {
    subject: String,
    from_email: String,
    from_name: String,
    reply_to: String,
    html_content: String,
    text_content: String,
    attachments: [String]
  },
  schedule: {
    scheduled: Boolean,
    send_at: ISODate
  },
  zoho_campaign_key: String,
  analytics: {
    sent: Number,
    delivered: Number,
    opened: Number,
    clicked: Number,
    bounced: Number,
    unsubscribed: Number,
    open_rate: Number,
    click_rate: Number,
    last_synced: ISODate
  },
  created_at: ISODate,
  updated_at: ISODate,
  sent_at: ISODate
}
```

**Indexes:**
- `campaign_id`: unique
- `user_id`
- `status`
- `schedule.send_at`

---

### 9. `content_library`
**Purpose:** Generated content (text, images, videos)

```javascript
{
  _id: ObjectId,
  content_id: String (unique),
  user_id: String,
  campaign_id: String, // optional
  type: String, // "text", "image", "video", "audio"
  content_type: String, // "blog", "social_post", "ad_copy", "email", "seo_content"
  content: {
    text: String,
    image_url: String,
    image_base64: String,
    video_url: String,
    video_base64: String,
    audio_url: String,
    metadata: {
      prompt: String,
      model_used: String,
      generation_params: Object
    }
  },
  platform: String, // "facebook", "instagram", "blog", "email"
  status: String, // "draft", "approved", "published", "archived"
  tags: [String],
  created_by: String, // "ai", "user", "agent_name"
  created_at: ISODate,
  updated_at: ISODate,
  used_in: [String] // Array of post_ids or campaign_ids
}
```

**Indexes:**
- `content_id`: unique
- `user_id`
- `campaign_id`
- `type`
- `created_at`: descending

---

### 10. `user_memory`
**Purpose:** Vector memory for personalization (user-specific)

```javascript
{
  _id: ObjectId,
  user_id: String,
  memory_type: String, // "user_message", "agent_response", "preference", "insight"
  content: String,
  embedding: [Number], // OpenAI embedding vector
  metadata: {
    conversation_id: String,
    timestamp: ISODate,
    importance: Number, // 1-10
    category: String
  },
  agent_name: String,
  created_at: ISODate
}
```

**Indexes:**
- `user_id`
- `memory_type`
- `created_at`: descending
- Vector index on `embedding` (if MongoDB Atlas)

---

### 11. `agent_memory`
**Purpose:** Shared agent learnings

```javascript
{
  _id: ObjectId,
  agent_name: String,
  memory_type: String, // "pattern", "best_practice", "learning"
  content: String,
  embedding: [Number],
  metadata: {
    use_count: Number,
    success_rate: Number,
    category: String
  },
  created_at: ISODate,
  updated_at: ISODate
}
```

**Indexes:**
- `agent_name`
- `memory_type`
- Vector index on `embedding`

---

### 12. `global_memory`
**Purpose:** Platform-wide insights and patterns

```javascript
{
  _id: ObjectId,
  memory_type: String, // "trend", "insight", "pattern"
  content: String,
  embedding: [Number],
  metadata: {
    industry: String,
    effectiveness_score: Number,
    usage_count: Number
  },
  created_at: ISODate,
  updated_at: ISODate
}
```

**Indexes:**
- `memory_type`
- Vector index on `embedding`

---

### 13. `agent_events`
**Purpose:** Agent collaboration and activity log

```javascript
{
  _id: ObjectId,
  event_id: String (unique),
  conversation_id: String,
  user_id: String,
  agent_name: String,
  event_type: String, // "task_started", "task_completed", "message", "collaboration"
  data: Object,
  timestamp: ISODate
}
```

**Indexes:**
- Compound: `conversation_id, timestamp`
- `agent_name`
- `event_type`

---

### 14. `agent_tasks`
**Purpose:** Task execution tracking

```javascript
{
  _id: ObjectId,
  task_id: String (unique),
  campaign_id: String,
  agent_name: String,
  status: String, // "pending", "in_progress", "completed", "failed"
  input: Object,
  result: Object,
  error: String,
  started_at: ISODate,
  completed_at: ISODate,
  duration_ms: Number
}
```

**Indexes:**
- `task_id`: unique
- `campaign_id`
- `status`

---

### 15. `approval_requests`
**Purpose:** Content/campaign approval workflow

```javascript
{
  _id: ObjectId,
  request_id: String (unique),
  user_id: String,
  campaign_id: String,
  conversation_id: String,
  request_type: String, // "campaign_plan", "content", "budget", "publish"
  content: Object, // What needs approval
  status: String, // "pending", "approved", "rejected"
  requested_by: String, // agent_name
  approved_by: String, // user_id or "voice_approval"
  approval_notes: String,
  rejection_reason: String,
  created_at: ISODate,
  resolved_at: ISODate
}
```

**Indexes:**
- `request_id`: unique
- `user_id`
- `status`
- `created_at`: descending

---

### 16. `analytics_data`
**Purpose:** Aggregated analytics and insights

```javascript
{
  _id: ObjectId,
  user_id: String,
  campaign_id: String, // optional
  date: ISODate,
  metrics: {
    // Social Media
    social: {
      posts_published: Number,
      total_reach: Number,
      total_engagement: Number,
      total_impressions: Number,
      by_platform: {
        facebook: Object,
        instagram: Object,
        twitter: Object,
        linkedin: Object
      }
    },
    // Email
    email: {
      campaigns_sent: Number,
      emails_delivered: Number,
      open_rate: Number,
      click_rate: Number,
      conversions: Number
    },
    // CRM
    crm: {
      new_leads: Number,
      new_contacts: Number,
      deals_closed: Number,
      revenue: Number
    },
    // SEO
    seo: {
      organic_traffic: Number,
      keyword_rankings: Object,
      backlinks: Number
    },
    // PPC
    ppc: {
      ad_spend: Number,
      clicks: Number,
      conversions: Number,
      roas: Number
    }
  },
  created_at: ISODate
}
```

**Indexes:**
- Compound: `user_id, date`
- `campaign_id`
- `date`: descending

---

### 17. `settings`
**Purpose:** User configuration and preferences

```javascript
{
  _id: ObjectId,
  user_id: String (unique),
  api_keys: {
    openai_key: String (encrypted),
    custom_keys: Object
  },
  integrations: {
    zoho_connected: Boolean,
    social_platforms: [String],
    analytics_enabled: Boolean
  },
  notifications: {
    email: Boolean,
    in_app: Boolean,
    webhook_url: String
  },
  branding: {
    company_name: String,
    logo_url: String,
    primary_color: String,
    tone_of_voice: String
  },
  updated_at: ISODate
}
```

**Indexes:**
- `user_id`: unique

---

### 18. `webhooks`
**Purpose:** Webhook management for integrations

```javascript
{
  _id: ObjectId,
  user_id: String,
  webhook_id: String (unique),
  name: String,
  url: String,
  events: [String], // Events to trigger webhook
  secret: String,
  active: Boolean,
  last_triggered: ISODate,
  created_at: ISODate
}
```

**Indexes:**
- `webhook_id`: unique
- `user_id`
- `active`

---

### 19. `scheduled_jobs`
**Purpose:** Background job scheduling

```javascript
{
  _id: ObjectId,
  job_id: String (unique),
  user_id: String,
  job_type: String, // "post_social", "send_email", "sync_analytics"
  payload: Object,
  schedule: {
    execute_at: ISODate,
    recurring: Boolean,
    cron_expression: String // if recurring
  },
  status: String, // "pending", "processing", "completed", "failed"
  attempts: Number,
  max_attempts: Number,
  result: Object,
  error: String,
  created_at: ISODate,
  executed_at: ISODate
}
```

**Indexes:**
- `job_id`: unique
- `status`
- `schedule.execute_at`

---

### 20. `audit_log`
**Purpose:** Security and compliance audit trail

```javascript
{
  _id: ObjectId,
  user_id: String,
  action: String, // "login", "post_published", "campaign_created", etc.
  resource_type: String,
  resource_id: String,
  details: Object,
  ip_address: String,
  user_agent: String,
  timestamp: ISODate
}
```

**Indexes:**
- `user_id`
- `action`
- `timestamp`: descending

---

## Collection Relationships

```
users (1) -----> (many) campaigns
users (1) -----> (many) conversations
users (1) -----> (many) social_accounts
users (1) -----> (1) zoho_tokens
users (1) -----> (1) settings

campaigns (1) -----> (many) social_posts
campaigns (1) -----> (many) email_campaigns
campaigns (1) -----> (many) agent_tasks
campaigns (1) -----> (many) approval_requests

conversations (1) -----> (1) campaigns

social_accounts (many) -----> (many) social_posts

content_library (many) -----> (many) social_posts
content_library (many) -----> (many) email_campaigns
```

---

## Initialization Script

```javascript
// MongoDB initialization script
db.createCollection("users");
db.users.createIndex({ user_id: 1 }, { unique: true });
db.users.createIndex({ email: 1 }, { unique: true });

db.createCollection("conversations");
db.conversations.createIndex({ conversation_id: 1 }, { unique: true });
db.conversations.createIndex({ user_id: 1 });
db.conversations.createIndex({ updated_at: -1 });

db.createCollection("campaigns");
db.campaigns.createIndex({ campaign_id: 1 }, { unique: true });
db.campaigns.createIndex({ user_id: 1 });
db.campaigns.createIndex({ status: 1 });
db.campaigns.createIndex({ created_at: -1 });

db.createCollection("zoho_tokens");
db.zoho_tokens.createIndex({ user_id: 1 }, { unique: true });
db.zoho_tokens.createIndex({ expires_at: 1 });

db.createCollection("social_accounts");
db.social_accounts.createIndex({ user_id: 1, platform: 1 });
db.social_accounts.createIndex({ account_id: 1 });

db.createCollection("social_posts");
db.social_posts.createIndex({ post_id: 1 }, { unique: true });
db.social_posts.createIndex({ user_id: 1 });
db.social_posts.createIndex({ campaign_id: 1 });
db.social_posts.createIndex({ "schedule.publish_at": 1 });
db.social_posts.createIndex({ created_at: -1 });

db.createCollection("zoho_crm_records");
db.zoho_crm_records.createIndex({ user_id: 1, module: 1 });
db.zoho_crm_records.createIndex({ record_id: 1 });

db.createCollection("email_campaigns");
db.email_campaigns.createIndex({ campaign_id: 1 }, { unique: true });
db.email_campaigns.createIndex({ user_id: 1 });
db.email_campaigns.createIndex({ status: 1 });

db.createCollection("content_library");
db.content_library.createIndex({ content_id: 1 }, { unique: true });
db.content_library.createIndex({ user_id: 1 });
db.content_library.createIndex({ type: 1 });
db.content_library.createIndex({ created_at: -1 });

db.createCollection("user_memory");
db.user_memory.createIndex({ user_id: 1 });
db.user_memory.createIndex({ memory_type: 1 });
db.user_memory.createIndex({ created_at: -1 });

db.createCollection("agent_memory");
db.agent_memory.createIndex({ agent_name: 1 });
db.agent_memory.createIndex({ memory_type: 1 });

db.createCollection("global_memory");
db.global_memory.createIndex({ memory_type: 1 });

db.createCollection("agent_events");
db.agent_events.createIndex({ conversation_id: 1, timestamp: -1 });
db.agent_events.createIndex({ agent_name: 1 });

db.createCollection("agent_tasks");
db.agent_tasks.createIndex({ task_id: 1 }, { unique: true });
db.agent_tasks.createIndex({ campaign_id: 1 });
db.agent_tasks.createIndex({ status: 1 });

db.createCollection("approval_requests");
db.approval_requests.createIndex({ request_id: 1 }, { unique: true });
db.approval_requests.createIndex({ user_id: 1 });
db.approval_requests.createIndex({ status: 1 });
db.approval_requests.createIndex({ created_at: -1 });

db.createCollection("analytics_data");
db.analytics_data.createIndex({ user_id: 1, date: -1 });
db.analytics_data.createIndex({ campaign_id: 1 });

db.createCollection("settings");
db.settings.createIndex({ user_id: 1 }, { unique: true });

db.createCollection("webhooks");
db.webhooks.createIndex({ webhook_id: 1 }, { unique: true });
db.webhooks.createIndex({ user_id: 1 });

db.createCollection("scheduled_jobs");
db.scheduled_jobs.createIndex({ job_id: 1 }, { unique: true });
db.scheduled_jobs.createIndex({ status: 1 });
db.scheduled_jobs.createIndex({ "schedule.execute_at": 1 });

db.createCollection("audit_log");
db.audit_log.createIndex({ user_id: 1 });
db.audit_log.createIndex({ timestamp: -1 });

console.log("✅ All collections and indexes created successfully!");
```

---

**Total Collections:** 20
**Purpose:** Complete marketing automation platform with Zoho integration and social media management
