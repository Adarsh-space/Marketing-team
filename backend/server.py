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

# Import agent orchestrator, voice service, social media service, vector memory, and collaboration system
from agents.orchestrator import AgentOrchestrator
from voice_service import VoiceService
from social_media_service import SocialMediaService
from vector_memory_service import VectorMemoryService
from agent_collaboration_system import AgentCollaborationSystem

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']

# Configure SSL only for Atlas (srv:// protocol)
if "mongodb+srv://" in mongo_url:
    import certifi
    client = AsyncIOMotorClient(
        mongo_url,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=20000
    )
else:
    # Local MongoDB, no SSL
    client = AsyncIOMotorClient(mongo_url)

db = client[os.environ['DB_NAME']]

async def initialize_database():
    """Initialize database collections and indexes on startup."""
    try:
        logger.info("Initializing database collections...")
        
        # Get list of existing collections
        existing_collections = await db.list_collection_names()
        
        # Collections to create
        required_collections = [
            "conversations",
            "campaigns", 
            "user_memory",
            "agent_memory",
            "global_memory",
            "tenants",
            "agent_events",
            "agent_tasks",
            "hubspot_tokens",
            "settings",
            "published_content"
        ]
        
        # Create missing collections
        for collection_name in required_collections:
            if collection_name not in existing_collections:
                await db.create_collection(collection_name)
                logger.info(f"✅ Created collection: {collection_name}")
            else:
                logger.info(f"✓ Collection exists: {collection_name}")
        
        # Create indexes
        await db.conversations.create_index("conversation_id", unique=True)
        await db.campaigns.create_index("campaign_id", unique=True)
        await db.tenants.create_index("user_id", unique=True)
        await db.user_memory.create_index("user_id")
        await db.agent_memory.create_index("agent_name")
        await db.agent_events.create_index([("conversation_id", 1), ("timestamp", -1)])
        
        logger.info("✅ Database initialization complete!")
        
        # Test connection
        await db.command("ping")
        logger.info("✅ MongoDB Atlas connection successful!")
        
    except Exception as e:
        logger.error(f"❌ Database initialization error: {str(e)}")
        # Don't fail the app, continue with warnings
        pass

# Initialize services
orchestrator = AgentOrchestrator(db)
voice_service = VoiceService()
social_media_service = SocialMediaService()
vector_memory = VectorMemoryService(db)
collaboration_system = AgentCollaborationSystem(db)

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
    user_id: Optional[str] = "default_user"  # Added user_id field

class ChatResponse(BaseModel):
    type: str  # "conversation" | "campaign_created" | "image_generated" | "error"
    message: str
    conversation_id: str
    campaign_id: Optional[str] = None
    questions: Optional[List[str]] = []
    ready_to_plan: bool = False
    image_base64: Optional[str] = None  # For image generation
    prompt_used: Optional[str] = None  # DALL-E prompt used

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
    NOW WITH VECTOR MEMORY!
    """
    try:
        user_id = message.user_id or "default_user"
        
        # Generate conversation ID if not provided
        conversation_id = message.conversation_id or str(uuid.uuid4())
        
        # Get or create tenant for this user
        tenant = await vector_memory.get_or_create_tenant(user_id)
        
        # If new user, greet them
        if tenant["is_new"]:
            logger.info(f"New user detected: {user_id}, creating tenant")
        
        # Store user message in vector memory
        await vector_memory.store_memory(
            user_id=user_id,
            content=message.message,
            memory_type="user_message",
            metadata={"conversation_id": conversation_id}
        )
        
        # Get relevant context from vector memory
        context = await vector_memory.get_context_for_agent(
            user_id=user_id,
            agent_name="ConversationalAgent",
            query=message.message
        )
        
        # Publish event: User message received
        await collaboration_system.publish_event(
            agent_name="System",
            event_type="user_message_received",
            data={"message": message.message[:100]},
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        # Process message through orchestrator (with context)
        response = await orchestrator.process_user_message(
            user_message=message.message,
            conversation_id=conversation_id,
            vector_context=context  # Pass memory context
        )
        
        # Store agent response in vector memory
        agent_message = response.get("message", "")
        if agent_message:
            await vector_memory.store_memory(
                user_id=user_id,
                content=agent_message,
                memory_type="agent_response",
                agent_name="ConversationalAgent",
                metadata={"conversation_id": conversation_id}
            )
        
        # Publish event: Agent responded
        await collaboration_system.publish_event(
            agent_name="ConversationalAgent",
            event_type="agent_responded",
            data={"response_type": response.get("type")},
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        return ChatResponse(
            type=response.get("type", "conversation"),
            message=response.get("message", ""),
            conversation_id=conversation_id,
            campaign_id=response.get("campaign_id"),
            questions=response.get("questions", []),
            ready_to_plan=response.get("ready_to_plan", False),
            image_base64=response.get("image_base64"),  # Include image data
            prompt_used=response.get("prompt_used")  # Include DALL-E prompt
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

# ==================== Vector Memory Endpoints ====================

@api_router.post("/memory/search")
async def search_memories(data: Dict[str, Any]):
    """
    Semantic search in vector memory.
    
    Expected data:
    {
        "user_id": "user_id",
        "query": "search query",
        "limit": 5,
        "scope": "user" or "agent" or "global"
    }
    """
    try:
        user_id = data.get("user_id", "default_user")
        query = data.get("query", "")
        limit = data.get("limit", 5)
        scope = data.get("scope", "user")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        results = await vector_memory.search_memories(
            user_id=user_id,
            query=query,
            limit=limit,
            scope=scope
        )
        
        return {
            "status": "success",
            "results": results,
            "count": len(results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Memory search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/memory/profile/{user_id}")
async def get_user_profile(user_id: str):
    """Get user profile built from memories."""
    try:
        profile = await vector_memory.get_user_profile(user_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        return {
            "status": "success",
            "profile": profile
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Agent Collaboration Endpoints ====================

@api_router.get("/collaboration/events/{conversation_id}")
async def get_collaboration_events(conversation_id: str, limit: int = Query(default=50, le=100)):
    """
    Get all agent collaboration events for a conversation.
    Shows how agents are working together.
    """
    try:
        events = await collaboration_system.get_conversation_events(
            conversation_id=conversation_id,
            limit=limit
        )
        
        return {
            "status": "success",
            "events": events,
            "count": len(events)
        }
        
    except Exception as e:
        logger.error(f"Error getting collaboration events: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/collaboration/agent/{agent_name}")
async def get_agent_activity(agent_name: str, limit: int = Query(default=20, le=50)):
    """Get recent activity for a specific agent."""
    try:
        activity = await collaboration_system.get_agent_activity(
            agent_name=agent_name,
            limit=limit
        )
        
        return {
            "status": "success",
            "agent": agent_name,
            "activity": activity,
            "count": len(activity)
        }
        
    except Exception as e:
        logger.error(f"Error getting agent activity: {str(e)}")
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

# ==================== Individual Agent Chat ====================

@api_router.post("/agent-chat")
async def agent_chat(data: Dict[str, Any]):
    """
    Chat with individual agents directly with vector memory context.
    Returns natural conversation instead of JSON.
    """
    try:
        agent_id = data.get("agent_id")
        message = data.get("message")
        user_id = data.get("user_id", "default_user")
        conversation_id = data.get("conversation_id", str(uuid.uuid4()))

        # Get the specific agent
        agent = orchestrator.agents.get(agent_id)

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Get or create tenant for this user
        await vector_memory.get_or_create_tenant(user_id)

        # Store user message in vector memory
        await vector_memory.store_memory(
            user_id=user_id,
            content=message,
            memory_type="user_message",
            agent_name=agent_id,
            metadata={"conversation_id": conversation_id}
        )

        # Get relevant context from vector memory for this specific agent
        context = await vector_memory.get_context_for_agent(
            user_id=user_id,
            agent_name=agent_id,
            query=message
        )

        # Publish collaboration event
        await collaboration_system.publish_event(
            agent_name=agent_id,
            event_type="task_started",
            data={"task": "direct_chat", "message": message[:100]},
            user_id=user_id,
            conversation_id=conversation_id
        )

        # Prepare task payload with vector context
        task_payload = {
            "task_id": "direct_chat",
            "user_message": message,
            "vector_context": context,  # Add vector context
            "campaign_brief": {"product": "User inquiry", "target_audience": "General"},
            "previous_results": {}
        }

        # Execute agent with message and context
        result = await agent.execute(task_payload)

        # Extract response string from result
        agent_result = result.get("result", {})

        # Clean the response to natural language
        from utils.response_formatter import clean_agent_response
        response_text = clean_agent_response(agent_result)

        # Store agent response in vector memory
        await vector_memory.store_memory(
            user_id=user_id,
            content=response_text,
            memory_type="agent_response",
            agent_name=agent_id,
            metadata={"conversation_id": conversation_id}
        )

        # Publish completion event
        await collaboration_system.publish_event(
            agent_name=agent_id,
            event_type="task_completed",
            data={"task": "direct_chat"},
            user_id=user_id,
            conversation_id=conversation_id
        )

        return {"response": response_text}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Image Generation Endpoints ====================

@api_router.post("/generate-image")
async def generate_image(data: Dict[str, Any]):
    """
    Generate marketing image using AI.
    
    Expected data:
    {
        "content": "Marketing content/post text",
        "brand_info": "Brand information (optional)",
        "platform": "Target platform like Instagram, Facebook (optional)",
        "conversation_id": "conversation_id to get context (optional)"
    }
    """
    try:
        content = data.get("content", "")
        brand_info = data.get("brand_info", "")
        platform = data.get("platform", "social media")
        conversation_id = data.get("conversation_id")
        
        # If conversation_id provided, get additional context
        if conversation_id:
            conversation = await db.conversations.find_one({"conversation_id": conversation_id})
            if conversation:
                # Extract brand info from conversation history
                messages = conversation.get("messages", [])
                for msg in messages:
                    if msg.get("role") == "user":
                        user_content = msg.get("content", "")
                        # Look for website mentions or brand names
                        if "website" in user_content.lower() or ".com" in user_content:
                            brand_info += f" {user_content}"
        
        # Get ImageGenerationAgent
        image_agent = orchestrator.agents.get("ImageGenerationAgent")
        
        if not image_agent:
            raise HTTPException(status_code=500, detail="Image generation agent not available")
        
        # Generate image
        logger.info(f"Generating image for content: {content[:100]}...")
        result = await image_agent.generate_image_from_context({
            "content": content,
            "brand_info": brand_info,
            "platform": platform
        })
        
        if result.get("status") == "success":
            return {
                "status": "success",
                "image_base64": result.get("image_base64"),
                "prompt": result.get("prompt_used"),
                "message": "Image generated successfully!"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "Image generation failed")
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/generate-video")
async def generate_video(data: Dict[str, Any]):
    """
    Generate marketing video using Sora AI.

    Expected data:
    {
        "content": "Marketing message/product description",
        "brand_info": "Brand information (optional)",
        "platform": "Target platform like TikTok, Instagram Reels, YouTube",
        "duration": Duration in seconds (4-20),
        "resolution": "720p or 1080p",
        "conversation_id": "conversation_id to get context (optional)"
    }
    """
    try:
        content = data.get("content", "")
        brand_info = data.get("brand_info", "")
        platform = data.get("platform", "Instagram Reels")
        duration = data.get("duration", 10)
        resolution = data.get("resolution", "1080p")
        conversation_id = data.get("conversation_id")

        # Validate duration (Sora supports 4-20 seconds)
        if duration < 4:
            duration = 4
        elif duration > 20:
            duration = 20

        # If conversation_id provided, get additional context
        if conversation_id:
            conversation = await db.conversations.find_one({"conversation_id": conversation_id})
            if conversation:
                messages = conversation.get("messages", [])
                for msg in messages:
                    if msg.get("role") == "user":
                        user_content = msg.get("content", "")
                        if "website" in user_content.lower() or ".com" in user_content:
                            brand_info += f" {user_content}"

        # Get MultiModelVideoAgent
        video_agent = orchestrator.agents.get("MultiModelVideoAgent")
        
        if not video_agent:
            raise HTTPException(status_code=500, detail="Video generation agent not available")

        # Generate video
        logger.info(f"Generating video for content: {content[:100]}...")
        result = await video_agent.generate_video_from_context({
            "content": content,
            "brand_info": brand_info,
            "platform": platform,
            "duration": duration,
            "resolution": resolution
        })

        if result.get("status") == "success":
            return {
                "status": "success",
                "video_base64": result.get("video_base64"),
                "prompt": result.get("prompt_used"),
                "duration": result.get("duration"),
                "resolution": result.get("resolution"),
                "message": "Video generated successfully!"
            }
        elif result.get("status") == "concept_only":
            # Sora not available, return concept
            return {
                "status": "concept_only",
                "video_concept": result.get("video_concept"),
                "duration": result.get("duration"),
                "resolution": result.get("resolution"),
                "message": result.get("message"),
                "note": result.get("note")
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "Video generation failed")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Settings Endpoints ====================

@api_router.get("/settings")
async def get_settings(user_id: str = "default_user"):
    """Get user settings and credentials."""
    try:
        settings = await db.settings.find_one(
            {"user_id": user_id},
            {"_id": 0}
        )
        
        if not settings:
            return {"credentials": {}}
        
        return settings
        
    except Exception as e:
        logger.error(f"Error fetching settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/settings")
async def save_settings(data: Dict[str, Any], user_id: str = "default_user"):
    """Save user settings and credentials."""
    try:
        settings = {
            "user_id": user_id,
            "credentials": data.get("credentials", {}),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.settings.update_one(
            {"user_id": user_id},
            {"$set": settings},
            upsert=True
        )
        
        return {"status": "success", "message": "Settings saved"}
        
    except Exception as e:
        logger.error(f"Error saving settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Social Media Publishing Endpoints ====================

@api_router.post("/publish")
async def publish_content(data: Dict[str, Any]):
    """
    Publish content to social media platforms.
    
    Expected data:
    {
        "platforms": ["facebook", "instagram"],
        "content": {
            "message": "Post text",
            "image_url": "https://...",
            "link": "https://..."
        },
        "user_id": "default_user"
    }
    """
    try:
        platforms = data.get("platforms", [])
        content = data.get("content", {})
        user_id = data.get("user_id", "default_user")
        
        if not platforms:
            raise HTTPException(status_code=400, detail="No platforms specified")
        
        # Get credentials from settings
        settings = await db.settings.find_one({"user_id": user_id})
        
        if not settings:
            raise HTTPException(
                status_code=404,
                detail="No credentials found. Please configure social media credentials in settings."
            )
        
        credentials = settings.get("credentials", {})
        
        # Validate required credentials based on platforms
        if "facebook" in platforms:
            if not credentials.get("facebook_page_id") or not credentials.get("facebook_access_token"):
                raise HTTPException(
                    status_code=400,
                    detail="Facebook credentials not configured. Please add Facebook Page ID and Access Token in settings."
                )
        
        if "instagram" in platforms:
            if not credentials.get("instagram_account_id"):
                raise HTTPException(
                    status_code=400,
                    detail="Instagram credentials not configured. Please add Instagram Business Account ID in settings."
                )
        
        # Publish to platforms
        results = await social_media_service.publish_to_multiple_platforms(
            platforms=platforms,
            credentials=credentials,
            content=content
        )
        
        # Store publishing record in database
        publishing_record = {
            "user_id": user_id,
            "platforms": platforms,
            "content": content,
            "results": results,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await db.published_content.insert_one(publishing_record)
        
        return {
            "status": "success",
            "results": results,
            "timestamp": publishing_record["timestamp"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/publish/history")
async def get_publish_history(
    user_id: str = "default_user",
    limit: int = Query(default=20, le=100)
):
    """Get publishing history for a user."""
    try:
        history = await db.published_content.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        return {
            "history": history,
            "count": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error fetching publish history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Voice Endpoints ====================

@api_router.post("/voice/speech-to-text")
async def speech_to_text(
    audio: UploadFile = File(...),
    language: Optional[str] = Form(None)
):
    """
    Convert speech to text using OpenAI Whisper.
    Supports multiple languages with auto-detection.
    """
    try:
        # Read audio file
        audio_data = await audio.read()
        audio_file = io.BytesIO(audio_data)
        audio_file.name = audio.filename or "audio.webm"
        
        # Transcribe
        transcript = await voice_service.speech_to_text(
            audio_file=audio_file,
            language=language
        )
        
        return {
            "transcript": transcript,
            "language": language or "auto-detected"
        }
        
    except Exception as e:
        logger.error(f"Speech-to-text error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/voice/text-to-speech")
async def text_to_speech(
    data: Dict[str, Any]
):
    """
    Convert text to speech using OpenAI TTS.
    Automatically detects language from text.
    """
    try:
        text = data.get("text")
        voice = data.get("voice", "nova")
        speed = data.get("speed", 1.0)
        
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        # Generate speech
        audio_data = await voice_service.text_to_speech(
            text=text,
            voice=voice,
            speed=speed
        )
        
        # Return audio as streaming response
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=speech.mp3"
            }
        )
        
    except Exception as e:
        logger.error(f"Text-to-speech error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/voice/languages")
async def get_supported_languages():
    """
    Get list of supported languages for voice interaction.
    """
    return {
        "languages": voice_service.SUPPORTED_LANGUAGES,
        "voices": voice_service.AVAILABLE_VOICES
    }

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

# HubSpot OAuth callback (root level to match redirect URI)
@app.get("/callback")
async def hubspot_oauth_callback(code: str = None, error: str = None):
    """Handle HubSpot OAuth callback at root level."""
    try:
        if error:
            logger.error(f"OAuth error: {error}")
            return RedirectResponse(url=f"{os.environ.get('REACT_APP_FRONTEND_URL', 'http://localhost:3000')}/?error={error}")
        
        if not code:
            raise HTTPException(status_code=400, detail="No authorization code provided")
        
        # Exchange code for access token
        token_url = "https://api.hubapi.com/oauth/v1/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": os.environ.get('HUBSPOT_CLIENT_ID'),
            "client_secret": os.environ.get('HUBSPOT_CLIENT_SECRET'),
            "redirect_uri": os.environ.get('HUBSPOT_REDIRECT_URI'),
            "code": code
        }
        
        response = requests.post(token_url, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            
            # Store tokens in database
            await db.hubspot_tokens.update_one(
                {"user_id": "default_user"},
                {
                    "$set": {
                        "access_token": token_data.get("access_token"),
                        "refresh_token": token_data.get("refresh_token"),
                        "expires_in": token_data.get("expires_in"),
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                },
                upsert=True
            )
            
            logger.info("HubSpot OAuth successful")
            
            # Redirect to frontend success page
            return RedirectResponse(url=f"{os.environ.get('REACT_APP_FRONTEND_URL', 'http://localhost:3000')}/settings?hubspot=connected")
        else:
            error_msg = response.json().get("message", "Unknown error")
            logger.error(f"Token exchange failed: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
            
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        return RedirectResponse(url=f"{os.environ.get('REACT_APP_FRONTEND_URL', 'http://localhost:3000')}/?error=oauth_failed")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    """Initialize database on startup."""
    await initialize_database()
    logger.info("✅ Application startup complete")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    logger.info("Application shutdown complete")
