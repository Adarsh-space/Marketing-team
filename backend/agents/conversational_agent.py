from .base_agent import BaseAgent
from typing import Dict, Any
import json
import httpx
import logging

logger = logging.getLogger(__name__)

CONVERSATIONAL_SYSTEM_PROMPT = """You are a friendly, intelligent AI marketing assistant who talks naturally like a real human - warm, helpful, and conversational.

CRITICAL CONTEXT AWARENESS:
- YOU HAVE PERFECT MEMORY via vector memory system - I can access our entire conversation history
- VECTOR MEMORY: When you see "RELEVANT CONTEXT FROM MEMORY" in my input, USE that information naturally
- NEVER ask for information already provided - reference it: "I remember you mentioned..."
- I work with a TEAM OF SPECIALIST AGENTS who handle specific marketing tasks

MY CAPABILITIES:
1. Generate images using DALL-E AI
2. Browse websites automatically
3. Remember everything about you via vector memory
4. Create marketing content
5. Coordinate with specialist agents:
   - PlanningAgent: Creates strategic campaign plans
   - ScrapingAgent: Gathers contact data from Google Maps, LinkedIn, websites
   - ContentAgent: Creates compelling copy and creative
   - EmailAgent: Sends email campaigns via Zoho Mail
   - SocialMediaAgent: Posts to Facebook, Instagram, Twitter, LinkedIn
   - MarketResearchAgent: Analyzes markets and competitors
   - AnalyticsAgent: Tracks performance and ROI
   - And 5 more specialists

VECTOR MEMORY USAGE:
When you see context like:
"RELEVANT CONTEXT FROM MEMORY:
- User runs SaaS company called TechFlow
- Previous budget: $5,000
- Preferred channels: LinkedIn, Email"

Use it naturally:
✅ "Since TechFlow targets B2B customers, LinkedIn makes perfect sense..."
✅ "Based on your previous $5K budget, here's what we can achieve..."
❌ "What's your budget?" (when it's already in memory)

MULTI-AGENT COORDINATION:
When creating campaigns, I orchestrate other agents:
1. I gather requirements from you
2. PlanningAgent creates strategic plan with task assignments
3. ScrapingAgent finds target contacts (if needed)
4. ContentAgent creates personalized messaging
5. EmailAgent/SocialMediaAgent execute campaigns
6. AnalyticsAgent tracks results

ALL AGENTS SHARE DATA:
- Orchestrator passes results between agents
- Collaboration System: Agents publish events to each other
- Vector Memory: Shared context across all agents

CONVERSATION STYLE:
- Talk naturally like a friendly human colleague
- Use simple, flowing sentences
- Be warm and helpful
- NO bullet points, asterisks in "response" field
- Reference memory naturally

CRITICAL: YOUR RESPONSE FORMAT
You MUST ALWAYS respond with ONLY valid JSON. No extra text before or after.

**FOR NORMAL CONVERSATION:**
Respond with ONLY this JSON:
{
  "ready_to_plan": false,
  "response": "Your natural friendly response here in plain English"
}

**WHEN USER HAS PROVIDED ENOUGH INFO FOR A CAMPAIGN:**
Respond with ONLY this JSON:
{
  "ready_to_plan": true,
  "response": "Perfect! I have everything needed. I'll work with our specialist agents - PlanningAgent will create the strategy, then ScrapingAgent, ContentAgent, and EmailAgent will execute it together",
  "campaign_brief": {
    "product": "product name",
    "target_audience": "audience description",
    "objective": "campaign goal",
    "channels": ["Social Media", "Email"],
    "scraping_required": true,
    "scraping_source": "google_maps",
    "scraping_query": "restaurants",
    "scraping_location": "New York, NY"
  }
}

NOTE: Include scraping_required: true if user needs contact data gathered. ScrapingAgent will handle it.

**EXAMPLES OF CORRECT RESPONSES:**

User: "Generate an image for my tech company"
Your response:
{
  "ready_to_plan": false,
  "response": "I will create a professional tech image for you right now",
  "image_request": true,
  "image_context": {
    "content": "Modern professional technology company image with innovative design elements and tech symbols",
    "platform": "social media"
  }
}

User: "What services do you offer?"
Your response:
{
  "ready_to_plan": false,
  "response": "I can help you with marketing campaigns, content creation, social media strategy, SEO optimization and much more. What are you most interested in?"
}

REMEMBER: 
- ONLY output valid JSON
- NO text before or after the JSON
- Keep "response" field natural and conversational
- NO special symbols or formatting in "response" field
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
        """Browse a website and extract content using web scraping."""
        try:
            # Ensure URL has protocol
            if not url.startswith('http'):
                url = 'https://' + url
            
            logger.info(f"Browsing website: {url}")
            
            async with httpx.AsyncClient(
                timeout=15.0,
                follow_redirects=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            ) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    # Extract text content
                    html = response.text
                    
                    # Simple text extraction (remove HTML tags)
                    import re
                    # Remove script and style elements
                    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
                    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
                    # Remove HTML tags
                    text = re.sub(r'<[^>]+>', ' ', html)
                    # Clean up whitespace
                    text = re.sub(r'\s+', ' ', text).strip()
                    
                    # Get first 3000 chars
                    text_preview = text[:3000] if text else "No text content found"
                    
                    logger.info(f"Successfully browsed {url}, extracted {len(text_preview)} chars")
                    
                    return f"""
✅ I've checked {url}!

Here's what I found:
{text_preview}
"""
                else:
                    error_msg = f"Website returned HTTP {response.status_code}"
                    logger.warning(f"{error_msg} for {url}")
                    return f"⚠️ {error_msg}"
                    
        except httpx.TimeoutException as e:
            error_msg = f"Website took too long to respond"
            logger.error(f"{error_msg}: {url} - {str(e)}")
            return f"⚠️ {error_msg}"
        except httpx.HTTPError as e:
            error_msg = f"Network error accessing website"
            logger.error(f"{error_msg}: {url} - {str(e)}")
            return f"⚠️ {error_msg}: {str(e)}"
        except Exception as e:
            error_msg = f"Could not access website"
            logger.error(f"{error_msg}: {url} - {type(e).__name__}: {str(e)}")
            return f"⚠️ {error_msg}: {type(e).__name__}"
    
    def _extract_urls(self, text: str) -> list:
        """Extract URLs from text."""
        import re
        # Pattern to match URLs and domain names
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        domain_pattern = r'\b(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?\b'
        
        urls = re.findall(url_pattern, text)
        
        # Also find domain names and convert to URLs
        if not urls:
            domains = re.findall(domain_pattern, text)
            urls = [d if d.startswith('http') else f'https://{d}' for d in domains]
        
        return urls
    
    async def execute(self, task_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent task with web browsing support.
        Overrides base execute to handle async web browsing.
        """
        try:
            session_id = f"{self.agent_name}_{task_payload.get('task_id', 'unknown')}"
            
            # Check if user provided URLs and browse them FIRST
            user_message = task_payload.get('user_message', '')
            urls = self._extract_urls(user_message)
            
            website_info = ""
            if urls:
                logger.info(f"Found URLs to browse: {urls}")
                for url in urls[:2]:  # Limit to 2 URLs
                    try:
                        content = await self.browse_website(url)
                        website_info += f"\n{content}\n"
                    except Exception as e:
                        logger.error(f"Error browsing {url}: {str(e)}")
                        website_info += f"\n❌ Could not browse {url}\n"
            
            # Add website info to task payload
            if website_info:
                task_payload['website_browsing_results'] = website_info
            
            # Prepare user message with website info
            user_prompt = self._prepare_prompt_with_browsing(task_payload)
            
            # Initialize LLM chat
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id,
                system_message=self.system_prompt
            ).with_model("openai", self.model)
            
            user_msg = UserMessage(text=user_prompt)
            
            # Get LLM response
            logger.info(f"{self.agent_name} processing task...")
            response = await chat.send_message(user_msg)
            
            # Parse and structure response
            result = self._parse_response(response, task_payload)
            
            return {
                "status": "success",
                "agent": self.agent_name,
                "result": result,
                "task_id": task_payload.get('task_id')
            }
            
        except Exception as e:
            logger.error(f"{self.agent_name} error: {str(e)}")
            return {
                "status": "error",
                "agent": self.agent_name,
                "error": str(e),
                "task_id": task_payload.get('task_id')
            }
    
    def _prepare_prompt_with_browsing(self, task_payload: Dict[str, Any]) -> str:
        """Prepare prompt with browsing results and vector memory if available."""
        user_message = task_payload.get('user_message', '')
        conversation_history = task_payload.get('conversation_history', [])
        website_browsing = task_payload.get('website_browsing_results', '')
        vector_context = task_payload.get('vector_context', '')
        
        prompt = f"User message: {user_message}\n\n"
        
        # Add vector memory context if available (MOST IMPORTANT!)
        if vector_context:
            prompt += f"📝 YOUR MEMORY (What you remember about this user):\n{vector_context}\n\n"
            prompt += "⚠️ IMPORTANT: Use this memory! Don't ask for info already here!\n\n"
        
        # Add website browsing results if available
        if website_browsing:
            prompt += f"🌐 WEBSITE CONTENT:\n{website_browsing}\n\n"
        
        # Add recent conversation
        if conversation_history:
            prompt += "Recent conversation:\n"
            for msg in conversation_history[-3:]:  # Only last 3 to save tokens
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
            # If not JSON, try to extract JSON from text
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                try:
                    parsed = json.loads(json_match.group(0))
                    logger.info(f"Extracted JSON from text response")
                    return parsed
                except:
                    pass
            
            # If still no JSON, return as plain response
            logger.warning(f"Could not parse JSON from response, returning as plain text")
            return {
                "ready_to_plan": False,
                "response": response,
                "questions": []
            }
