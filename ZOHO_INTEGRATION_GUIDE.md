# Complete Zoho Integration Guide

## Overview

This application now uses **Zoho** as the complete backend platform, replacing HubSpot. All marketing automation, email operations, campaign management, and data visualization are powered by Zoho services.

## Zoho Services Integrated

### 1. **Zoho OAuth 2.0 Authentication** (`zoho_auth_service.py`)
- Complete OAuth 2.0 authorization code flow
- Automatic token refresh (1-hour expiry handled automatically)
- Multi-service scope management
- Secure token storage in MongoDB

### 2. **Zoho CRM** (`zoho_crm_service.py`)
- Campaign creation and management
- Custom modules for tenants and credentials
- Records management (CRUD operations)
- Search and filtering with COQL
- Field metadata management

### 3. **Zoho Mail** (`zoho_mail_service.py`)
- Send individual and bulk emails
- Email scheduling
- Message management (folders, search)
- Email statistics and tracking

### 4. **Zoho Campaigns** (`zoho_campaigns_service.py`)
- Create and manage email marketing campaigns
- Mailing list management
- Campaign analytics (open rate, click rate, etc.)
- Schedule campaigns
- A/B testing support

### 5. **Zoho Analytics** (`zoho_analytics_service.py`)
- Create workspaces and tables
- Import data for visualization
- Generate charts (75+ types available)
- SQL queries on data
- Export reports in multiple formats

## Setup Instructions

### Step 1: Register Your App in Zoho API Console

1. Go to [Zoho API Console](https://api-console.zoho.com/)
2. Click **GET STARTED** or **ADD CLIENT**
3. Choose **Server-based Applications**
4. Fill in details:
   - **Client Name:** Your app name
   - **Homepage URL:** Your app URL (e.g., http://localhost:3000)
   - **Authorized Redirect URI:** Your callback URL (e.g., http://localhost:3000/zoho/callback)
5. Click **CREATE**
6. Copy your **Client ID** and **Client Secret**

### Step 2: Configure Environment Variables

Add these to your `backend/.env` file:

```bash
# Zoho OAuth Credentials
ZOHO_CLIENT_ID=your_client_id_here
ZOHO_CLIENT_SECRET=your_client_secret_here
ZOHO_REDIRECT_URI=http://localhost:3000/zoho/callback

# Existing variables
OPENAI_API_KEY=your_openai_key
MONGO_URL=your_mongodb_url
DB_NAME=your_database_name
```

### Step 3: Database Setup

The system will automatically create a `zoho_tokens` collection in MongoDB to store OAuth tokens securely.

### Step 4: Connect to Zoho

1. Start your backend and frontend
2. Navigate to Settings or Zoho Connections page
3. Click **Connect to Zoho**
4. You'll be redirected to Zoho for authorization
5. Grant permissions for all required scopes
6. You'll be redirected back to your app with a success message

## API Endpoints

### Authentication Endpoints

#### `GET /api/zoho/connect`
Initiate Zoho OAuth connection.

**Response:**
```json
{
  "authorization_url": "https://accounts.zoho.com/oauth/v2/auth?..."
}
```

#### `GET /api/zoho/callback`
OAuth callback endpoint (handled automatically).

#### `GET /api/zoho/status`
Check connection status.

**Response:**
```json
{
  "connected": true,
  "expires_at": "2025-01-26T15:30:00Z",
  "scope": "ZohoCRM.modules.ALL,ZohoMail.messages.ALL,..."
}
```

#### `POST /api/zoho/disconnect`
Disconnect Zoho integration.

### Campaign Management (Zoho CRM)

#### `POST /api/zoho/campaigns/create`
Create a marketing campaign.

**Request:**
```json
{
  "name": "Q1 2025 Campaign",
  "type": "Email",
  "status": "Planning",
  "start_date": "2025-02-01",
  "budget": 5000,
  "target_audience": "Small businesses",
  "goal": "Lead generation"
}
```

#### `GET /api/zoho/campaigns`
List all campaigns.

#### `GET /api/zoho/campaigns/{campaign_id}`
Get campaign details.

### Email Operations (Zoho Mail)

#### `POST /api/zoho/mail/send`
Send an email.

**Request:**
```json
{
  "to": ["customer@example.com"],
  "subject": "Welcome to our service!",
  "body": "<html><body><h1>Welcome!</h1></body></html>",
  "cc": ["manager@example.com"],
  "schedule_time": "2025-01-27T10:00:00Z"
}
```

#### `POST /api/zoho/mail/send-bulk`
Send personalized bulk emails.

**Request:**
```json
{
  "recipients": [
    {"email": "john@example.com", "name": "John", "company": "Acme"},
    {"email": "jane@example.com", "name": "Jane", "company": "TechCorp"}
  ],
  "subject_template": "Hello {name}!",
  "body_template": "<p>Hi {name}, Special offer for {company}!</p>"
}
```

### Email Campaigns (Zoho Campaigns)

#### `POST /api/zoho/campaigns/mailing-lists`
Create a mailing list.

#### `POST /api/zoho/campaigns/email-campaign`
Create and send email campaign.

**Request:**
```json
{
  "campaign_name": "Product Launch",
  "list_key": "abc123",
  "subject": "Introducing Our New Product",
  "from_email": "marketing@yourcompany.com",
  "html_content": "<html>...</html>",
  "schedule_time": "2025-01-28T09:00:00Z"
}
```

#### `GET /api/zoho/campaigns/{campaign_key}/stats`
Get campaign statistics.

**Response:**
```json
{
  "sent": 1000,
  "opened": 450,
  "clicked": 120,
  "open_rate": 45,
  "click_rate": 12,
  "bounced": 5,
  "unsubscribed": 2
}
```

### Data Visualization (Zoho Analytics)

#### `POST /api/zoho/analytics/workspace`
Create a workspace for data.

#### `POST /api/zoho/analytics/import-data`
Import data for visualization.

**Request:**
```json
{
  "workspace_id": "123456",
  "table_name": "Campaign_Performance",
  "data": [
    {"campaign": "Q1", "leads": 150, "conversions": 25},
    {"campaign": "Q2", "leads": 200, "conversions": 40}
  ]
}
```

#### `POST /api/zoho/analytics/create-chart`
Create a chart/visualization.

**Request:**
```json
{
  "workspace_id": "123456",
  "view_name": "Campaign Performance Bar Chart",
  "chart_config": {
    "chartType": "bar",
    "tableName": "Campaign_Performance",
    "xAxis": "campaign",
    "yAxis": "conversions",
    "aggregation": "sum"
  }
}
```

#### `GET /api/zoho/analytics/chart/{view_id}/data`
Get chart data for frontend visualization.

## Agent Integration

### EmailAgent with Zoho Mail

The `EmailAgent` now actually sends emails via Zoho Mail API:

```python
# EmailAgent generates content
email_content = await email_agent.execute(task)

# Zoho Mail sends the email
result = await zoho_mail_service.send_email(
    to=recipients,
    subject=email_content["subject"],
    body=email_content["body"]
)
```

### SocialMediaAgent Workflow

**Important:** Zoho Social has **NO API**. The workflow is:

1. `SocialMediaAgent` generates social media content
2. Content is stored in Zoho CRM as a record
3. User downloads or copies content
4. User manually posts to Zoho Social web interface

**Alternative:** Use Buffer or Hootsuite API for automated posting.

## Data Visualization in UI

### Example: Campaign Dashboard

```javascript
// Fetch data from Zoho Analytics
const response = await fetch(`/api/zoho/analytics/chart/${viewId}/data`);
const chartData = await response.json();

// Render with Chart.js
<Bar data={{
  labels: chartData.labels,
  datasets: [{
    label: 'Campaign Performance',
    data: chartData.values
  }]
}} />
```

### Available Chart Types

Zoho Analytics supports 75+ chart types:
- Bar, Line, Pie, Scatter, Area
- Funnel, Sankey, Sunburst
- Heatmap, Treemap, Bubble
- Racing charts, Sparklines
- Geo maps with layering

## Database Strategy

### Hybrid Approach (Recommended)

**MongoDB (Keep):**
- Real-time conversational data
- Vector embeddings for semantic search
- Session management
- Fast read/write operations

**Zoho Creator/CRM (New):**
- Structured campaign data
- Customer records
- Email tracking
- Analytics data
- Business intelligence

## Security Considerations

### Token Management
- Access tokens expire after 1 hour
- Automatic refresh handled by `ZohoAuthService`
- Refresh tokens stored securely in MongoDB
- All sensitive data encrypted at rest

### Credentials Storage
- Use Zoho CRM custom modules with encryption
- Field-level security
- Audit logging for all API calls

## Scopes Required

The following scopes are requested during OAuth:

```
ZohoCRM.modules.ALL          - Campaign management
ZohoCRM.settings.ALL         - Custom modules/fields
ZohoCRM.users.ALL            - User management
ZohoMail.messages.ALL        - Send/receive emails
ZohoMail.accounts.ALL        - Account management
ZohoCampaigns.campaign.ALL   - Email campaigns
ZohoCampaigns.contact.ALL    - Contact management
ZohoCreator.meta.ALL         - Database metadata
ZohoCreator.report.ALL       - Data operations
ZohoAnalytics.data.ALL       - Data visualization
ZohoAnalytics.workspace.ALL  - Workspace management
```

## Troubleshooting

### "No valid Zoho connection"
- Check if user has connected to Zoho
- Verify OAuth tokens are not expired
- Check MongoDB for `zoho_tokens` collection

### "Authentication failed"
- Verify Client ID and Client Secret
- Check Redirect URI matches exactly
- Ensure all scopes are requested

### "Token refresh failed"
- User may need to re-authorize
- Check if refresh token is valid
- Verify Zoho account has proper permissions

### Rate Limits
- Zoho CRM: 5000 API calls per day
- Zoho Mail: Depends on account type
- Zoho Campaigns: 100 API calls per minute

## Migration from HubSpot

### What's Removed
- HubSpot OAuth endpoints
- HubSpot token storage
- HubSpot-specific code in `server.py`

### What's Added
- Complete Zoho service layer
- Enhanced agent capabilities (actual sending/posting)
- Data visualization infrastructure
- Comprehensive campaign management

### Data Migration Steps
1. Export campaigns from HubSpot (if any)
2. Import to Zoho CRM using API
3. Update frontend to use new endpoints
4. Test thoroughly before going live

## Cost Considerations

### Zoho Pricing
- **Zoho CRM:** Free tier available, paid plans from $14/user/month
- **Zoho Mail:** Free tier available, paid from $1/user/month
- **Zoho Campaigns:** Free up to 2000 subscribers, paid from $3/month
- **Zoho Analytics:** Free tier available, paid from $22/month
- **Zoho Creator:** Free tier limited, paid from $10/user/month

### API Credits
- Custom module creation: 500 credits per module
- Plan accordingly for custom modules

## Support

For Zoho API issues:
- [Zoho Developer Documentation](https://www.zoho.com/developer/rest-api.html)
- [Zoho CRM API Docs](https://www.zoho.com/crm/developer/docs/)
- [Zoho Support](https://help.zoho.com/)

For application issues:
- Check backend logs
- Verify OAuth connection status
- Test API calls with Postman

---

**Integration Status:** ✅ Complete
**HubSpot Status:** ❌ Removed
**Backend:** Zoho
**Ready for Production:** After testing
