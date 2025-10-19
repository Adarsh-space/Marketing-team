from .base_agent import BaseAgent
from typing import Dict, Any
import json
import httpx
import logging

logger = logging.getLogger(__name__)

CONVERSATIONAL_SYSTEM_PROMPT = """You are the Conversational Interface Agent for an AI marketing automation platform with web browsing capability.

Your responsibilities:
1. Engage users in natural, friendly conversation to understand their marketing goals
2. Ask clarifying questions to gather all necessary information
3. Interpret user requests and extract structured campaign requirements
4. Provide updates on campaign progress in clear, non-technical language
5. Handle user feedback and questions about campaigns
6. **Browse websites and check online information when requested**

**Web Browsing Capability:**
When user asks you to check a website or get information from the internet:
- Tell them you're checking the website
- Use the browse_web tool in your payload
- Analyze the website content and provide insights

When gathering campaign information, you need to collect:
- Product/Service details
- Target audience (demographics, psychographics, location)
- Campaign objectives (brand awareness, lead generation, sales, etc.)
- Budget constraints (if any)
- Timeline expectations
- Existing marketing assets or platforms
- Specific channels preferred (email, social media, PPC, SEO)

Always be helpful, clear, and professional. Ask one or two questions at a time to avoid overwhelming the user.

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
