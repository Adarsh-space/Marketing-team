from .base_agent import BaseAgent
from typing import Dict, Any

SOCIAL_SYSTEM_PROMPT = """You are the Social Media Agent for an AI marketing automation platform.

Your responsibilities:
1. Create platform-specific social media content
2. Design content calendars
3. Optimize posting schedules
4. Generate engagement strategies
5. Monitor trends and hashtags

Output format (JSON):
{
  "content_calendar": [
    {
      "date": "2025-01-15",
      "platform": "instagram",
      "post_type": "image | video | carousel | story",
      "content": {
        "caption": "...",
        "hashtags": [...],
        "mentions": [...],
        "visual_description": "..."
      },
      "best_posting_time": "18:00",
      "expected_engagement": "high | medium | low"
    }
  ],
  "platform_strategy": {
    "instagram": {"focus": "...", "frequency": "..."},
    "linkedin": {"focus": "...", "frequency": "..."},
    "twitter": {"focus": "...", "frequency": "..."},
    "facebook": {"focus": "...", "frequency": "..."}
  },
  "hashtag_strategy": {
    "brand_hashtags": [...],
    "trending_hashtags": [...],
    "niche_hashtags": [...]
  }
}
"""

class SocialMediaAgent(BaseAgent):
    """Agent responsible for social media management."""
    
    def __init__(self):
        super().__init__(
            agent_name="SocialMediaAgent",
            system_prompt=SOCIAL_SYSTEM_PROMPT,
            model="gpt-4o"
        )
    
    def _parse_response(self, response: str, task_payload: Dict[str, Any]) -> Any:
        """Parse agent response to JSON."""
        try:
            import json
            if '```json' in response:
                start = response.find('```json') + 7
                end = response.find('```', start)
                response = response[start:end].strip()
            elif '```' in response:
                start = response.find('```') + 3
                end = response.find('```', start)
                response = response[start:end].strip()
            return json.loads(response)
        except json.JSONDecodeError:
            return {"result": response}
