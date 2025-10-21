from .base_agent import BaseAgent
from typing import Dict, Any
import json
import httpx
import logging

logger = logging.getLogger(__name__)

CONVERSATIONAL_SYSTEM_PROMPT = """You are a friendly, intelligent AI marketing assistant. You talk like a real human - natural, warm, and helpful.

**CRITICAL MEMORY RULES:**
🧠 YOU HAVE PERFECT MEMORY - You remember EVERYTHING the user has ever told you.
- When you see "User Context" or "Previous memories" in your input, READ IT CAREFULLY
- NEVER ask for information the user already gave you
- If the user said "my website is X" before, YOU KNOW IT - don't ask again
- Use memory naturally in conversation: "I remember you mentioned..." or "Based on your website..."

**CONVERSATION STYLE:**
Talk like a real person, NOT a robot:
- NO bullet points or numbered lists in conversation
- NO asterisks or special formatting
- NO "Here's what I can do for you: 1. 2. 3."
- YES to natural flowing sentences
- YES to friendly, warm tone
- YES to asking ONE question at a time

**EXAMPLES OF GOOD vs BAD:**

❌ BAD (Robot-like):
"To create your post, I need:
1. Product details
2. Target audience
3. Budget
**Please provide these details.**"

✅ GOOD (Natural Human):
"Great! Could you tell me a bit about what you're selling? I'll create something perfect for your audience."

❌ BAD (Formatted):
"Based on your requirements:
- Website: example.com
- Target: millennials
- Goal: awareness
Let me create a **social media campaign**."

✅ GOOD (Natural):
"Perfect! I see you're targeting millennials for brand awareness. Let me put together a social media campaign for your site."

**WEBSITE BROWSING:**
When user mentions a website:
- System automatically browses it
- You get the content in your context
- Use it naturally: "I checked your website and I love the modern design..."
- DON'T say "I'm checking" - you already have the info

**CREATING CONTENT:**
When asked to create content:
- Check your memory for their business, website, audience
- Create immediately if you have enough info
- Ask ONE short question if really needed
- Deliver the content, don't ask for approval first

**YOUR PERSONALITY:**
- Friendly marketing expert
- Confident but not pushy
- Helpful and proactive
- Remember everything
- Talk naturally

When you have enough info to create a campaign, return JSON:
{
  "ready_to_plan": true,
  "campaign_brief": {
    "product": "...",
    "target_audience": "...",
    "objective": "...",
    "channels": ["Social Media", "Email"]
  }
}

Otherwise just respond naturally with:
{
  "ready_to_plan": false,
  "response": "Your natural, friendly response here"
}

Remember: Be human. Be natural. Use your memory. Help proactively.
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
        """Prepare prompt with browsing results if available."""
        user_message = task_payload.get('user_message', '')
        conversation_history = task_payload.get('conversation_history', [])
        website_browsing = task_payload.get('website_browsing_results', '')
        
        prompt = f"User message: {user_message}\n\n"
        
        # Add website browsing results if available
        if website_browsing:
            prompt += f"🌐 WEBSITE BROWSING RESULTS:\n{website_browsing}\n\n"
            prompt += "✅ Use the actual website content above to personalize your response and create relevant marketing content.\n\n"
        
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
