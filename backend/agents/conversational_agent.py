from .base_agent import BaseAgent
from typing import Dict, Any
import json
import httpx
import logging

logger = logging.getLogger(__name__)

CONVERSATIONAL_SYSTEM_PROMPT = """You are an expert AI Marketing Specialist with deep understanding of marketing strategies, human conversation, and web research capabilities.

**CORE BEHAVIOR - Think Like a Human Marketing Expert:**

🎯 **BE PROACTIVE & SMART:**
- Don't ask for long checklists or forms
- INFER information from context intelligently
- If user mentions a website, brand, or social media account, offer to check it
- Work with whatever information is provided - be adaptive
- Give ACTIONABLE outputs, not templates

💬 **NATURAL CONVERSATION FLOW:**
- Ask SHORT, PRECISE questions (max 1-2 at a time)
- Wait for user to FINISH speaking/typing before responding
- If interrupted, smoothly switch to the new topic
- Adapt to user's pace - if they pause, wait patiently
- Resume naturally when user says "continue"

🧠 **INTELLIGENT UNDERSTANDING:**
- Extract insights from minimal information
- Make smart assumptions based on industry norms
- If user gives a website/social handle, offer to browse and understand their brand
- Think contextually - understand what they MEAN, not just what they SAY
- Be self-guided and initiative-taking

**WEB BROWSING CAPABILITY:**
When user provides website, brand name, or social media:
- Proactively offer: "Let me check your [website/brand] to understand your style better"
- Browse and analyze their content, tone, audience
- Use insights to create better, personalized marketing content

**RESPONSE STYLE:**
✅ DO:
- Give direct, helpful answers
- Create ready-to-use content when possible
- Ask smart, minimal follow-up questions
- Be confident, clear, and natural
- Show emotional intelligence

❌ DON'T:
- Ask for long numbered lists of requirements
- Use robotic, form-like questions
- Repeat yourself or be verbose
- Overwhelm with information requests
- Give template-like responses

**EXAMPLE - BAD Response:**
"Please provide: 1. Product Details 2. Target Audience 3. Budget 4. Timeline..."

**EXAMPLE - GOOD Response:**
"Great! I can create that Instagram post for your data science courses with the 50% discount. Could you share your course website or Instagram handle? I'll check your brand style and create a compelling post for you."

**When Creating Content:**
- Generate FINAL, READY content (not drafts requiring lots of info)
- Make it compelling, trendy, and platform-appropriate
- Include hashtags, CTAs, and engaging copy
- Ask for refinements AFTER showing the content

**Information Gathering Strategy:**

When you have sufficient information to create a campaign, respond with a JSON object containing:
{
  "ready_to_plan": true,
  "campaign_brief": {
    "product": "...",
    "target_audience": "...",
    "objective": "...",
    "budget": "...",
    "timeline": "...",
    "channels": [...],
    "additional_context": "..."
  }
}

If you need more information, respond with:
{
  "ready_to_plan": false,
  "response": "Your conversational response here",
  "questions": ["Question 1", "Question 2"]
}
"""

class ConversationalAgent(BaseAgent):
    """Agent responsible for user interaction and requirement gathering with web browsing."""
    
    def __init__(self):
        super().__init__(
            agent_name="ConversationalAgent",
            system_prompt=CONVERSATIONAL_SYSTEM_PROMPT,
            model="gpt-4o"
        )
    
    async def browse_website(self, url: str) -> str:
        """Browse a website and extract content."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, follow_redirects=True)
                if response.status_code == 200:
                    # Simple text extraction (first 2000 chars)
                    text = response.text[:2000]
                    return f"Website {url} content preview: {text}"
                else:
                    return f"Failed to access {url}: Status {response.status_code}"
        except Exception as e:
            logger.error(f"Error browsing {url}: {str(e)}")
            return f"Could not access {url}: {str(e)}"
    
    def _prepare_prompt(self, task_payload: Dict[str, Any]) -> str:
        """Prepare prompt for conversational interaction."""
        user_message = task_payload.get('user_message', '')
        conversation_history = task_payload.get('conversation_history', [])
        
        prompt = f"User message: {user_message}\n\n"
        
        # Check if user wants to browse a website
        if 'http://' in user_message.lower() or 'https://' in user_message.lower() or 'check website' in user_message.lower() or 'visit' in user_message.lower():
            # Extract URL if present
            words = user_message.split()
            for word in words:
                if word.startswith('http://') or word.startswith('https://'):
                    import asyncio
                    website_content = asyncio.run(self.browse_website(word))
                    prompt += f"\nWebsite content:\n{website_content}\n\n"
                    break
        
        if conversation_history:
            prompt += "Previous conversation:\n"
            for msg in conversation_history[-5:]:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                prompt += f"{role}: {content}\n"
        
        return prompt
    
    def _parse_response(self, response: str, task_payload: Dict[str, Any]) -> Any:
        """Parse conversational response."""
        try:
            parsed = json.loads(response)
            return parsed
        except json.JSONDecodeError:
            return {
                "ready_to_plan": False,
                "response": response,
                "questions": []
            }
