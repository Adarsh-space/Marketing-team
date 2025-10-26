# Quick Setup Instructions

Follow these steps to integrate the new multi-agent system into your application.

## Prerequisites

- Python 3.8 or higher
- MongoDB instance
- OpenAI API key
- Emergent Integrations API key

---

## Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This will install:
- LangChain and LangGraph
- All existing dependencies
- OpenAI Python SDK

---

## Step 2: Configure Environment Variables

Update your `.env` file:

```bash
# Add this new key
OPENAI_API_KEY=sk-your-openai-key-here

# Keep existing keys
EMERGENT_LLM_KEY=your-emergent-key-here
MONGODB_URI=your-mongodb-uri
```

---

## Step 3: Test Installation

```python
# test_setup.py
import os
from dotenv import load_dotenv

load_dotenv()

# Test imports
try:
    from backend.agents.langgraph_supervisor import MultiAgentSupervisor
    from backend.agents.approval_workflow import ApprovalWorkflowManager
    from backend.agents.hd_image_agent import HDImageAgent
    print("✓ All imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    exit(1)

# Test initialization
try:
    supervisor = MultiAgentSupervisor(api_key=os.getenv('OPENAI_API_KEY'))
    print("✓ Supervisor initialized")
except Exception as e:
    print(f"✗ Initialization error: {e}")
    exit(1)

print("\nAll tests passed! System ready.")
```

Run the test:
```bash
python test_setup.py
```

---

## Step 4: Integration Options

### Option A: Simple Integration (Recommended for Testing)

Add to your existing `server.py` or main application file:

```python
from backend.agents.langgraph_supervisor import MultiAgentSupervisor
from backend.agents.approval_workflow import ApprovalWorkflowManager
import os

# Initialize (do this once at startup)
supervisor = MultiAgentSupervisor(api_key=os.getenv('OPENAI_API_KEY'))
approval_manager = ApprovalWorkflowManager()

# Use in your endpoints
@app.post("/api/create-campaign")
async def create_campaign(request):
    user_request = request.user_message

    # Execute with multi-agent system
    result = await supervisor.execute(
        user_request=user_request,
        conversation_id=request.conversation_id
    )

    # Check if approval needed
    if result.get('status') == 'awaiting_approval':
        # Create approval request
        approval_request = await approval_manager.create_approval_request(
            approval_type=ApprovalType.CAMPAIGN_EXECUTION,
            task_description="Execute campaign",
            details=result,
            requester_agent="Supervisor"
        )

        return {
            "type": "approval_required",
            "request_id": approval_request.request_id,
            "message": approval_manager.format_approval_request_for_user(approval_request)
        }

    return result
```

### Option B: Full Integration (Recommended for Production)

Create an enhanced orchestrator:

```python
# backend/agents/enhanced_orchestrator.py
from backend.agents.orchestrator import AgentOrchestrator
from backend.agents.langgraph_supervisor import MultiAgentSupervisor
from backend.agents.approval_workflow import ApprovalWorkflowManager, ApprovalType
import os

class EnhancedOrchestrator(AgentOrchestrator):
    """
    Enhanced orchestrator with multi-agent system and approval workflows.
    """

    def __init__(self, db):
        super().__init__(db)

        # Initialize new components
        self.supervisor = MultiAgentSupervisor(
            api_key=os.getenv('OPENAI_API_KEY')
        )
        self.approval_manager = ApprovalWorkflowManager(db=db)

    async def process_user_message(
        self,
        user_message: str,
        conversation_id: str,
        vector_context: str = None
    ):
        """
        Enhanced message processing with multi-agent coordination.
        """
        # For complex multi-agent tasks, use supervisor
        if self._is_complex_task(user_message):
            return await self._process_with_supervisor(
                user_message,
                conversation_id
            )

        # For simple tasks, use existing system
        return await super().process_user_message(
            user_message,
            conversation_id,
            vector_context
        )

    def _is_complex_task(self, message: str) -> bool:
        """
        Determine if task requires multi-agent coordination.
        """
        complex_keywords = [
            "campaign", "mail campaign", "create content",
            "multiple", "everything", "full strategy"
        ]
        return any(keyword in message.lower() for keyword in complex_keywords)

    async def _process_with_supervisor(
        self,
        user_message: str,
        conversation_id: str
    ):
        """
        Process complex tasks with supervisor.
        """
        result = await self.supervisor.execute(
            user_request=user_message,
            conversation_id=conversation_id
        )

        # Handle approval workflow
        if result.get('status') == 'awaiting_approval':
            request = await self.approval_manager.create_approval_request(
                approval_type=ApprovalType.CAMPAIGN_EXECUTION,
                task_description=f"Execute: {user_message}",
                details=result,
                requester_agent="Supervisor",
                conversation_id=conversation_id
            )

            return {
                "type": "approval_required",
                "approval_request": request.to_dict(),
                "agent_communication": result.get('agent_communication', []),
                "message": "Task analysis complete. Please review and approve."
            }

        return {
            "type": "completed",
            "result": result,
            "agent_communication": result.get('agent_communication', [])
        }
```

Then update `server.py`:

```python
# Replace
orchestrator = AgentOrchestrator(db)

# With
from backend.agents.enhanced_orchestrator import EnhancedOrchestrator
orchestrator = EnhancedOrchestrator(db)
```

---

## Step 5: Add Approval Endpoints

Add these endpoints to handle approvals:

```python
@app.post("/api/approve/{request_id}")
async def approve_request(request_id: str):
    """
    Approve a pending request.
    """
    result = await approval_manager.approve_request(request_id)

    return {
        "status": result["status"],
        "message": result["message"],
        "navigate_to": result.get("navigate_to", "/task-management")
    }

@app.post("/api/reject/{request_id}")
async def reject_request(request_id: str, reason: str = None):
    """
    Reject a pending request.
    """
    result = await approval_manager.reject_request(request_id, notes=reason)

    return {
        "status": result["status"],
        "message": result["message"]
    }

@app.get("/api/pending-approvals")
async def get_pending_approvals():
    """
    Get all pending approval requests.
    """
    requests = await approval_manager.get_pending_requests()

    return {
        "pending": [req.to_dict() for req in requests]
    }
```

---

## Step 6: Update Frontend (Optional)

Add approval UI components:

```javascript
// Example React component
function ApprovalNotification({ approvalRequest }) {
  const handleApprove = async () => {
    const response = await fetch(`/api/approve/${approvalRequest.request_id}`, {
      method: 'POST'
    });

    const result = await response.json();

    if (result.navigate_to) {
      window.location.href = result.navigate_to;
    }
  };

  return (
    <div className="approval-notification">
      <h3>Approval Required</h3>
      <p>{approvalRequest.task_description}</p>

      <div className="details">
        {Object.entries(approvalRequest.details).map(([key, value]) => (
          <div key={key}>
            <strong>{key}:</strong> {value}
          </div>
        ))}
      </div>

      <button onClick={handleApprove}>Approve</button>
      <button onClick={handleReject}>Reject</button>
    </div>
  );
}
```

---

## Step 7: Use HD Image Agent

Replace existing image generation:

```python
# Before
from backend.agents.image_generation_agent import ImageGenerationAgent
image_agent = ImageGenerationAgent()

# After
from backend.agents.hd_image_agent import HDImageAgent
image_agent = HDImageAgent()

# Generate HD image
result = await image_agent.generate_hd_image(
    context={
        "content": post_content,
        "brand_info": brand_info,
        "platform": "Instagram"
    },
    size="1024x1024"  # HD square for social media
)

if result["status"] == "success":
    image_base64 = result["image_base64"]
    resolution = result["technical_specs"]["resolution"]
    print(f"Generated HD image: {resolution}")
```

---

## Step 8: Verify Agent Communication

Test that agent communication is visible and clean (no emojis):

```python
result = await supervisor.execute("Create a mail campaign")

# Print agent communication
print("Agent Communication:")
for comm in result['agent_communication']:
    print(f"[{comm['agent']}]: {comm['message']}")

# Verify no emojis
for comm in result['agent_communication']:
    assert not any(char in comm['message'] for char in ['😊', '🎨', '✨', '👍', '💡'])
    print("✓ No emojis found - Clean communication")
```

---

## Troubleshooting

### Issue: Import Error

```
ImportError: cannot import name 'MultiAgentSupervisor'
```

**Solution**: Ensure you installed dependencies:
```bash
pip install -r backend/requirements.txt
```

### Issue: OpenAI API Key Error

```
Error: OpenAI API key not found
```

**Solution**: Set your API key in `.env`:
```bash
OPENAI_API_KEY=sk-your-key-here
```

### Issue: Images Not HD

```
Warning: Image size seems small for HD quality
```

**Solution**: Use `HDImageAgent` instead of `ImageGenerationAgent`:
```python
from backend.agents.hd_image_agent import HDImageAgent
agent = HDImageAgent()
```

### Issue: Agents Still Using Emojis

**Solution**: Check that you're using the updated agents. The system prompts should include:
```
COMMUNICATION RULES:
- Speak naturally and professionally
- DO NOT use emojis or special symbols
```

---

## Documentation

Full documentation available in:

1. **`MULTI_AGENT_INTEGRATION_GUIDE.md`**
   - Complete integration guide
   - Architecture overview
   - API reference
   - Usage examples

2. **`IMPLEMENTATION_SUMMARY.md`**
   - Summary of changes
   - File structure
   - Benefits and limitations

3. **`CANVA_OAUTH_GUIDE.md`**
   - Canva API integration (previous work)

---

## Example: Complete Workflow

Here's a complete example from request to approval:

```python
# 1. User makes request
user_request = "Create a mail campaign for our new feature"

# 2. Supervisor processes request
result = await supervisor.execute(user_request, conversation_id="user123")

# 3. View agent communication
print("Agent Communication:")
for comm in result['agent_communication']:
    print(f"{comm['agent']}: {comm['message']}")

# Output:
# Supervisor: Analyzing request. Will delegate to Content Agent and Email Agent.
# ContentAgent: Creating email content focusing on feature benefits.
# EmailAgent: Designing campaign structure based on content from Content Agent.
# Supervisor: All tasks completed. Awaiting approval.

# 4. Create approval request
request = await approval_manager.create_approval_request(
    approval_type=ApprovalType.EMAIL_CAMPAIGN,
    task_description="Send email campaign to subscribers",
    details=result['agent_results'],
    requester_agent="Supervisor"
)

# 5. Show to user
print(approval_manager.format_approval_request_for_user(request))

# 6. User approves
approval_result = await approval_manager.approve_request(request.request_id)

# 7. Navigate to task management
print(f"Navigate to: {approval_result['navigate_to']}")
# Navigate to: /task-management

# 8. Execute approved campaign
# (Your execution logic here)
```

---

## Support

For questions or issues:

1. Check documentation in `MULTI_AGENT_INTEGRATION_GUIDE.md`
2. Review examples in `IMPLEMENTATION_SUMMARY.md`
3. Consult troubleshooting section above

---

## Summary

You have successfully:

1. ✓ Installed LangChain/LangGraph dependencies
2. ✓ Configured environment variables
3. ✓ Integrated multi-agent supervisor system
4. ✓ Added approval workflow
5. ✓ Enabled HD image generation
6. ✓ Removed emojis from agent communication
7. ✓ Set up agent-to-agent communication logging

Your system is now ready for enhanced multi-agent marketing automation!

---

**Setup Date**: January 26, 2025
**Version**: 2.0.0
