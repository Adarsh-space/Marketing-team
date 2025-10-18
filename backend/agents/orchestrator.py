from typing import Dict, Any, List
import logging
import uuid
from datetime import datetime, timezone
import asyncio

from .conversational_agent import ConversationalAgent
from .planning_agent import PlanningAgent
from .market_research_agent import MarketResearchAgent
from .content_agent import ContentAgent
from .email_agent import EmailAgent
from .social_media_agent import SocialMediaAgent
from .seo_agent import SEOAgent
from .ppc_agent import PPCAgent
from .analytics_agent import AnalyticsAgent
from .reporting_agent import ReportingAgent

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """
    Central orchestrator that manages the lifecycle of marketing campaigns.
    Routes tasks to appropriate agents and manages their execution.
    """
    
    def __init__(self, db):
        self.db = db
        self.agents = {
            "ConversationalAgent": ConversationalAgent(),
            "PlanningAgent": PlanningAgent(),
            "MarketResearchAgent": MarketResearchAgent(),
            "ContentAgent": ContentAgent(),
            "EmailAgent": EmailAgent(),
            "SocialMediaAgent": SocialMediaAgent(),
            "SEOAgent": SEOAgent(),
            "PPCAgent": PPCAgent(),
            "AnalyticsAgent": AnalyticsAgent(),
            "ReportingAgent": ReportingAgent()
        }
        logger.info("AgentOrchestrator initialized with all agents")
    
    async def process_user_message(self, user_message: str, conversation_id: str) -> Dict[str, Any]:
        """
        Process a user message through the Conversational Interface Agent.
        """
        try:
            # Get conversation history
            conversation = await self.db.conversations.find_one({"conversation_id": conversation_id})
            
            if not conversation:
                # Create new conversation
                conversation = {
                    "conversation_id": conversation_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "messages": []
                }
                await self.db.conversations.insert_one(conversation)
            
            # Add user message to history
            user_msg = {
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Process with Conversational Agent
            cia = self.agents["ConversationalAgent"]
            response = await cia.execute({
                "user_message": user_message,
                "conversation_history": conversation.get("messages", [])
            })
            
            # Add assistant response to history
            assistant_msg = {
                "role": "assistant",
                "content": response.get("result", {}).get("response", ""),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Update conversation
            await self.db.conversations.update_one(
                {"conversation_id": conversation_id},
                {
                    "$push": {"messages": {"$each": [user_msg, assistant_msg]}},
                    "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
                }
            )
            
            result = response.get("result", {})
            
            # Check if ready to create campaign
            if result.get("ready_to_plan"):
                campaign_brief = result.get("campaign_brief", {})
                campaign = await self.create_campaign(campaign_brief, conversation_id)
                
                return {
                    "type": "campaign_created",
                    "message": "Great! I've created your campaign plan. Let me start working on it.",
                    "campaign_id": campaign["campaign_id"],
                    "ready_to_plan": True
                }
            else:
                return {
                    "type": "conversation",
                    "message": result.get("response", ""),
                    "questions": result.get("questions", []),
                    "ready_to_plan": False
                }
                
        except Exception as e:
            logger.error(f"Error processing user message: {str(e)}")
            return {
                "type": "error",
                "message": "I encountered an error processing your request. Please try again.",
                "error": str(e)
            }
    
    async def create_campaign(self, campaign_brief: Dict[str, Any], conversation_id: str = None) -> Dict[str, Any]:
        """
        Create a new campaign from a brief.
        """
        try:
            campaign_id = str(uuid.uuid4())
            
            # Create campaign document
            campaign = {
                "campaign_id": campaign_id,
                "conversation_id": conversation_id,
                "brief": campaign_brief,
                "status": "planning",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "plan": None,
                "tasks": [],
                "results": {}
            }
            
            await self.db.campaigns.insert_one(campaign)
            logger.info(f"Created campaign: {campaign_id}")
            
            return campaign
            
        except Exception as e:
            logger.error(f"Error creating campaign: {str(e)}")
            raise
    
    async def execute_campaign_plan(self, campaign_id: str) -> Dict[str, Any]:
        """
        Execute a campaign plan by orchestrating all agent tasks.
        This runs synchronously as per requirements.
        """
        try:
            campaign = await self.db.campaigns.find_one({"campaign_id": campaign_id})
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")
            
            logger.info(f"Starting campaign execution: {campaign_id}")
            
            # Step 1: Generate plan using Planning Agent
            await self._update_campaign_status(campaign_id, "planning")
            planning_agent = self.agents["PlanningAgent"]
            plan_response = await planning_agent.execute({
                "campaign_brief": campaign["brief"],
                "task_id": "planning"
            })
            
            plan = plan_response.get("result", {})
            await self.db.campaigns.update_one(
                {"campaign_id": campaign_id},
                {"$set": {"plan": plan, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            
            # Step 2: Execute tasks in order (respecting dependencies)
            tasks = plan.get("tasks", [])
            task_results = {}
            
            for task in tasks:
                task_id = task.get("task_id")
                agent_name = task.get("agent_assigned")
                
                # Check dependencies
                dependencies = task.get("dependencies", [])
                if dependencies:
                    # Ensure all dependencies are completed
                    for dep in dependencies:
                        if dep not in task_results:
                            logger.warning(f"Dependency {dep} not completed for {task_id}")
                
                # Execute task
                await self._update_campaign_status(campaign_id, f"executing_{task_id}")
                agent = self.agents.get(agent_name)
                
                if not agent:
                    logger.error(f"Agent {agent_name} not found for task {task_id}")
                    continue
                
                # Prepare task payload with context from previous tasks
                task_payload = task.get("payload", {})
                task_payload["task_id"] = task_id
                task_payload["campaign_brief"] = campaign["brief"]
                task_payload["plan"] = plan
                task_payload["previous_results"] = task_results
                
                logger.info(f"Executing task: {task_id} with agent: {agent_name}")
                result = await agent.execute(task_payload)
                
                # Store task result
                task_results[task_id] = result
                
                # Save task to database
                task_doc = {
                    "task_id": task_id,
                    "campaign_id": campaign_id,
                    "agent": agent_name,
                    "status": result.get("status"),
                    "result": result.get("result"),
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }
                await self.db.tasks.insert_one(task_doc)
            
            # Step 3: Update campaign with results
            await self._update_campaign_status(campaign_id, "completed")
            await self.db.campaigns.update_one(
                {"campaign_id": campaign_id},
                {
                    "$set": {
                        "results": task_results,
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            logger.info(f"Campaign {campaign_id} execution completed")
            
            return {
                "campaign_id": campaign_id,
                "status": "completed",
                "plan": plan,
                "results": task_results
            }
            
        except Exception as e:
            logger.error(f"Error executing campaign: {str(e)}")
            await self._update_campaign_status(campaign_id, "failed")
            raise
    
    async def _update_campaign_status(self, campaign_id: str, status: str):
        """Update campaign status in database."""
        await self.db.campaigns.update_one(
            {"campaign_id": campaign_id},
            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
    
    async def get_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Get campaign details."""
        campaign = await self.db.campaigns.find_one({"campaign_id": campaign_id}, {"_id": 0})
        return campaign
    
    async def list_campaigns(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List all campaigns."""
        campaigns = await self.db.campaigns.find({}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
        return campaigns
