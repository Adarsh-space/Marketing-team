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
from .image_generation_agent import ImageGenerationAgent
from .video_generation_agent import VideoGenerationAgent
from .multi_model_video_agent import MultiModelVideoAgent
from .scraping_agent import ScrapingAgent
from .approval_workflow import ApprovalWorkflowManager, ApprovalType

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """
    Central orchestrator that manages the lifecycle of marketing campaigns.
    Routes tasks to appropriate agents and manages their execution.
    Now integrated with Zoho CRM for data storage!
    """

    def __init__(self, db, zoho_crm_service=None):
        self.db = db
        self.zoho_crm_service = zoho_crm_service
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
            "ReportingAgent": ReportingAgent(),
            "ImageGenerationAgent": ImageGenerationAgent(),
            "VideoGenerationAgent": VideoGenerationAgent(),
            "MultiModelVideoAgent": MultiModelVideoAgent(),
            "ScrapingAgent": ScrapingAgent()
        }
        # Initialize approval workflow manager
        self.approval_manager = ApprovalWorkflowManager(db)
        logger.info("AgentOrchestrator initialized with all agents including ScrapingAgent, ApprovalWorkflow, and Zoho CRM integration")
    
    async def process_user_message(
        self,
        user_message: str,
        conversation_id: str,
        vector_context: str = None
    ) -> Dict[str, Any]:
        """
        Process a user message through the Conversational Interface Agent.
        Now with vector memory context and approval handling!
        """
        try:
            # Get conversation history
            conversation = await self.db.conversations.find_one({"conversation_id": conversation_id})

            if not conversation:
                # Create new conversation
                conversation = {
                    "conversation_id": conversation_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "messages": [],
                    "pending_approval": None
                }
                await self.db.conversations.insert_one(conversation)

            # Check if there's a pending approval for this conversation
            pending_approval = conversation.get("pending_approval")

            if pending_approval:
                # User is responding to approval request
                user_response_lower = user_message.lower().strip()

                if any(word in user_response_lower for word in ["approve", "approved", "yes", "okay", "ok", "proceed", "go ahead", "confirm"]):
                    # User approved!
                    campaign_id = pending_approval["campaign_id"]
                    approval_request_id = pending_approval["approval_request_id"]

                    # Approve the campaign
                    logger.info(f"User approved campaign {campaign_id} via chat")

                    await self.approval_manager.approve_request(approval_request_id)

                    # Execute the campaign
                    result = await self.execute_campaign_with_approval(
                        campaign_id=campaign_id,
                        approval_request_id=approval_request_id
                    )

                    # Clear pending approval
                    await self.db.conversations.update_one(
                        {"conversation_id": conversation_id},
                        {"$set": {"pending_approval": None}}
                    )

                    # Return execution result
                    return {
                        "type": "campaign_executing",
                        "message": "Great! I'm executing your campaign now. Agents are working together...\n\nI'll let you know when it's complete!",
                        "campaign_id": campaign_id,
                        "ready_to_plan": True,
                        "execution_started": True
                    }

                elif any(word in user_response_lower for word in ["reject", "rejected", "no", "cancel", "stop", "decline"]):
                    # User rejected
                    campaign_id = pending_approval["campaign_id"]
                    approval_request_id = pending_approval["approval_request_id"]

                    logger.info(f"User rejected campaign {campaign_id} via chat")

                    await self.approval_manager.reject_request(
                        approval_request_id,
                        notes="User rejected via chat"
                    )

                    # Clear pending approval
                    await self.db.conversations.update_one(
                        {"conversation_id": conversation_id},
                        {"$set": {"pending_approval": None}}
                    )

                    return {
                        "type": "campaign_rejected",
                        "message": "No problem! Campaign cancelled. What else can I help you with?",
                        "ready_to_plan": False
                    }
            
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
                "conversation_history": conversation.get("messages", []),
                "vector_context": vector_context  # ADD THIS!
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
            
            # Check if user wants image generation
            if result.get("image_request"):
                image_context = result.get("image_context", {})
                image_agent = self.agents.get("ImageGenerationAgent")
                
                if image_agent:
                    logger.info("User requested image generation, creating image...")
                    # Get conversation context for brand info
                    brand_info = ""
                    for msg in conversation.get("messages", [])[-5:]:
                        if "website" in msg.get("content", "").lower():
                            brand_info += msg.get("content", "") + " "
                    
                    image_context["brand_info"] = brand_info
                    image_result = await image_agent.generate_image_from_context(image_context)
                    
                    return {
                        "type": "image_generated",
                        "message": result.get("response", "Here's your generated image!"),
                        "image_base64": image_result.get("image_base64"),
                        "prompt_used": image_result.get("prompt_used"),
                        "ready_to_plan": False
                    }
            
            # Check if ready to create campaign
            if result.get("ready_to_plan"):
                campaign_brief = result.get("campaign_brief", {})

                # Use NEW approval workflow
                campaign_result = await self.create_campaign_with_approval(
                    campaign_brief=campaign_brief,
                    conversation_id=conversation_id
                )

                # Format approval request for user
                approval_request = campaign_result.get("approval_request", {})
                plan = campaign_result.get("plan", {})

                # Create user-friendly message
                message = f"""Perfect! I've created an execution plan for your campaign.

CAMPAIGN PLAN:
{plan.get('summary', 'Multi-step marketing campaign')}

AGENTS INVOLVED:
"""
                tasks = plan.get("tasks", [])
                for task in tasks[:5]:  # Show first 5 tasks
                    agent = task.get("agent_assigned", "Unknown")
                    desc = task.get("description", "")
                    message += f"- {agent}: {desc}\n"

                if len(tasks) > 5:
                    message += f"... and {len(tasks) - 5} more tasks\n"

                message += f"""
ESTIMATED COST: {approval_request.get('details', {}).get('estimated_cost', 'TBD')}
TIMELINE: {approval_request.get('details', {}).get('estimated_duration', 'Based on task complexity')}

Please review the plan and approve to start execution. Once approved, agents will work together to complete all tasks.

Reply 'approve' to proceed or 'reject' to cancel.
"""

                # Store pending approval in conversation
                await self.db.conversations.update_one(
                    {"conversation_id": conversation_id},
                    {"$set": {
                        "pending_approval": {
                            "campaign_id": campaign_result["campaign_id"],
                            "approval_request_id": approval_request["request_id"]
                        }
                    }}
                )

                return {
                    "type": "awaiting_approval",
                    "message": message,
                    "campaign_id": campaign_result["campaign_id"],
                    "approval_request_id": approval_request["request_id"],
                    "plan": plan,
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
            
            # Return campaign without MongoDB _id
            return {
                "campaign_id": campaign_id,
                "conversation_id": conversation_id,
                "brief": campaign_brief,
                "status": "planning",
                "created_at": campaign["created_at"],
                "updated_at": campaign["updated_at"],
                "plan": None,
                "tasks": [],
                "results": {}
            }
            
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
                # Only pass serializable data to avoid circular references
                task_payload = {
                    "task_id": task_id,
                    "campaign_brief": campaign["brief"],
                    "task_description": task.get("description", ""),
                    "task_requirements": task.get("requirements", []),
                    # Zoho CRM integration
                    "campaign_id": campaign.get("zoho_campaign_id", campaign_id),  # Use Zoho campaign ID if available
                    "zoho_crm_service": self.zoho_crm_service,  # Zoho CRM service instance
                    "user_id": campaign.get("user_id", campaign["brief"].get("user_id", "default_user"))  # For Zoho auth
                }

                # Add scraping-specific parameters for ScrapingAgent
                if agent_name == "ScrapingAgent":
                    brief = campaign["brief"]
                    task_payload.update({
                        "scraping_source": "google_maps",  # or from brief
                        "query": brief.get("target_audience", "businesses"),
                        "location": brief.get("location", brief.get("target_location", "United States")),
                        "max_results": brief.get("contact_count", 50)
                    })

                # Add previous task results but ensure they're clean
                if task_results:
                    task_payload["previous_results"] = {
                        task_name: {
                            "status": result.get("status"),
                            "agent": result.get("agent"),
                            "result": result.get("result", {})  # Include result data for agent collaboration
                        } for task_name, result in task_results.items()
                    }

                logger.info(f"Executing task: {task_id} with agent: {agent_name} (Zoho CRM: {'enabled' if self.zoho_crm_service else 'disabled'})")
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
            
            # Return clean data without MongoDB ObjectIds
            # Convert any complex objects to serializable format
            clean_plan = self._clean_for_json(plan)
            clean_results = self._clean_for_json(task_results)
            
            return {
                "campaign_id": campaign_id,
                "status": "completed",
                "plan": clean_plan,
                "results": clean_results
            }
            
        except Exception as e:
            logger.error(f"Error executing campaign: {str(e)}")
            await self._update_campaign_status(campaign_id, "failed")
            raise
    
    def _clean_for_json(self, data: Any) -> Any:
        """
        Recursively clean data for JSON serialization.
        Removes MongoDB ObjectIds and converts non-serializable types.
        """
        if isinstance(data, dict):
            return {k: self._clean_for_json(v) for k, v in data.items() if k != '_id'}
        elif isinstance(data, list):
            return [self._clean_for_json(item) for item in data]
        elif hasattr(data, '__dict__'):
            # Handle objects with __dict__
            return str(data)
        else:
            return data
    
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

    async def create_campaign_with_approval(
        self,
        campaign_brief: Dict[str, Any],
        conversation_id: str = None
    ) -> Dict[str, Any]:
        """
        Create campaign and request approval before execution.
        This is the NEW workflow with approval.

        Steps:
        1. Create campaign
        2. Generate plan with Planning Agent
        3. Create approval request
        4. Return plan and approval_request_id to frontend
        5. Wait for user approval
        6. Execute when approved
        """
        try:
            # Step 1: Create campaign in MongoDB
            campaign = await self.create_campaign(campaign_brief, conversation_id)
            campaign_id = campaign["campaign_id"]

            # Step 1.5: Create campaign in Zoho CRM (if available)
            zoho_campaign_id = None
            if self.zoho_crm_service:
                try:
                    logger.info(f"Creating campaign {campaign_id} in Zoho CRM...")
                    zoho_result = await self.zoho_crm_service.create_campaign(
                        campaign_data={
                            "name": campaign_brief.get("product", "Campaign") + f" - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
                            "status": "Planning",
                            "type": "Email",
                            "budget": campaign_brief.get("budget", 0),
                            "description": campaign_brief.get("objective", ""),
                            "target_audience": campaign_brief.get("target_audience", ""),
                            "product": campaign_brief.get("product", ""),
                            "goal": campaign_brief.get("objective", "")
                        },
                        user_id=campaign_brief.get("user_id", "default_user")
                    )
                    if zoho_result.get("status") == "success":
                        zoho_campaign_id = zoho_result["campaign_id"]
                        logger.info(f"Created Zoho CRM campaign: {zoho_campaign_id}")
                        # Store Zoho campaign ID in MongoDB campaign
                        await self.db.campaigns.update_one(
                            {"campaign_id": campaign_id},
                            {"$set": {"zoho_campaign_id": zoho_campaign_id}}
                        )
                    else:
                        logger.warning(f"Failed to create Zoho campaign: {zoho_result.get('message')}")
                except Exception as e:
                    logger.error(f"Error creating Zoho campaign: {str(e)}")
                    # Continue without Zoho CRM

            # Step 2: Generate plan
            await self._update_campaign_status(campaign_id, "planning")
            planning_agent = self.agents["PlanningAgent"]
            plan_response = await planning_agent.execute({
                "campaign_brief": campaign_brief,
                "task_id": "planning"
            })

            plan = plan_response.get("result", {})
            await self.db.campaigns.update_one(
                {"campaign_id": campaign_id},
                {"$set": {"plan": plan, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )

            # Step 3: Create approval request
            approval_request = await self.approval_manager.create_campaign_approval_request(
                campaign_brief=campaign_brief,
                plan=plan,
                conversation_id=conversation_id
            )

            # Store approval request ID in campaign
            await self.db.campaigns.update_one(
                {"campaign_id": campaign_id},
                {"$set": {
                    "approval_request_id": approval_request.request_id,
                    "status": "awaiting_approval"
                }}
            )

            logger.info(f"Campaign {campaign_id} created and awaiting approval")

            return {
                "campaign_id": campaign_id,
                "status": "awaiting_approval",
                "plan": self._clean_for_json(plan),
                "approval_request": approval_request.to_dict(),
                "message": "Campaign plan created. Please review and approve to proceed."
            }

        except Exception as e:
            logger.error(f"Error creating campaign with approval: {str(e)}")
            raise

    async def execute_campaign_with_approval(
        self,
        campaign_id: str,
        approval_request_id: str
    ) -> Dict[str, Any]:
        """
        Execute campaign after approval.
        This checks approval status before executing.
        """
        try:
            # Check approval status
            approval_request = await self.approval_manager.get_approval_request(approval_request_id)

            if not approval_request:
                # Check in database
                db_request = await self.db.approval_requests.find_one(
                    {"request_id": approval_request_id}
                )
                if not db_request or db_request.get("status") != "approved":
                    return {
                        "status": "error",
                        "message": "Campaign execution not approved"
                    }
            elif approval_request.status.value != "approved":
                return {
                    "status": "error",
                    "message": f"Campaign is {approval_request.status.value}, not approved"
                }

            # Execute campaign
            logger.info(f"Executing approved campaign: {campaign_id}")
            result = await self.execute_campaign_plan(campaign_id)

            return result

        except Exception as e:
            logger.error(f"Error executing campaign with approval: {str(e)}")
            raise

    async def get_campaign_status_stream(self, campaign_id: str):
        """
        Generator function for streaming campaign execution status.
        Yields updates as tasks complete.
        """
        campaign = await self.db.campaigns.find_one({"campaign_id": campaign_id})
        if not campaign:
            yield {"error": "Campaign not found"}
            return

        # Yield initial status
        yield {
            "status": campaign.get("status"),
            "message": "Campaign execution started"
        }

        # Monitor task completion
        while True:
            await asyncio.sleep(2)  # Poll every 2 seconds

            campaign = await self.db.campaigns.find_one({"campaign_id": campaign_id})
            current_status = campaign.get("status")

            yield {
                "status": current_status,
                "plan": campaign.get("plan"),
                "results": campaign.get("results", {})
            }

            if current_status in ["completed", "failed"]:
                break
