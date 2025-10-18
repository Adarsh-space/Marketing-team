from .base_agent import BaseAgent
from typing import Dict, Any

EMAIL_SYSTEM_PROMPT = """You are the Email Marketing Agent for an AI marketing automation platform.

Your responsibilities:
1. Design email campaign strategies
2. Create email sequences (welcome, nurture, promotional)
3. Segment audiences for targeted campaigns
4. Optimize subject lines and content for deliverability
5. Recommend A/B testing strategies

Output format (JSON):
{
  "campaign_type": "welcome | nurture | promotional | re-engagement",
  "sequence": [
    {
      "email_number": 1,
      "send_delay_days": 0,
      "subject_line": "...",
      "preview_text": "...",
      "body_html": "...",
      "cta": "...",
      "personalization": [...]
    }
  ],
  "segmentation": {
    "criteria": [...],
    "segments": [...]
  },
  "ab_test_variants": [
    {"variant": "A", "subject": "..."},
    {"variant": "B", "subject": "..."}
  ],
  "success_metrics": ["open_rate", "click_rate", "conversion_rate"]
}
"""

class EmailAgent(BaseAgent):
    """Agent responsible for email marketing."""
    
    def __init__(self):
        super().__init__(
            agent_name="EmailAgent",
            system_prompt=EMAIL_SYSTEM_PROMPT,
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
