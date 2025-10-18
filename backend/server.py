from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, Query, UploadFile, File, Form
from fastapi.responses import RedirectResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import httpx
from authlib.integrations.starlette_client import OAuth
import io

# Import agent orchestrator and voice service
from agents.orchestrator import AgentOrchestrator
from voice_service import VoiceService

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize orchestrator and voice service
orchestrator = AgentOrchestrator(db)
voice_service = VoiceService()

# Create the main app
app = FastAPI(
    title="AI Marketing Automation Platform",
    description="Multi-agent AI marketing platform with conversational interface",
    version="1.0.0"
)

# Create router with /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== Models ====================

class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    type: str  # "conversation" | "campaign_created" | "error"
    message: str
    conversation_id: str
    campaign_id: Optional[str] = None
    questions: Optional[List[str]] = []
    ready_to_plan: bool = False

class CampaignBrief(BaseModel):
    product: str
    target_audience: str
    objective: str
    budget: Optional[str] = "Flexible"
    timeline: Optional[str] = "30-60 days"
    channels: List[str] = ["Email", "Social Media", "PPC", "SEO"]
    additional_context: Optional[str] = ""

class Campaign(BaseModel):
    campaign_id: str
    brief: Dict[str, Any]
    status: str
    created_at: str
    plan: Optional[Dict[str, Any]] = None
    results: Optional[Dict[str, Any]] = None

class HubSpotConnection(BaseModel):
    user_id: str
    access_token: str
    refresh_token: str
    expires_at: int
    portal_id: str
    created_at: str

# ==================== Chat Endpoints ====================

@api_router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """
    Process user message through Conversational Interface Agent.
    Gathers requirements and creates campaigns when ready.
    """
    try:
        # Generate conversation ID if not provided
        conversation_id = message.conversation_id or str(uuid.uuid4())
        
        # Process message through orchestrator
        response = await orchestrator.process_user_message(
            user_message=message.message,
            conversation_id=conversation_id
        )
        
        return ChatResponse(
            type=response.get("type", "conversation"),
            message=response.get("message", ""),
            conversation_id=conversation_id,
            campaign_id=response.get("campaign_id"),
            questions=response.get("questions", []),
            ready_to_plan=response.get("ready_to_plan", False)
        )
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Get conversation history.
    """
    try:
        conversation = await db.conversations.find_one(
            {"conversation_id": conversation_id},
            {"_id": 0}
        )
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return conversation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Campaign Endpoints ====================

@api_router.post("/campaigns")
async def create_campaign(brief: CampaignBrief, background_tasks: BackgroundTasks):
    """
    Create a new campaign from a brief.
    Starts plan execution in background.
    """
    try:
        # Create campaign
        campaign = await orchestrator.create_campaign(brief.model_dump())
        campaign_id = campaign["campaign_id"]
        
        # Start execution in background (but we'll do it synchronously per requirements)
        # Execute campaign plan immediately (synchronous)
        result = await orchestrator.execute_campaign_plan(campaign_id)
        
        return {
            "campaign_id": campaign_id,
            "status": "completed",
            "message": "Campaign executed successfully",
            "plan": result.get("plan"),
            "results": result.get("results")
        }
        
    except Exception as e:
        logger.error(f"Error creating campaign: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/campaigns/{campaign_id}")
async def get_campaign(campaign_id: str):
    """
    Get campaign details including plan and results.
    """
    try:
        campaign = await orchestrator.get_campaign(campaign_id)
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        return campaign
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching campaign: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/campaigns/{campaign_id}/execute")
async def execute_campaign(campaign_id: str):
    """
    Execute a campaign plan (run all agents).
    """
    try:
        result = await orchestrator.execute_campaign_plan(campaign_id)
        return result
        
    except Exception as e:
        logger.error(f"Error executing campaign: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/campaigns")
async def list_campaigns(limit: int = Query(default=50, le=100)):
    """
    List all campaigns.
    """
    try:
        campaigns = await orchestrator.list_campaigns(limit=limit)
        return {"campaigns": campaigns, "count": len(campaigns)}
        
    except Exception as e:
        logger.error(f"Error listing campaigns: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== HubSpot OAuth Endpoints ====================

@api_router.get("/oauth/hubspot/authorize")
async def hubspot_authorize():
    """
    Redirect user to HubSpot OAuth authorization page.
    """
    client_id = os.environ.get('HUBSPOT_CLIENT_ID')
    redirect_uri = os.environ.get('HUBSPOT_REDIRECT_URI')
    
    # HubSpot OAuth URL
    scopes = [
        "crm.objects.contacts.read",
        "crm.objects.contacts.write",
        "crm.objects.companies.read",
        "crm.objects.companies.write",
        "crm.objects.deals.read",
        "crm.objects.deals.write"
    ]
    
    auth_url = (
        f"https://app.hubspot.com/oauth/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={' '.join(scopes)}"
    )
    
    return {"authorization_url": auth_url}

@api_router.get("/oauth/hubspot/callback")
async def hubspot_callback(code: str):
    """
    Handle HubSpot OAuth callback and exchange code for tokens.
    """
    try:
        client_id = os.environ.get('HUBSPOT_CLIENT_ID')
        client_secret = os.environ.get('HUBSPOT_CLIENT_SECRET')
        redirect_uri = os.environ.get('HUBSPOT_REDIRECT_URI')
        
        # Exchange code for access token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.hubapi.com/oauth/v1/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "code": code
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"HubSpot OAuth error: {response.text}"
                )
            
            tokens = response.json()
            
            # Get user info
            access_token = tokens["access_token"]
            user_response = await client.get(
                "https://api.hubapi.com/oauth/v1/access-tokens/" + access_token
            )
            user_info = user_response.json()
            
            # Store connection in database
            connection = {
                "user_id": user_info.get("user_id", "default_user"),
                "portal_id": user_info.get("hub_id"),
                "access_token": access_token,
                "refresh_token": tokens["refresh_token"],
                "expires_at": tokens["expires_in"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "token_type": tokens["token_type"]
            }
            
            await db.hubspot_connections.update_one(
                {"user_id": connection["user_id"]},
                {"$set": connection},
                upsert=True
            )
            
            # Redirect to frontend success page
            frontend_url = os.environ.get('REACT_APP_BACKEND_URL', '').replace('/api', '')
            return RedirectResponse(url=f"{frontend_url}/?hubspot_connected=true")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"HubSpot OAuth error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/hubspot/status")
async def hubspot_status(user_id: str = "default_user"):
    """
    Check HubSpot connection status.
    """
    try:
        connection = await db.hubspot_connections.find_one(
            {"user_id": user_id},
            {"_id": 0, "access_token": 0, "refresh_token": 0}
        )
        
        if not connection:
            return {"connected": False}
        
        return {
            "connected": True,
            "portal_id": connection.get("portal_id"),
            "connected_at": connection.get("created_at")
        }
        
    except Exception as e:
        logger.error(f"Error checking HubSpot status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Analytics Endpoints ====================

@api_router.get("/analytics/dashboard")
async def get_dashboard():
    """
    Get dashboard analytics summary.
    """
    try:
        # Get campaign stats
        total_campaigns = await db.campaigns.count_documents({})
        active_campaigns = await db.campaigns.count_documents({"status": {"$in": ["planning", "executing"]}})
        completed_campaigns = await db.campaigns.count_documents({"status": "completed"})
        
        # Get recent campaigns
        recent = await db.campaigns.find(
            {},
            {"_id": 0, "campaign_id": 1, "brief": 1, "status": 1, "created_at": 1}
        ).sort("created_at", -1).limit(5).to_list(5)
        
        return {
            "stats": {
                "total_campaigns": total_campaigns,
                "active_campaigns": active_campaigns,
                "completed_campaigns": completed_campaigns
            },
            "recent_campaigns": recent
        }
        
    except Exception as e:
        logger.error(f"Error fetching dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Health Check ====================

@api_router.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check MongoDB connection
        await db.command('ping')
        
        return {
            "status": "healthy",
            "database": "connected",
            "agents": list(orchestrator.agents.keys())
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@api_router.get("/")
async def root():
    return {
        "message": "AI Marketing Automation Platform API",
        "version": "1.0.0",
        "agents": list(orchestrator.agents.keys())
    }

# Include router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    logger.info("Application shutdown complete")
