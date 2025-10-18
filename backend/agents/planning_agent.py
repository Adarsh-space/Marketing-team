from .base_agent import BaseAgent
from typing import Dict, Any
import json

PLANNING_SYSTEM_PROMPT = """You are the Planning Agent for an AI marketing automation platform.

Your task is to interpret a user's high-level marketing goal and generate a detailed, actionable campaign plan.

The plan should include:
1. **Objective:** A clear, measurable objective derived from the user's goal
2. **Key Tasks:** Sequential or parallel marketing tasks (Market Research, Content Creation, Email Campaign, Social Media, PPC, SEO, Analytics)
3. **Channel Strategy:** Recommended marketing channels for each task
4. **Timeline:** High-level timeline for each task (in days)
5. **Dependencies:** Inter-task or inter-agent dependencies
6. **KPIs:** Key Performance Indicators to measure success

You must output a structured JSON plan with the following format:
{
  "campaign_name": "...",
  "objective": "...",
  "target_audience": "...",
  "timeline_days": 30,
  "tasks": [
    {
      "task_id": "task_1",
      "task_name": "Market Research",
      "agent_assigned": "MarketResearchAgent",
      "description": "...",
      "estimated_duration_days": 2,
      "dependencies": [],
      "payload": { /* agent-specific parameters */ }
    },
    {
      "task_id": "task_2",
      "task_name": "Content Strategy",
      "agent_assigned": "ContentAgent",
      "description": "...",
      "estimated_duration_days": 3,
      "dependencies": ["task_1"],
      "payload": {}
    }
  ],
  "kpis": [
    {"metric": "Brand Awareness", "target": "25% increase"},
    {"metric": "Engagement Rate", "target": "5%"},
    {"metric": "Lead Generation", "target": "1000 leads"}
  ],
  "channels": ["Email", "Social Media", "PPC", "SEO"],
  "budget_allocation": {
    "email": 20,
    "social": 30,
    "ppc": 40,
    "seo": 10
  }
}

Be strategic, comprehensive, and realistic in your planning. Consider the target audience, product type, and desired outcomes.
"""

class PlanningAgent(BaseAgent):
    """Agent responsible for strategic campaign planning."""
    
    def __init__(self):
        super().__init__(
            agent_name="PlanningAgent",
            system_prompt=PLANNING_SYSTEM_PROMPT,
            model="gpt-4o"
        )
    
    def _prepare_prompt(self, task_payload: Dict[str, Any]) -> str:
        """Prepare planning prompt."""
        campaign_brief = task_payload.get('campaign_brief', {})
        
        prompt = f"""Create a comprehensive marketing campaign plan based on:

Product/Service: {campaign_brief.get('product', 'Not specified')}
Target Audience: {campaign_brief.get('target_audience', 'Not specified')}
Objective: {campaign_brief.get('objective', 'Not specified')}
Budget: {campaign_brief.get('budget', 'Flexible')}
Timeline: {campaign_brief.get('timeline', '30-60 days')}
Preferred Channels: {', '.join(campaign_brief.get('channels', ['Email', 'Social Media', 'PPC', 'SEO']))}
Additional Context: {campaign_brief.get('additional_context', 'None')}

Generate a complete campaign plan as a JSON object.
"""
        return prompt
    
    def _parse_response(self, response: str, task_payload: Dict[str, Any]) -> Any:
        """Parse planning response to JSON."""
        try:
            # Extract JSON from response (handle markdown code blocks)
            if '```json' in response:
                start = response.find('```json') + 7
                end = response.find('```', start)
                response = response[start:end].strip()
            elif '```' in response:
                start = response.find('```') + 3
                end = response.find('```', start)
                response = response[start:end].strip()
            
            plan = json.loads(response)
            return plan
        except json.JSONDecodeError as e:
            return {
                "error": f"Failed to parse plan: {str(e)}",
                "raw_response": response
            }
