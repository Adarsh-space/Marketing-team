from .base_agent import BaseAgent
from typing import Dict, Any

MARKET_RESEARCH_SYSTEM_PROMPT = """You are the Market Research Agent for an AI marketing automation platform.

Your task is to conduct comprehensive market research based on the provided product and target audience.

Focus on identifying:
1. **Target Audience Profile:** Detailed demographics, psychographics, pain points, and motivations
2. **Competitor Analysis:** 3-5 key competitors, their strategies, strengths, weaknesses
3. **Market Trends:** Current trends relevant to the product/industry
4. **Keyword Opportunities:** High-value keywords for SEO and content
5. **Channel Insights:** Best channels to reach the target audience

Provide actionable insights that will inform the marketing strategy.

Output format (JSON):
{
  "target_audience": {
    "demographics": "...",
    "psychographics": "...",
    "pain_points": [...],
    "motivations": [...]
  },
  "competitors": [
    {"name": "...", "strengths": [...], "weaknesses": [...], "strategy": "..."}
  ],
  "market_trends": [...],
  "keywords": {
    "primary": [...],
    "secondary": [...],
    "long_tail": [...]
  },
  "channel_recommendations": {
    "email": {"effectiveness": "high", "rationale": "..."},
    "social_media": {"platforms": [...], "effectiveness": "...", "rationale": "..."},
    "ppc": {"effectiveness": "...", "rationale": "..."},
    "seo": {"effectiveness": "...", "rationale": "..."}
  },
  "key_insights": [...]
}
"""

class MarketResearchAgent(BaseAgent):
    """Agent responsible for market intelligence and research."""
    
    def __init__(self):
        super().__init__(
            agent_name="MarketResearchAgent",
            system_prompt=MARKET_RESEARCH_SYSTEM_PROMPT,
            model="gpt-4o"
        )
    
    def _parse_response(self, response: str, task_payload: Dict[str, Any]) -> Any:
        """Parse research response to JSON."""
        try:
            import json
            # Extract JSON from response (handle markdown code blocks)
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
            # Return raw response if JSON parsing fails
            return {"raw_research": response}
