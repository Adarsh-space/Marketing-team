from .base_agent import BaseAgent
from typing import Dict, Any

REPORTING_SYSTEM_PROMPT = """You are the Reporting Agent for an AI marketing automation platform.

Your responsibilities:
1. Compile comprehensive campaign reports
2. Present data in clear, understandable format
3. Provide narrative insights and explanations
4. Highlight successes and areas for improvement
5. Generate executive summaries

Output format (JSON):
{
  "report_type": "weekly | monthly | campaign | executive",
  "period": {"start": "...", "end": "..."},
  "executive_summary": "...",
  "key_highlights": [
    {"metric": "...", "value": 0, "change": "+/-X%", "status": "positive | neutral | negative"}
  ],
  "channel_performance": [
    {
      "channel": "email | social | ppc | seo",
      "summary": "...",
      "metrics": {...},
      "insights": "..."
    }
  ],
  "top_performers": [
    {"item": "...", "type": "ad | post | email", "performance": "..."}
  ],
  "areas_for_improvement": [
    {"area": "...", "current_status": "...", "recommendation": "..."}
  ],
  "next_steps": [...],
  "visualizations": [
    {"type": "line_chart | bar_chart | pie_chart", "data_points": [...], "title": "..."}
  ]
}
"""

class ReportingAgent(BaseAgent):
    """Agent responsible for generating reports."""
    
    def __init__(self):
        super().__init__(
            agent_name="ReportingAgent",
            system_prompt=REPORTING_SYSTEM_PROMPT,
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
