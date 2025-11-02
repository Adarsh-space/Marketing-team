"""
Approval Workflow System

This module manages approval workflows for critical marketing tasks.
Before executing certain actions (publishing content, sending emails, spending budget),
the system requests user approval.

Features:
- Task approval requests
- Approval status tracking
- Voice agent integration for spoken approvals
- Task management page navigation
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)


class ApprovalStatus(Enum):
    """Status of an approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalType(Enum):
    """Types of actions requiring approval."""
    CONTENT_PUBLISHING = "content_publishing"
    EMAIL_CAMPAIGN = "email_campaign"
    BUDGET_SPEND = "budget_spend"
    CAMPAIGN_EXECUTION = "campaign_execution"
    IMAGE_GENERATION = "image_generation"
    AD_LAUNCH = "ad_launch"


class ApprovalRequest:
    """
    Represents a single approval request.
    """

    def __init__(
        self,
        request_id: str,
        approval_type: ApprovalType,
        task_description: str,
        details: Dict[str, Any],
        requester_agent: str,
        priority: str = "medium"
    ):
        self.request_id = request_id
        self.approval_type = approval_type
        self.task_description = task_description
        self.details = details
        self.requester_agent = requester_agent
        self.priority = priority
        self.status = ApprovalStatus.PENDING
        self.created_at = datetime.now().isoformat()
        self.reviewed_at = None
        self.reviewer_notes = None

    def approve(self, notes: Optional[str] = None):
        """Approve the request."""
        self.status = ApprovalStatus.APPROVED
        self.reviewed_at = datetime.now().isoformat()
        self.reviewer_notes = notes
        logger.info(f"[Approval] Request {self.request_id} approved")

    def reject(self, notes: Optional[str] = None):
        """Reject the request."""
        self.status = ApprovalStatus.REJECTED
        self.reviewed_at = datetime.now().isoformat()
        self.reviewer_notes = notes
        logger.info(f"[Approval] Request {self.request_id} rejected")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "request_id": self.request_id,
            "approval_type": self.approval_type.value,
            "task_description": self.task_description,
            "details": self.details,
            "requester_agent": self.requester_agent,
            "priority": self.priority,
            "status": self.status.value,
            "created_at": self.created_at,
            "reviewed_at": self.reviewed_at,
            "reviewer_notes": self.reviewer_notes
        }


class ApprovalWorkflowManager:
    """
    Manages the approval workflow system.

    This class:
    - Creates approval requests
    - Tracks approval status
    - Notifies users of pending approvals
    - Integrates with voice agent for spoken approvals
    - Manages navigation to task management page
    """

    def __init__(self, db=None):
        """
        Initialize the approval workflow manager.

        Args:
            db: Database connection for persisting approvals
        """
        self.db = db
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        logger.info("ApprovalWorkflowManager initialized")

    async def create_approval_request(
        self,
        approval_type: ApprovalType,
        task_description: str,
        details: Dict[str, Any],
        requester_agent: str,
        priority: str = "medium",
        conversation_id: str = None
    ) -> ApprovalRequest:
        """
        Create a new approval request.

        Args:
            approval_type: Type of approval needed
            task_description: Human-readable task description
            details: Detailed information about the task
            requester_agent: Agent requesting approval
            priority: Priority level (high, medium, low)
            conversation_id: Associated conversation ID

        Returns:
            ApprovalRequest object
        """
        request_id = str(uuid.uuid4())

        request = ApprovalRequest(
            request_id=request_id,
            approval_type=approval_type,
            task_description=task_description,
            details=details,
            requester_agent=requester_agent,
            priority=priority
        )

        # Store in memory
        self.pending_requests[request_id] = request

        # Persist to database if available
        if self.db is not None:
            await self.db.approval_requests.insert_one({
                **request.to_dict(),
                "conversation_id": conversation_id
            })

        logger.info(f"[Approval] Created request {request_id} for {approval_type.value}")

        return request

    async def get_approval_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """
        Get an approval request by ID.

        Args:
            request_id: Request ID

        Returns:
            ApprovalRequest or None if not found
        """
        return self.pending_requests.get(request_id)

    async def approve_request(
        self,
        request_id: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Approve an approval request.

        Args:
            request_id: Request ID to approve
            notes: Optional reviewer notes

        Returns:
            Result dictionary with status and navigation info
        """
        request = await self.get_approval_request(request_id)

        if not request:
            return {
                "status": "error",
                "message": f"Approval request {request_id} not found"
            }

        if request.status != ApprovalStatus.PENDING:
            return {
                "status": "error",
                "message": f"Request already {request.status.value}"
            }

        # Approve the request
        request.approve(notes)

        # Update in database
        if self.db is not None:
            await self.db.approval_requests.update_one(
                {"request_id": request_id},
                {"$set": request.to_dict()}
            )

        # Remove from pending
        if request_id in self.pending_requests:
            del self.pending_requests[request_id]

        logger.info(f"[Approval] Request {request_id} approved successfully")

        return {
            "status": "approved",
            "message": "Request approved successfully. Redirecting to task management page.",
            "request_id": request_id,
            "navigate_to": "/task-management",
            "task_details": request.details
        }

    async def reject_request(
        self,
        request_id: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reject an approval request.

        Args:
            request_id: Request ID to reject
            notes: Optional rejection reason

        Returns:
            Result dictionary
        """
        request = await self.get_approval_request(request_id)

        if not request:
            return {
                "status": "error",
                "message": f"Approval request {request_id} not found"
            }

        if request.status != ApprovalStatus.PENDING:
            return {
                "status": "error",
                "message": f"Request already {request.status.value}"
            }

        # Reject the request
        request.reject(notes)

        # Update in database
        if self.db is not None:
            await self.db.approval_requests.update_one(
                {"request_id": request_id},
                {"$set": request.to_dict()}
            )

        # Remove from pending
        if request_id in self.pending_requests:
            del self.pending_requests[request_id]

        logger.info(f"[Approval] Request {request_id} rejected")

        return {
            "status": "rejected",
            "message": "Request rejected.",
            "request_id": request_id
        }

    async def get_pending_requests(
        self,
        conversation_id: Optional[str] = None,
        approval_type: Optional[ApprovalType] = None
    ) -> List[ApprovalRequest]:
        """
        Get all pending approval requests.

        Args:
            conversation_id: Filter by conversation ID
            approval_type: Filter by approval type

        Returns:
            List of pending ApprovalRequest objects
        """
        pending = [
            req for req in self.pending_requests.values()
            if req.status == ApprovalStatus.PENDING
        ]

        # Apply filters if provided
        if approval_type:
            pending = [req for req in pending if req.approval_type == approval_type]

        # If conversation_id filter is needed, query from database
        if conversation_id and self.db:
            db_requests = await self.db.approval_requests.find({
                "conversation_id": conversation_id,
                "status": ApprovalStatus.PENDING.value
            }).to_list(100)
            # Convert to ApprovalRequest objects
            # (Implementation depends on your needs)

        return pending

    def format_approval_request_for_user(self, request: ApprovalRequest) -> str:
        """
        Format an approval request for user display.

        This creates a clear, plain text message without emojis.

        Args:
            request: ApprovalRequest to format

        Returns:
            Formatted string for display
        """
        message = f"""
APPROVAL REQUIRED

Request ID: {request.request_id}
Type: {request.approval_type.value.replace('_', ' ').title()}
Priority: {request.priority.upper()}
Requested by: {request.requester_agent}

Task Description:
{request.task_description}

Details:
"""
        # Add details in a readable format
        for key, value in request.details.items():
            message += f"  - {key.replace('_', ' ').title()}: {value}\n"

        message += f"""
Created: {request.created_at}

Please review the task details and approve or reject this request.
Once approved, you will be directed to the task management page to monitor execution.
"""

        return message

    async def create_campaign_approval_request(
        self,
        campaign_brief: Dict[str, Any],
        plan: Dict[str, Any],
        conversation_id: str = None
    ) -> ApprovalRequest:
        """
        Create an approval request for campaign execution.

        Args:
            campaign_brief: Campaign brief details
            plan: Execution plan from planning agent
            conversation_id: Associated conversation ID

        Returns:
            ApprovalRequest object
        """
        task_description = f"Execute marketing campaign: {campaign_brief.get('campaign_goal', 'Campaign')}"

        details = {
            "campaign_goal": campaign_brief.get("campaign_goal", "Not specified"),
            "target_audience": campaign_brief.get("target_audience", "Not specified"),
            "budget": campaign_brief.get("budget", "Not specified"),
            "timeline": campaign_brief.get("timeline", "Not specified"),
            "planned_tasks": len(plan.get("tasks", [])),
            "agents_involved": len(set(task.get("agent_assigned") for task in plan.get("tasks", []))),
            "estimated_duration": "Based on task complexity",
            "plan_summary": plan.get("summary", "Campaign execution plan")
        }

        return await self.create_approval_request(
            approval_type=ApprovalType.CAMPAIGN_EXECUTION,
            task_description=task_description,
            details=details,
            requester_agent="PlanningAgent",
            priority="high",
            conversation_id=conversation_id
        )


class VoiceApprovalHandler:
    """
    Handles voice-based approvals through the voice agent.

    When using voice interface:
    - Voice agent asks for approval
    - User responds vocally (yes/no/approve/reject)
    - System processes the approval
    - Navigates to task management page
    """

    def __init__(self, approval_manager: ApprovalWorkflowManager):
        """
        Initialize voice approval handler.

        Args:
            approval_manager: ApprovalWorkflowManager instance
        """
        self.approval_manager = approval_manager
        logger.info("VoiceApprovalHandler initialized")

    async def request_voice_approval(
        self,
        request: ApprovalRequest
    ) -> Dict[str, Any]:
        """
        Request approval through voice interface.

        Args:
            request: ApprovalRequest to present

        Returns:
            Dictionary with voice prompt and expected responses
        """
        # Create a natural spoken prompt
        voice_prompt = f"""
I need your approval to proceed with the following task.

{request.approval_type.value.replace('_', ' ').title()}

{request.task_description}

Here are the details:
"""

        # Add key details in spoken format
        for key, value in list(request.details.items())[:5]:  # Limit to 5 details for voice
            voice_prompt += f"{key.replace('_', ' ').title()}: {value}. "

        voice_prompt += """

Would you like to approve this task?
Please say approve to proceed, or reject to cancel.
"""

        return {
            "voice_prompt": voice_prompt,
            "request_id": request.request_id,
            "expected_responses": ["approve", "yes", "proceed", "reject", "no", "cancel"],
            "next_action": "await_voice_response"
        }

    async def process_voice_response(
        self,
        request_id: str,
        user_response: str
    ) -> Dict[str, Any]:
        """
        Process user's voice response to approval request.

        Args:
            request_id: Request ID being responded to
            user_response: User's spoken response (transcribed)

        Returns:
            Result dictionary with approval status and navigation
        """
        user_response = user_response.lower().strip()

        # Determine if approved or rejected
        approval_words = ["approve", "approved", "yes", "okay", "ok", "proceed", "continue", "go ahead"]
        rejection_words = ["reject", "rejected", "no", "cancel", "stop", "decline"]

        if any(word in user_response for word in approval_words):
            # Approve the request
            result = await self.approval_manager.approve_request(request_id)

            return {
                **result,
                "voice_message": "Request approved. Navigating to task management page where you can monitor the execution.",
                "navigate_to": "/task-management"
            }

        elif any(word in user_response for word in rejection_words):
            # Reject the request
            result = await self.approval_manager.reject_request(request_id)

            return {
                **result,
                "voice_message": "Request rejected. The task will not be executed."
            }

        else:
            # Unclear response
            return {
                "status": "unclear",
                "voice_message": "I did not understand your response. Please say approve to proceed, or reject to cancel."
            }


# Example usage functions

async def example_create_and_approve_workflow():
    """
    Example demonstrating the approval workflow.
    """
    # Initialize manager
    manager = ApprovalWorkflowManager()

    # Create an approval request
    request = await manager.create_approval_request(
        approval_type=ApprovalType.EMAIL_CAMPAIGN,
        task_description="Send welcome email campaign to 1000 new subscribers",
        details={
            "campaign_name": "Welcome Series 2025",
            "recipient_count": 1000,
            "email_count": 3,
            "schedule": "Immediate",
            "content_status": "Ready to send"
        },
        requester_agent="EmailAgent",
        priority="high"
    )

    # Format for user display
    display_message = manager.format_approval_request_for_user(request)
    print(display_message)

    # Simulate user approval
    result = await manager.approve_request(request.request_id, notes="Looks good, proceed")
    print(f"\nApproval result: {result}")

    return result


async def example_voice_approval_workflow():
    """
    Example demonstrating voice approval workflow.
    """
    # Initialize managers
    approval_manager = ApprovalWorkflowManager()
    voice_handler = VoiceApprovalHandler(approval_manager)

    # Create request
    request = await approval_manager.create_approval_request(
        approval_type=ApprovalType.CAMPAIGN_EXECUTION,
        task_description="Launch social media campaign for product launch",
        details={
            "platform": "Instagram, Facebook",
            "budget": "$5000",
            "duration": "2 weeks",
            "content_pieces": 12
        },
        requester_agent="SocialMediaAgent",
        priority="high"
    )

    # Get voice prompt
    voice_prompt = await voice_handler.request_voice_approval(request)
    print("Voice Agent speaks:")
    print(voice_prompt["voice_prompt"])

    # Simulate user response
    user_says = "Yes, I approve"
    result = await voice_handler.process_voice_response(
        request.request_id,
        user_says
    )

    print(f"\nVoice Agent responds: {result.get('voice_message')}")
    print(f"Navigation: {result.get('navigate_to')}")

    return result
