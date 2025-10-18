from .base_agent import BaseAgent
from typing import Dict, Any
import json

CONVERSATIONAL_SYSTEM_PROMPT = """You are the Conversational Interface Agent for an AI marketing automation platform.

Your responsibilities:
1. Engage users in natural, friendly conversation to understand their marketing goals
2. Ask clarifying questions to gather all necessary information
3. Interpret user requests and extract structured campaign requirements
4. Provide updates on campaign progress in clear, non-technical language
5. Handle user feedback and questions about campaigns

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
    """Agent responsible for user interaction and requirement gathering."""
    
    def __init__(self):
        super().__init__(
            agent_name="ConversationalAgent",
            system_prompt=CONVERSATIONAL_SYSTEM_PROMPT,
            model="gpt-4o"
        )
    
    def _prepare_prompt(self, task_payload: Dict[str, Any]) -> str:
        """Prepare prompt for conversational interaction."""
        user_message = task_payload.get('user_message', '')
        conversation_history = task_payload.get('conversation_history', [])
        
        prompt = f"User message: {user_message}\n\n"
        
        if conversation_history:
            prompt += "Previous conversation:\n"
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                prompt += f"{role}: {content}\n"
        
        return prompt
    
    def _parse_response(self, response: str, task_payload: Dict[str, Any]) -> Any:
        """Parse conversational response."""
        try:
            # Try to parse as JSON first
            parsed = json.loads(response)
            return parsed
        except json.JSONDecodeError:
            # If not valid JSON, return as text response
            return {
                "ready_to_plan": False,
                "response": response,
                "questions": []
            }
