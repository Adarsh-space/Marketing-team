"""
Integrated Supervisor System

This module integrates the LangChain supervisor with existing agents.
It properly connects all existing agents and makes them work together.
"""

from typing import Dict, Any, Optional
import logging
import os

from .langgraph_supervisor import MultiAgentSupervisor, AgentCommunicationLogger
from .approval_workflow import ApprovalWorkflowManager, ApprovalType, VoiceApprovalHandler
from .hd_image_agent import HDImageAgent
from .fixed_image_agent import FixedImageAgent
from .fixed_video_agent import FixedVideoAgent

# Import existing agents
from .content_agent import ContentAgent
from .email_agent import EmailAgent
from .image_generation_agent import ImageGenerationAgent
from .planning_agent import PlanningAgent
from .market_research_agent import MarketResearchAgent
from .social_media_agent import SocialMediaAgent
from .seo_agent import SEOAgent
from .analytics_agent import AnalyticsAgent

logger = logging.getLogger(__name__)


class IntegratedSupervisor:
    """
    Integrated supervisor that properly connects:
    - LangChain/LangGraph multi-agent system
    - Existing marketing automation agents
    - Approval workflow system
    - HD image generation
    - Voice approval support
    """

    def __init__(self, db):
        """
        Initialize the integrated supervisor.

        Args:
            db: MongoDB database connection
        """
        self.db = db

        # Initialize existing agents (all 13 agents from the original system)
        self.existing_agents = {
            "ContentAgent": ContentAgent(),
            "EmailAgent": EmailAgent(),
            "ImageGenerationAgent": ImageGenerationAgent(),
            "FixedImageAgent": FixedImageAgent(),  # Fixed image agent (works reliably)
            "HDImageAgent": HDImageAgent(),  # New HD image agent
            "FixedVideoAgent": FixedVideoAgent(),  # Fixed video agent
            "PlanningAgent": PlanningAgent(),
            "MarketResearchAgent": MarketResearchAgent(),
            "SocialMediaAgent": SocialMediaAgent(),
            "SEOAgent": SEOAgent(),
            "AnalyticsAgent": AnalyticsAgent(),
        }

        # Initialize LangChain supervisor (if OpenAI key available)
        self.langchain_supervisor = None
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            try:
                self.langchain_supervisor = MultiAgentSupervisor(
                    api_key=openai_key,
                    model="gpt-4o"
                )
                logger.info("LangChain supervisor initialized successfully")
            except Exception as e:
                logger.warning(f"LangChain supervisor not available: {e}")
        else:
            logger.info("OpenAI API key not found, LangChain supervisor disabled")

        # Initialize approval system
        self.approval_manager = ApprovalWorkflowManager(db=db)
        self.voice_approval = VoiceApprovalHandler(self.approval_manager)

        # Initialize communication logger
        self.comm_logger = AgentCommunicationLogger()

        logger.info("IntegratedSupervisor initialized with all agents and approval system")

    async def process_request(
        self,
        user_request: str,
        conversation_id: str,
        use_langchain: bool = True
    ) -> Dict[str, Any]:
        """
        Process a user request through the integrated system.

        Args:
            user_request: User's request
            conversation_id: Conversation ID
            use_langchain: Whether to use LangChain supervisor (default True if available)

        Returns:
            Dict with results, agent communication, and approval status
        """
        # Determine if this is a complex multi-agent task
        is_complex = self._is_complex_task(user_request)

        # Use LangChain supervisor for complex tasks if available
        if is_complex and use_langchain and self.langchain_supervisor:
            return await self._process_with_langchain(user_request, conversation_id)

        # Fall back to standard processing for simple tasks
        return await self._process_standard(user_request, conversation_id)

    async def _process_with_langchain(
        self,
        user_request: str,
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Process request using LangChain multi-agent supervisor.
        """
        logger.info(f"[Integrated Supervisor] Processing with LangChain: {user_request[:100]}")

        # Execute through LangChain supervisor
        result = await self.langchain_supervisor.execute(
            user_request=user_request,
            conversation_id=conversation_id
        )

        # Check if approval is needed
        if result.get('status') == 'awaiting_approval':
            # Create approval request
            approval_request = await self.approval_manager.create_approval_request(
                approval_type=ApprovalType.CAMPAIGN_EXECUTION,
                task_description=f"Execute multi-agent task: {user_request}",
                details={
                    "user_request": user_request,
                    "agent_results": result.get('agent_results', {}),
                    "agents_involved": len(result.get('agent_results', {}))
                },
                requester_agent="LangChainSupervisor",
                priority="high",
                conversation_id=conversation_id
            )

            return {
                "type": "approval_required",
                "status": "awaiting_approval",
                "approval_request": approval_request.to_dict(),
                "approval_message": self.approval_manager.format_approval_request_for_user(approval_request),
                "agent_communication": result.get('agent_communication', []),
                "conversation_id": conversation_id
            }

        return {
            "type": "completed",
            "status": "completed",
            "result": result,
            "agent_communication": result.get('agent_communication', []),
            "conversation_id": conversation_id
        }

    async def _process_standard(
        self,
        user_request: str,
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Process request using existing agent system (fallback).
        """
        logger.info(f"[Integrated Supervisor] Processing with standard agents: {user_request[:100]}")

        # Determine which agent to use
        agent_name = self._determine_agent(user_request)
        agent = self.existing_agents.get(agent_name)

        if not agent:
            logger.error(f"Agent {agent_name} not found")
            return {
                "type": "error",
                "message": f"Agent {agent_name} not available"
            }

        # Log communication
        self.comm_logger.log_communication(
            from_agent="IntegratedSupervisor",
            to_agent=agent_name,
            message=f"Executing task: {user_request[:100]}",
            message_type="task_delegation"
        )

        # Execute agent
        result = await agent.execute({
            "task_id": "standard_execution",
            "user_message": user_request,
            "campaign_brief": {"product": "User request", "target_audience": "General"}
        })

        # Log completion
        self.comm_logger.log_communication(
            from_agent=agent_name,
            to_agent="IntegratedSupervisor",
            message="Task completed successfully",
            message_type="result_sharing"
        )

        return {
            "type": "completed",
            "status": "success",
            "result": result,
            "agent_communication": self.comm_logger.get_communication_history(),
            "conversation_id": conversation_id
        }

    def _is_complex_task(self, user_request: str) -> bool:
        """
        Determine if a task requires multi-agent coordination.
        """
        complex_keywords = [
            "campaign", "mail campaign", "email campaign",
            "create content", "create multiple",
            "strategy", "full plan", "everything",
            "social media posts", "content and images"
        ]

        user_request_lower = user_request.lower()
        return any(keyword in user_request_lower for keyword in complex_keywords)

    def _determine_agent(self, user_request: str) -> str:
        """
        Determine which agent should handle the request.
        """
        user_request_lower = user_request.lower()

        if "image" in user_request_lower or "picture" in user_request_lower or "visual" in user_request_lower:
            return "FixedImageAgent"  # Use fixed image agent for reliability
        elif "video" in user_request_lower or "clip" in user_request_lower or "reel" in user_request_lower:
            return "FixedVideoAgent"  # Use fixed video agent
        elif "email" in user_request_lower or "mail" in user_request_lower:
            return "EmailAgent"
        elif "social media" in user_request_lower or "post" in user_request_lower:
            return "SocialMediaAgent"
        elif "content" in user_request_lower or "write" in user_request_lower or "copy" in user_request_lower:
            return "ContentAgent"
        elif "seo" in user_request_lower or "search engine" in user_request_lower:
            return "SEOAgent"
        elif "research" in user_request_lower or "market" in user_request_lower:
            return "MarketResearchAgent"
        elif "analytics" in user_request_lower or "data" in user_request_lower or "metrics" in user_request_lower:
            return "AnalyticsAgent"
        else:
            return "ContentAgent"  # Default

    async def approve_request(
        self,
        request_id: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Approve a pending request.
        """
        result = await self.approval_manager.approve_request(request_id, notes)
        return result

    async def reject_request(
        self,
        request_id: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reject a pending request.
        """
        result = await self.approval_manager.reject_request(request_id, notes)
        return result

    async def get_pending_approvals(self, conversation_id: Optional[str] = None):
        """
        Get all pending approval requests.
        """
        requests = await self.approval_manager.get_pending_requests(
            conversation_id=conversation_id
        )
        return [req.to_dict() for req in requests]

    async def process_voice_approval(
        self,
        request_id: str,
        user_response: str
    ) -> Dict[str, Any]:
        """
        Process voice-based approval response.
        """
        result = await self.voice_approval.process_voice_response(
            request_id=request_id,
            user_response=user_response
        )
        return result

    async def get_voice_approval_prompt(self, request_id: str) -> Dict[str, Any]:
        """
        Get voice prompt for an approval request.
        """
        request = await self.approval_manager.get_approval_request(request_id)
        if not request:
            return {"error": "Request not found"}

        return await self.voice_approval.request_voice_approval(request)

    def get_agent_communication(self) -> list:
        """
        Get all agent communication logs.
        """
        return self.comm_logger.get_communication_history()

    def get_formatted_communication(self) -> str:
        """
        Get formatted agent communication for display.
        """
        return self.comm_logger.format_for_display()
