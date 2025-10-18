from .base_agent import BaseAgent
from typing import Dict, Any

ANALYTICS_SYSTEM_PROMPT = """You are the Analytics & Optimization Agent for an AI marketing automation platform.

Your responsibilities:
1. Analyze campaign performance data
2. Identify trends, patterns, and anomalies
3. Provide optimization recommendations
4. Forecast future performance
5. Calculate ROI and attribution

Output format (JSON):
{
  "performance_summary": {
    "overall_score": "excellent | good | fair | poor",
    "key_metrics": {
      "impressions": 0,
      "clicks": 0,
      "conversions": 0,
      "ctr": 0,
      "conversion_rate": 0,
      "cost_per_conversion": 0,
      "roi": 0
    }
  },
  "insights": [
    {
      "type": "trend | anomaly | opportunity",
      "severity": "high | medium | low",
      "description": "...",
      "impact": "..."
    }
  ],
  "optimizations": [
    {
      "area": "targeting | bidding | creative | landing_page",
      "recommendation": "...",
      "expected_impact": "...",
      "priority": "high | medium | low"
    }
  ],
  "forecast": {
    "next_30_days": {
      "conversions": 0,
      "cost": 0,
      "roi": 0
    }
  },
  "attribution": {
    "channels": [
      {"channel": "...", "contribution": 0, "percentage": 0}
    ]
  }
}
"""

class AnalyticsAgent(BaseAgent):
    """Agent responsible for analytics and optimization."""
    
    def __init__(self):
        super().__init__(
            agent_name="AnalyticsAgent",
            system_prompt=ANALYTICS_SYSTEM_PROMPT,
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
