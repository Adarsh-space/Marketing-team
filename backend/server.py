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
from agents.integrated_supervisor import IntegratedSupervisor
from voice_service import VoiceService
from social_media_service import SocialMediaService
from vector_memory_service import VectorMemoryService
from agent_collaboration_system import AgentCollaborationSystem

# Import Zoho services
from zoho_auth_service import ZohoAuthService
from zoho_crm_service import ZohoCRMService
from zoho_mail_service import ZohoMailService
from zoho_campaigns_service import ZohoCampaignsService
from zoho_analytics_service import ZohoAnalyticsService

# Import social media integration service
from social_media_integration_service import SocialMediaIntegrationService

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
            "zoho_tokens",  # Zoho OAuth tokens
            "social_credentials",  # Social media credentials
            "settings",
            "published_content",
            "approval_requests"  # Approval workflow
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
integrated_supervisor = IntegratedSupervisor(db)  # New integrated supervisor
voice_service = VoiceService()
social_media_service = SocialMediaService()
vector_memory = VectorMemoryService(db)
collaboration_system = AgentCollaborationSystem(db)

# Initialize Zoho services
zoho_auth = ZohoAuthService(db)
zoho_crm = ZohoCRMService(zoho_auth)
zoho_mail = ZohoMailService(zoho_auth)
zoho_campaigns = ZohoCampaignsService(zoho_auth)
zoho_analytics = ZohoAnalyticsService(zoho_auth)

# Initialize social media integration service
social_media_integration = SocialMediaIntegrationService(zoho_crm, db)

# Update SocialMediaAgent with social media service
from agents.social_media_agent import SocialMediaAgent
social_media_agent = SocialMediaAgent(social_media_integration)

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

        # Check if user requested image or video generation
        image_base64 = None
        video_concept = None
        prompt_used = None

        # Detect image generation requests
        image_keywords = ["create image", "generate image", "make image", "design image",
                         "create visual", "generate visual", "create graphic", "generate graphic",
                         "create picture", "show me image", "create post", "generate post",
                         "make post", "design post", "create poster", "make poster", "design poster"]

        video_keywords = ["create video", "generate video", "make video", "design video",
                         "create clip", "video concept", "video storyboard", "make clip",
                         "create reel", "make reel", "video script"]

        message_lower = message.lower()

        # Generate image if requested
        if any(keyword in message_lower for keyword in image_keywords):
            try:
                image_agent = orchestrator.agents.get("ImageGenerationAgent")
                if image_agent:
                    img_result = await image_agent.generate_image_from_context({
                        "content": message,
                        "platform": "social media",
                        "brand_info": ""
                    })
                    if img_result.get("status") == "success":
                        image_base64 = img_result.get("image_base64")
                        prompt_used = img_result.get("prompt_used")
                    else:
                        # Image generation failed, append error to response
                        error_msg = img_result.get("message", "Image generation failed")
                        response_text += f"\n\n[Error: {error_msg}]"
                else:
                    response_text += "\n\n[Error: ImageGenerationAgent not found]"
            except Exception as e:
                response_text += f"\n\n[Error generating image: {str(e)}]"

        # Generate video concept if requested
        elif any(keyword in message_lower for keyword in video_keywords):
            try:
                from agents.video_generation_agent import VideoGenerationAgent
                video_agent = VideoGenerationAgent()
                video_result = await video_agent.generate_video_concept({
                    "content": message,
                    "platform": "Instagram Reels",
                    "duration": 30,
                    "style": "modern and engaging",
                    "goal": "engagement"
                })
                if "error" not in video_result:
                    video_concept = video_result
                else:
                    error_msg = video_result.get("details", "Video generation failed")
                    response_text += f"\n\n[Error: {error_msg}]"
            except Exception as e:
                response_text += f"\n\n[Error generating video: {str(e)}]"

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

        return {
            "response": response_text,
            "image_base64": image_base64,
            "video_concept": video_concept,
            "prompt_used": prompt_used,
            "conversation_id": conversation_id
        }

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

# ==================== Approval Workflow Endpoints ====================

@api_router.post("/integrated/chat")
async def integrated_chat(message: ChatMessage):
    """
    Process user message through integrated supervisor system.
    Uses LangChain multi-agent system for complex tasks.
    """
    try:
        user_id = message.user_id or "default_user"
        conversation_id = message.conversation_id or str(uuid.uuid4())

        # Get or create tenant
        await vector_memory.get_or_create_tenant(user_id)

        # Store user message
        await vector_memory.store_memory(
            user_id=user_id,
            content=message.message,
            memory_type="user_message",
            metadata={"conversation_id": conversation_id}
        )

        # Process with integrated supervisor
        result = await integrated_supervisor.process_request(
            user_request=message.message,
            conversation_id=conversation_id,
            use_langchain=True
        )

        # Store agent response
        if result.get("type") != "error":
            await vector_memory.store_memory(
                user_id=user_id,
                content=str(result.get("result", "")),
                memory_type="agent_response",
                metadata={"conversation_id": conversation_id}
            )

        return {
            **result,
            "conversation_id": conversation_id
        }

    except Exception as e:
        logger.error(f"Integrated chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/approvals/pending")
async def get_pending_approvals(conversation_id: Optional[str] = None):
    """
    Get all pending approval requests.
    """
    try:
        approvals = await integrated_supervisor.get_pending_approvals(conversation_id)
        return {
            "status": "success",
            "approvals": approvals,
            "count": len(approvals)
        }
    except Exception as e:
        logger.error(f"Error getting pending approvals: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/approvals/{request_id}/approve")
async def approve_request(request_id: str, data: Optional[Dict[str, Any]] = None):
    """
    Approve a pending request.
    """
    try:
        notes = data.get("notes") if data else None
        result = await integrated_supervisor.approve_request(request_id, notes)
        return result
    except Exception as e:
        logger.error(f"Error approving request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/approvals/{request_id}/reject")
async def reject_request(request_id: str, data: Optional[Dict[str, Any]] = None):
    """
    Reject a pending request.
    """
    try:
        notes = data.get("notes") if data else None
        result = await integrated_supervisor.reject_request(request_id, notes)
        return result
    except Exception as e:
        logger.error(f"Error rejecting request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/approvals/{request_id}/voice")
async def process_voice_approval(request_id: str, data: Dict[str, Any]):
    """
    Process voice-based approval response.
    Expected data: {"user_response": "approve" | "reject"}
    """
    try:
        user_response = data.get("user_response", "")
        result = await integrated_supervisor.process_voice_approval(
            request_id=request_id,
            user_response=user_response
        )
        return result
    except Exception as e:
        logger.error(f"Error processing voice approval: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/approvals/{request_id}/voice-prompt")
async def get_voice_approval_prompt(request_id: str):
    """
    Get voice prompt for an approval request.
    """
    try:
        prompt = await integrated_supervisor.get_voice_approval_prompt(request_id)
        return prompt
    except Exception as e:
        logger.error(f"Error getting voice prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/agent-communication")
async def get_agent_communication():
    """
    Get all agent-to-agent communication logs.
    """
    try:
        communication = integrated_supervisor.get_agent_communication()
        return {
            "status": "success",
            "communication": communication,
            "count": len(communication)
        }
    except Exception as e:
        logger.error(f"Error getting agent communication: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Zoho Integration Endpoints ====================

@api_router.get("/zoho/connect")
async def zoho_connect(user_id: str = "default_user"):
    """Initiate Zoho OAuth connection."""
    try:
        state = str(uuid.uuid4())
        auth_url = zoho_auth.get_authorization_url(state=state)
        return {
            "status": "success",
            "authorization_url": auth_url,
            "state": state
        }
    except Exception as e:
        logger.error(f"Error initiating Zoho OAuth: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/zoho/callback")
async def zoho_callback(code: str, state: str):
    """Handle Zoho OAuth callback."""
    try:
        result = await zoho_auth.exchange_code_for_tokens(
            authorization_code=code,
            user_id="default_user"
        )

        if result.get("status") == "success":
            return RedirectResponse(
                url=f"{os.environ.get('REACT_APP_FRONTEND_URL', 'http://localhost:3000')}/settings?zoho=connected"
            )
        else:
            return RedirectResponse(
                url=f"{os.environ.get('REACT_APP_FRONTEND_URL', 'http://localhost:3000')}/settings?zoho=error"
            )
    except Exception as e:
        logger.error(f"Zoho OAuth callback error: {str(e)}")
        return RedirectResponse(
            url=f"{os.environ.get('REACT_APP_FRONTEND_URL', 'http://localhost:3000')}/settings?zoho=error"
        )

@api_router.get("/zoho/status")
async def zoho_status(user_id: str = "default_user"):
    """Check Zoho connection status."""
    try:
        status = await zoho_auth.get_connection_status(user_id)
        return status
    except Exception as e:
        logger.error(f"Error checking Zoho status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/zoho/disconnect")
async def zoho_disconnect(user_id: str = "default_user"):
    """Disconnect Zoho integration."""
    try:
        result = await zoho_auth.revoke_token(user_id)
        return result
    except Exception as e:
        logger.error(f"Error disconnecting Zoho: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Zoho CRM Endpoints ====================

@api_router.post("/zoho/campaigns/create")
async def create_zoho_campaign(data: Dict[str, Any], user_id: str = "default_user"):
    """Create campaign in Zoho CRM."""
    try:
        result = await zoho_crm.create_campaign(data, user_id)
        return result
    except Exception as e:
        logger.error(f"Error creating campaign: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/zoho/campaigns")
async def list_zoho_campaigns(user_id: str = "default_user", page: int = 1, per_page: int = 20):
    """List all campaigns from Zoho CRM."""
    try:
        result = await zoho_crm.list_campaigns(user_id, page, per_page)
        return result
    except Exception as e:
        logger.error(f"Error listing campaigns: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/zoho/campaigns/{campaign_id}")
async def get_zoho_campaign(campaign_id: str, user_id: str = "default_user"):
    """Get campaign details from Zoho CRM."""
    try:
        result = await zoho_crm.get_campaign(campaign_id, user_id)
        return result
    except Exception as e:
        logger.error(f"Error getting campaign: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/zoho/campaigns/{campaign_id}")
async def update_zoho_campaign(campaign_id: str, updates: Dict[str, Any], user_id: str = "default_user"):
    """Update campaign in Zoho CRM."""
    try:
        result = await zoho_crm.update_campaign(campaign_id, updates, user_id)
        return result
    except Exception as e:
        logger.error(f"Error updating campaign: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Zoho Mail Endpoints ====================

@api_router.post("/zoho/mail/send")
async def send_zoho_mail(data: Dict[str, Any], user_id: str = "default_user"):
    """
    Send email via Zoho Mail.

    Expected data:
    {
        "to": ["email@example.com"],
        "subject": "Email subject",
        "body": "<html>Email body</html>",
        "cc": ["cc@example.com"],  # optional
        "bcc": ["bcc@example.com"],  # optional
        "schedule_time": "2025-01-27T10:00:00Z"  # optional
    }
    """
    try:
        result = await zoho_mail.send_email(
            user_id=user_id,
            to=data.get("to"),
            subject=data.get("subject"),
            body=data.get("body"),
            cc=data.get("cc"),
            bcc=data.get("bcc"),
            schedule_time=data.get("schedule_time")
        )
        return result
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/zoho/mail/send-bulk")
async def send_bulk_zoho_mail(data: Dict[str, Any], user_id: str = "default_user"):
    """
    Send bulk personalized emails.

    Expected data:
    {
        "recipients": [
            {"email": "john@example.com", "name": "John", "company": "Acme"},
            {"email": "jane@example.com", "name": "Jane", "company": "TechCorp"}
        ],
        "subject_template": "Hello {name}!",
        "body_template": "<p>Hi {name}, Special offer for {company}!</p>"
    }
    """
    try:
        result = await zoho_mail.send_bulk_email(
            user_id=user_id,
            recipients=data.get("recipients"),
            subject_template=data.get("subject_template"),
            body_template=data.get("body_template")
        )
        return result
    except Exception as e:
        logger.error(f"Error sending bulk email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/zoho/mail/messages")
async def get_zoho_messages(folder_id: str = "1", page: int = 1, limit: int = 20, user_id: str = "default_user"):
    """Get messages from Zoho Mail folder."""
    try:
        result = await zoho_mail.get_messages(folder_id, page, limit, user_id)
        return result
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Zoho Campaigns Endpoints ====================

@api_router.post("/zoho/campaigns/mailing-lists")
async def create_mailing_list(data: Dict[str, Any], user_id: str = "default_user"):
    """Create mailing list in Zoho Campaigns."""
    try:
        result = await zoho_campaigns.create_mailing_list(
            list_name=data.get("list_name"),
            list_description=data.get("description", ""),
            user_id=user_id
        )
        return result
    except Exception as e:
        logger.error(f"Error creating mailing list: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/zoho/campaigns/email-campaign")
async def create_email_campaign(data: Dict[str, Any], user_id: str = "default_user"):
    """Create email campaign in Zoho Campaigns."""
    try:
        result = await zoho_campaigns.create_campaign(
            campaign_name=data.get("campaign_name"),
            list_key=data.get("list_key"),
            subject=data.get("subject"),
            from_email=data.get("from_email"),
            html_content=data.get("html_content"),
            user_id=user_id
        )
        return result
    except Exception as e:
        logger.error(f"Error creating email campaign: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/zoho/campaigns/send")
async def send_campaign(data: Dict[str, Any], user_id: str = "default_user"):
    """Send or schedule email campaign."""
    try:
        result = await zoho_campaigns.send_campaign(
            campaign_key=data.get("campaign_key"),
            schedule_time=data.get("schedule_time"),
            user_id=user_id
        )
        return result
    except Exception as e:
        logger.error(f"Error sending campaign: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/zoho/campaigns/{campaign_key}/stats")
async def get_campaign_stats(campaign_key: str, user_id: str = "default_user"):
    """Get campaign statistics."""
    try:
        result = await zoho_campaigns.get_campaign_statistics(campaign_key, user_id)
        return result
    except Exception as e:
        logger.error(f"Error getting campaign stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Zoho Analytics Endpoints ====================

@api_router.post("/zoho/analytics/workspace")
async def create_analytics_workspace(data: Dict[str, Any], user_id: str = "default_user"):
    """Create workspace in Zoho Analytics."""
    try:
        result = await zoho_analytics.create_workspace(
            workspace_name=data.get("workspace_name"),
            description=data.get("description", ""),
            user_id=user_id
        )
        return result
    except Exception as e:
        logger.error(f"Error creating workspace: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/zoho/analytics/import-data")
async def import_analytics_data(data: Dict[str, Any], user_id: str = "default_user"):
    """Import data to Zoho Analytics."""
    try:
        result = await zoho_analytics.import_data(
            workspace_id=data.get("workspace_id"),
            table_name=data.get("table_name"),
            data=data.get("data"),
            import_type=data.get("import_type", "append"),
            user_id=user_id
        )
        return result
    except Exception as e:
        logger.error(f"Error importing data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/zoho/analytics/create-chart")
async def create_analytics_chart(data: Dict[str, Any], user_id: str = "default_user"):
    """Create chart in Zoho Analytics."""
    try:
        result = await zoho_analytics.create_chart(
            workspace_id=data.get("workspace_id"),
            view_name=data.get("view_name"),
            chart_config=data.get("chart_config"),
            user_id=user_id
        )
        return result
    except Exception as e:
        logger.error(f"Error creating chart: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/zoho/analytics/chart/{view_id}/data")
async def get_chart_data(workspace_id: str, view_id: str, user_id: str = "default_user"):
    """Get chart data from Zoho Analytics."""
    try:
        result = await zoho_analytics.get_chart_data(workspace_id, view_id, user_id)
        return result
    except Exception as e:
        logger.error(f"Error getting chart data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Social Media Integration Endpoints ====================

@api_router.get("/social-media/facebook/connect")
async def facebook_connect(user_id: str = "default_user"):
    """Initiate Facebook OAuth connection."""
    try:
        state = str(uuid.uuid4())
        auth_url = await social_media_integration.get_facebook_oauth_url(
            client_id=os.environ.get('FACEBOOK_APP_ID'),
            redirect_uri=os.environ.get('FACEBOOK_REDIRECT_URI'),
            state=state
        )
        return {
            "status": "success",
            "authorization_url": auth_url,
            "state": state
        }
    except Exception as e:
        logger.error(f"Error initiating Facebook OAuth: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/social-media/facebook/callback")
async def facebook_callback(code: str, state: str):
    """Handle Facebook OAuth callback."""
    try:
        token_result = await social_media_integration.exchange_facebook_code(
            code=code,
            client_id=os.environ.get('FACEBOOK_APP_ID'),
            client_secret=os.environ.get('FACEBOOK_APP_SECRET'),
            redirect_uri=os.environ.get('FACEBOOK_REDIRECT_URI')
        )

        if token_result.get("status") == "success":
            # Save credentials
            await social_media_integration.save_credentials(
                user_id="default_user",
                platform="facebook",
                credentials={"access_token": token_result.get("access_token")},
                auth_type="oauth"
            )

            return RedirectResponse(
                url=f"{os.environ.get('REACT_APP_FRONTEND_URL', 'http://localhost:3000')}/settings?facebook=connected"
            )
        else:
            return RedirectResponse(
                url=f"{os.environ.get('REACT_APP_FRONTEND_URL', 'http://localhost:3000')}/settings?facebook=error"
            )
    except Exception as e:
        logger.error(f"Facebook OAuth callback error: {str(e)}")
        return RedirectResponse(
            url=f"{os.environ.get('REACT_APP_FRONTEND_URL', 'http://localhost:3000')}/settings?facebook=error"
        )

@api_router.post("/social-media/credentials")
async def save_social_credentials(data: Dict[str, Any]):
    """
    Save social media credentials.

    Expected data:
    {
        "user_id": "user123",
        "platform": "facebook|instagram",
        "credentials": {"access_token": "..."} or {"username": "...", "password": "..."},
        "auth_type": "oauth|password"
    }
    """
    try:
        result = await social_media_integration.save_credentials(
            user_id=data.get("user_id", "default_user"),
            platform=data.get("platform"),
            credentials=data.get("credentials"),
            auth_type=data.get("auth_type", "oauth")
        )
        return result
    except Exception as e:
        logger.error(f"Error saving credentials: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/social-media/facebook/pages")
async def get_facebook_pages(user_id: str = "default_user"):
    """Get user's Facebook pages."""
    try:
        result = await social_media_integration.get_user_pages(user_id)
        return result
    except Exception as e:
        logger.error(f"Error getting Facebook pages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/social-media/instagram/accounts")
async def get_instagram_accounts(user_id: str = "default_user"):
    """Get user's Instagram Business accounts."""
    try:
        result = await social_media_integration.get_instagram_accounts(user_id)
        return result
    except Exception as e:
        logger.error(f"Error getting Instagram accounts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/social-media/credentials/{platform}")
async def delete_social_credentials(platform: str, user_id: str = "default_user"):
    """Disconnect social media account."""
    try:
        result = await social_media_integration.delete_credentials(user_id, platform)
        return result
    except Exception as e:
        logger.error(f"Error deleting credentials: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/social-media/facebook/post")
async def post_to_facebook(data: Dict[str, Any]):
    """
    Post to Facebook page.

    Expected data:
    {
        "user_id": "user123",
        "message": "Post content",
        "image_url": "https://...",  # optional
        "link": "https://...",  # optional
        "page_id": "page123"  # optional
    }
    """
    try:
        result = await social_media_integration.post_to_facebook(
            user_id=data.get("user_id", "default_user"),
            message=data.get("message"),
            page_id=data.get("page_id"),
            image_url=data.get("image_url"),
            link=data.get("link")
        )
        return result
    except Exception as e:
        logger.error(f"Error posting to Facebook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/social-media/instagram/post")
async def post_to_instagram(data: Dict[str, Any]):
    """
    Post to Instagram Business account.

    Expected data:
    {
        "user_id": "user123",
        "image_url": "https://...",  # required
        "caption": "Post caption",
        "instagram_account_id": "insta123"  # required
    }
    """
    try:
        result = await social_media_integration.post_to_instagram(
            user_id=data.get("user_id", "default_user"),
            image_url=data.get("image_url"),
            caption=data.get("caption"),
            instagram_account_id=data.get("instagram_account_id")
        )
        return result
    except Exception as e:
        logger.error(f"Error posting to Instagram: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/social-media/ai-post")
async def ai_generate_and_post(data: Dict[str, Any]):
    """
    Generate content with AI and post to social media.

    Expected data:
    {
        "user_id": "user123",
        "prompt": "Create Instagram post about our new product",
        "platform": "facebook|instagram",
        "auto_post": true,
        "page_id": "page123",  # for Facebook
        "instagram_account_id": "insta123"  # for Instagram
    }
    """
    try:
        # Generate content using SocialMediaAgent
        content_result = await social_media_agent.execute({
            "task_id": str(uuid.uuid4()),
            "user_message": data.get("prompt"),
            "campaign_brief": {"product": "AI-generated post", "target_audience": "General"}
        })

        # Extract posting content
        if data.get("auto_post"):
            post_result = await social_media_agent.post_to_platform(
                user_id=data.get("user_id", "default_user"),
                platform=data.get("platform"),
                content={
                    "message": content_result.get("content", {}).get("caption", ""),
                    "image_url": data.get("image_url"),
                    "hashtags": content_result.get("hashtag_strategy", {}).get("brand_hashtags", [])
                }
            )

            return {
                "status": "success",
                "generated_content": content_result,
                "post_result": post_result
            }
        else:
            return {
                "status": "success",
                "generated_content": content_result,
                "message": "Content generated. Use /post endpoint to publish."
            }

    except Exception as e:
        logger.error(f"Error in AI post: {str(e)}")
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

@app.on_event("startup")
async def startup_db_client():
    """Initialize database on startup."""
    await initialize_database()
    logger.info("✅ Application startup complete")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    logger.info("Application shutdown complete")
