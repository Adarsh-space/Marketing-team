# Multi-Agent System Integration Guide

Complete guide for the enhanced multi-agent marketing automation system with LangChain/LangGraph integration.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Key Features](#key-features)
4. [Installation](#installation)
5. [Multi-Agent Supervisor System](#multi-agent-supervisor-system)
6. [Approval Workflow](#approval-workflow)
7. [Agent Communication](#agent-communication)
8. [HD Image Generation](#hd-image-generation)
9. [Usage Examples](#usage-examples)
10. [Best Practices](#best-practices)

---

## Overview

The marketing automation platform has been enhanced with a sophisticated multi-agent system using LangChain and LangGraph. This system provides:

- **Hierarchical Agent Orchestration**: Supervisor pattern for coordinating specialized agents
- **Agent-to-Agent Communication**: Visible, structured communication between agents
- **Approval Workflows**: User approval required before critical actions
- **HD Image Generation**: Guaranteed high-definition image quality
- **Clean Communication**: Professional agent responses without emojis or symbols

---

## Architecture

### System Components

```
User Request
     |
     v
[Supervisor Agent]
     |
     |-----> [Content Agent]
     |-----> [Email Agent]
     |-----> [Image Agent (HD)]
     |-----> [Research Agent]
     |
     v
[Approval Workflow]
     |
     v
[Task Execution]
     |
     v
[Result Aggregation]
```

### Agent Hierarchy

1. **Supervisor Agent**
   - Analyzes user requests
   - Delegates tasks to specialized agents
   - Coordinates agent collaboration
   - Aggregates results

2. **Specialized Agents**
   - **Content Agent**: Creates marketing content, social posts, ad copy
   - **Email Agent**: Designs email campaigns and sequences
   - **Image Agent**: Generates HD marketing images
   - **Research Agent**: Conducts market research and analysis

3. **Support Systems**
   - **Approval Workflow Manager**: Handles approval requests
   - **Voice Approval Handler**: Processes voice-based approvals
   - **Communication Logger**: Tracks agent interactions

---

## Key Features

### 1. LangGraph Multi-Agent Orchestration

Using LangGraph's state graph system for:
- Sequential and parallel task execution
- State management across agents
- Conditional routing based on task requirements
- Memory and context persistence

### 2. Agent-to-Agent Communication

All agent communications are:
- Logged and visible to users
- Structured with clear sender/receiver
- Tracked with timestamps
- Available for audit and review

### 3. Approval Workflows

Critical actions require approval:
- Campaign execution
- Email sends
- Budget spending
- Content publishing
- Ad launches

### 4. HD Image Quality

All images are guaranteed HD:
- Minimum 1024x1024 resolution
- Quality validation
- Professional marketing standards
- Print-ready when needed

### 5. Clean Communication

Agents communicate professionally:
- No emojis in agent responses
- No symbols or formatting
- Clear, concise language
- Professional tone

Note: Marketing content created by agents (social posts, emails) can still include emojis and formatting as appropriate for the platform.

---

## Installation

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Key new dependencies:
```
langchain==0.3.20
langchain-core==0.3.39
langchain-openai==0.3.5
langgraph==0.3.6
```

### 2. Environment Variables

Add to your `.env` file:

```bash
# OpenAI API Key (for LangChain)
OPENAI_API_KEY=your_openai_key_here

# Emergent Integrations Key (existing)
EMERGENT_LLM_KEY=your_emergent_key_here

# MongoDB (existing)
MONGODB_URI=your_mongodb_uri
```

### 3. Import New Modules

```python
from backend.agents.langgraph_supervisor import MultiAgentSupervisor
from backend.agents.approval_workflow import ApprovalWorkflowManager, VoiceApprovalHandler
from backend.agents.hd_image_agent import HDImageAgent
```

---

## Multi-Agent Supervisor System

### Basic Usage

```python
from backend.agents.langgraph_supervisor import MultiAgentSupervisor

# Initialize supervisor
supervisor = MultiAgentSupervisor(
    api_key=os.getenv('OPENAI_API_KEY'),
    model="gpt-4o"
)

# Execute a request
result = await supervisor.execute(
    user_request="Create a social media campaign for our new product launch",
    conversation_id="user123_session1"
)

# Access results
print(result['agent_results'])
print(result['agent_communication'])
```

### Agent State Management

The system maintains state across all agents:

```python
class AgentState(TypedDict):
    task: str  # Current task
    user_request: str  # Original user request
    agent_messages: List[BaseMessage]  # Communication history
    agent_results: Dict[str, Any]  # Results from each agent
    pending_approval: bool  # Approval status
    final_output: Dict[str, Any]  # Aggregated results
```

### Supervisor Decision Making

The supervisor analyzes requests and delegates:

```json
{
  "analysis": "User wants to create a mail campaign. This requires content creation and email setup.",
  "subtasks": [
    {
      "task": "Create email content with compelling subject lines and body copy",
      "assigned_agent": "content_agent",
      "priority": "high"
    },
    {
      "task": "Design email campaign structure with sequences and segmentation",
      "assigned_agent": "email_agent",
      "priority": "high",
      "dependencies": ["content_creation"]
    }
  ],
  "requires_approval": true,
  "coordination_notes": "Content agent creates copy first, then email agent structures the campaign"
}
```

---

## Approval Workflow

### Creating Approval Requests

```python
from backend.agents.approval_workflow import (
    ApprovalWorkflowManager,
    ApprovalType
)

# Initialize manager
approval_manager = ApprovalWorkflowManager(db=mongodb_client)

# Create approval request
request = await approval_manager.create_approval_request(
    approval_type=ApprovalType.EMAIL_CAMPAIGN,
    task_description="Send welcome email to 1000 subscribers",
    details={
        "campaign_name": "Welcome Series 2025",
        "recipient_count": 1000,
        "email_count": 3,
        "schedule": "Immediate"
    },
    requester_agent="EmailAgent",
    priority="high"
)

# Display to user
message = approval_manager.format_approval_request_for_user(request)
print(message)
```

### Approval Output Format

```
APPROVAL REQUIRED

Request ID: abc123-def456
Type: Email Campaign
Priority: HIGH
Requested by: EmailAgent

Task Description:
Send welcome email campaign to 1000 new subscribers

Details:
  - Campaign Name: Welcome Series 2025
  - Recipient Count: 1000
  - Email Count: 3
  - Schedule: Immediate

Created: 2025-01-26T10:30:00Z

Please review the task details and approve or reject this request.
Once approved, you will be directed to the task management page to monitor execution.
```

### Processing Approval

```python
# User approves
result = await approval_manager.approve_request(
    request_id="abc123-def456",
    notes="Approved, content looks good"
)

# Result includes navigation
print(result)
# {
#     "status": "approved",
#     "message": "Request approved successfully. Redirecting to task management page.",
#     "navigate_to": "/task-management",
#     "task_details": {...}
# }
```

### Voice Approval Integration

```python
from backend.agents.approval_workflow import VoiceApprovalHandler

# Initialize voice handler
voice_handler = VoiceApprovalHandler(approval_manager)

# Get voice prompt
voice_prompt = await voice_handler.request_voice_approval(request)

# Voice agent speaks:
print(voice_prompt["voice_prompt"])
# "I need your approval to proceed with the following task.
#  Email Campaign
#  Send welcome email campaign to 1000 new subscribers
#  ...
#  Would you like to approve this task?
#  Please say approve to proceed, or reject to cancel."

# User responds via voice
user_says = "Yes, I approve"

# Process response
result = await voice_handler.process_voice_response(
    request_id=request.request_id,
    user_response=user_says
)

print(result["voice_message"])
# "Request approved. Navigating to task management page
#  where you can monitor the execution."
```

---

## Agent Communication

### Communication Logger

```python
from backend.agents.langgraph_supervisor import AgentCommunicationLogger

# Initialize logger
comm_logger = AgentCommunicationLogger()

# Log communication
comm_logger.log_communication(
    from_agent="Supervisor",
    to_agent="ContentAgent",
    message="Create social media content for product launch with focus on benefits",
    message_type="task_delegation"
)

comm_logger.log_communication(
    from_agent="ContentAgent",
    to_agent="EmailAgent",
    message="Social media content completed. Key message focuses on time-saving benefits. Use similar messaging for email campaign.",
    message_type="result_sharing"
)

# Get communication history
history = comm_logger.get_communication_history()

# Display formatted
print(comm_logger.format_for_display())
```

### Communication Output

```
Agent Communication Log:
==================================================

[2025-01-26T10:30:15Z]
Supervisor -> ContentAgent
Type: task_delegation
Message: Create social media content for product launch with focus on benefits
--------------------------------------------------

[2025-01-26T10:31:42Z]
ContentAgent -> EmailAgent
Type: result_sharing
Message: Social media content completed. Key message focuses on time-saving benefits. Use similar messaging for email campaign.
--------------------------------------------------
```

### Communication Types

- `task_delegation`: Supervisor assigning tasks
- `result_sharing`: Agent sharing outputs with other agents
- `question`: Agent requesting clarification
- `coordination`: Agents coordinating dependencies
- `status_update`: Progress updates

---

## HD Image Generation

### Using HD Image Agent

```python
from backend.agents.hd_image_agent import (
    HDImageAgent,
    ImageModel,
    ImageQuality
)

# Initialize HD agent
hd_image_agent = HDImageAgent()

# Generate HD image
result = await hd_image_agent.generate_hd_image(
    context={
        "content": "Launch of our new productivity app",
        "brand_info": "Modern tech company, blue and white colors, professional",
        "platform": "Instagram",
        "style_preferences": "Clean, modern, professional"
    },
    model=ImageModel.DALLE_3_HD,
    quality=ImageQuality.HD,
    size="1024x1024"
)

# Check result
if result["status"] == "success":
    image_data = result["image_base64"]
    resolution = result["technical_specs"]["resolution"]
    file_size = result["technical_specs"]["file_size_kb"]

    print(f"HD image generated: {resolution}, {file_size} KB")
    # HD image generated: 1024x1024, 245.67 KB
```

### Image Sizes

All sizes are HD:

```python
# Square (social feed)
size = "1024x1024"

# Wide (banners, LinkedIn)
size = "1792x1024"

# Vertical (stories, Pinterest)
size = "1024x1792"
```

### Quality Validation

The agent validates HD quality:

```python
{
    "quality_validated": True,  # File size check
    "file_size_kb": 245.67,     # HD images typically > 100 KB
    "resolution": "1024x1024",
    "suitable_for": ["digital", "print"]
}
```

---

## Usage Examples

### Example 1: Create Mail Campaign with Agent Collaboration

```python
async def create_mail_campaign_example():
    """
    User requests: "Create a mail campaign for our new feature"

    This demonstrates:
    - Multi-agent collaboration
    - Agent-to-agent communication
    - Approval workflow
    """

    # Initialize systems
    supervisor = MultiAgentSupervisor(api_key=os.getenv('OPENAI_API_KEY'))
    approval_manager = ApprovalWorkflowManager(db=mongodb_client)

    # User request
    user_request = "Create a mail campaign for our new feature"

    # Execute through supervisor
    result = await supervisor.execute(
        user_request=user_request,
        conversation_id="user123"
    )

    # Supervisor delegates to Content Agent and Email Agent
    # They communicate with each other

    # View agent communication
    for comm in result['agent_communication']:
        print(f"[{comm['agent']}]: {comm['message']}")

    # Output:
    # [Supervisor]: Analyzing request. Will delegate to Content Agent for email copy and Email Agent for campaign structure.
    # [ContentAgent]: Creating email content focusing on feature benefits and value proposition.
    # [ContentAgent]: Content complete. Subject line: "Introducing Our Game-Changing New Feature". Three email variants created.
    # [EmailAgent]: Received content from Content Agent. Designing 3-email welcome sequence with segmentation.
    # [EmailAgent]: Campaign structure complete. Segmented by user role with personalized messaging.
    # [Supervisor]: All agents completed. Campaign ready for approval.

    # Check if approval needed
    if result['status'] == 'awaiting_approval':
        # Create approval request
        request = await approval_manager.create_campaign_approval_request(
            campaign_brief={'goal': 'Feature announcement'},
            plan=result['plan']
        )

        # Show to user
        print(approval_manager.format_approval_request_for_user(request))

        # User approves
        approval_result = await approval_manager.approve_request(request.request_id)

        # Navigate to task management
        print(f"Navigate to: {approval_result['navigate_to']}")
        # Navigate to: /task-management

    return result
```

### Example 2: Voice-Activated Campaign with HD Images

```python
async def voice_campaign_with_images_example():
    """
    User speaks: "Create social media posts with images for our sale"

    This demonstrates:
    - Voice approval
    - HD image generation
    - Multi-agent coordination
    """

    # Initialize
    supervisor = MultiAgentSupervisor(api_key=os.getenv('OPENAI_API_KEY'))
    approval_manager = ApprovalWorkflowManager(db=mongodb_client)
    voice_handler = VoiceApprovalHandler(approval_manager)

    # Voice input (transcribed)
    user_request = "Create social media posts with images for our sale"

    # Execute
    result = await supervisor.execute(user_request)

    # Agent communication visible:
    # Supervisor -> ContentAgent: Create social media content for sale
    # ContentAgent: Creating engaging sale posts...
    # ContentAgent -> ImageAgent: Need HD images for social posts
    # ImageAgent: Generating HD 1024x1024 images optimized for Instagram...
    # ImageAgent: HD images complete, 1024x1024 resolution validated

    # Approval needed for publishing
    request = await approval_manager.create_approval_request(
        approval_type=ApprovalType.CONTENT_PUBLISHING,
        task_description="Publish 5 social media posts with images",
        details=result['agent_results'],
        requester_agent="SocialMediaAgent"
    )

    # Voice approval
    voice_prompt = await voice_handler.request_voice_approval(request)

    # Voice agent asks user
    # (User interface plays audio)

    # User responds
    user_says = "Yes, approve it"

    # Process
    approval_result = await voice_handler.process_voice_response(
        request.request_id,
        user_says
    )

    # Voice agent responds
    print(approval_result['voice_message'])
    # "Request approved. Navigating to task management page where you can monitor the execution."

    return approval_result
```

### Example 3: Integration with Existing Orchestrator

```python
from backend.agents.orchestrator import AgentOrchestrator
from backend.agents.langgraph_supervisor import MultiAgentSupervisor
from backend.agents.approval_workflow import ApprovalWorkflowManager

class EnhancedOrchestrator(AgentOrchestrator):
    """
    Enhanced orchestrator with LangGraph supervisor and approval workflows.
    """

    def __init__(self, db):
        super().__init__(db)

        # Add new components
        self.supervisor = MultiAgentSupervisor(
            api_key=os.getenv('OPENAI_API_KEY')
        )
        self.approval_manager = ApprovalWorkflowManager(db=db)

    async def process_user_message_with_approval(
        self,
        user_message: str,
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Process message with approval workflow integration.
        """
        # Use supervisor for complex multi-agent tasks
        result = await self.supervisor.execute(
            user_request=user_message,
            conversation_id=conversation_id
        )

        # Check if approval needed
        if result.get('status') == 'awaiting_approval':
            # Create approval request
            request = await self.approval_manager.create_approval_request(
                approval_type=ApprovalType.CAMPAIGN_EXECUTION,
                task_description="Execute campaign based on conversation",
                details=result,
                requester_agent="Supervisor"
            )

            return {
                "type": "approval_required",
                "approval_request": request.to_dict(),
                "display_message": self.approval_manager.format_approval_request_for_user(request)
            }

        return result
```

---

## Best Practices

### 1. Agent Communication

**DO:**
- Keep agent communication clear and professional
- Log all inter-agent communications
- Show communication flow to users
- Use structured message types

**DON'T:**
- Use emojis in agent-to-agent communication
- Hide agent interactions from users
- Skip logging for debugging purposes

### 2. Approval Workflows

**DO:**
- Require approval for critical actions
- Provide clear task descriptions
- Show all details to users
- Navigate to task management after approval
- Support both UI and voice approvals

**DON'T:**
- Execute critical actions without approval
- Hide task details
- Skip approval for budget/publishing actions

### 3. HD Image Generation

**DO:**
- Always use HD sizes (1024x1024 minimum)
- Include quality markers in prompts
- Validate image file sizes
- Provide technical specifications
- Optimize for target platform

**DON'T:**
- Generate low-resolution images
- Skip quality validation
- Use generic prompts
- Ignore platform requirements

### 4. Multi-Agent Coordination

**DO:**
- Let supervisor handle task delegation
- Share context between agents
- Respect task dependencies
- Aggregate results clearly
- Track execution progress

**DON'T:**
- Have agents work in isolation
- Ignore dependencies
- Skip result aggregation
- Lose context between tasks

---

## API Reference

### MultiAgentSupervisor

```python
supervisor = MultiAgentSupervisor(api_key: str, model: str = "gpt-4o")

# Execute request
result = await supervisor.execute(
    user_request: str,
    conversation_id: str = None
) -> Dict[str, Any]

# Resume after approval
continued = await supervisor.approve_and_continue(
    conversation_id: str
) -> Dict[str, Any]
```

### ApprovalWorkflowManager

```python
manager = ApprovalWorkflowManager(db=None)

# Create request
request = await manager.create_approval_request(
    approval_type: ApprovalType,
    task_description: str,
    details: Dict[str, Any],
    requester_agent: str,
    priority: str = "medium"
) -> ApprovalRequest

# Approve
result = await manager.approve_request(
    request_id: str,
    notes: Optional[str] = None
) -> Dict[str, Any]

# Reject
result = await manager.reject_request(
    request_id: str,
    notes: Optional[str] = None
) -> Dict[str, Any]
```

### HDImageAgent

```python
agent = HDImageAgent()

# Generate HD image
result = await agent.generate_hd_image(
    context: Dict[str, Any],
    model: ImageModel = ImageModel.DALLE_3_HD,
    quality: ImageQuality = ImageQuality.HD,
    size: str = "1024x1024"
) -> Dict[str, Any]
```

---

## Troubleshooting

### Issue: Agents using emojis in communication

**Solution:** Check agent system prompts. They should include:
```
COMMUNICATION RULES:
- Speak naturally and professionally
- DO NOT use emojis or special symbols
- Write in clear, plain English
```

### Issue: Images not HD quality

**Solution:** Use `HDImageAgent` instead of `ImageGenerationAgent`, or ensure size is HD:
```python
valid_sizes = ["1024x1024", "1792x1024", "1024x1792"]
```

### Issue: Approval workflow not triggering

**Solution:** Check supervisor decision includes:
```json
{
  "requires_approval": true
}
```

### Issue: Agent communication not visible

**Solution:** Use `AgentCommunicationLogger` and check `agent_messages` in state:
```python
for msg in result['agent_communication']:
    print(msg)
```

---

## Additional Resources

- **LangChain Documentation**: https://python.langchain.com/docs/
- **LangGraph Documentation**: https://langchain-ai.github.io/langgraph/
- **Multi-Agent Patterns**: https://blog.langchain.com/langgraph-multi-agent-workflows/
- **Deep Agents**: https://blog.langchain.com/deep-agents/

---

## Support

For issues or questions:
1. Check troubleshooting section
2. Review code examples
3. Consult LangChain documentation
4. Open GitHub issue

---

## License

MIT License - See LICENSE file for details

---

**Last Updated**: January 26, 2025
**Version**: 2.0.0
