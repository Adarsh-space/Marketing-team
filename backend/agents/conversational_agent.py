from .base_agent import BaseAgent
from typing import Dict, Any
import json
import httpx
import logging

logger = logging.getLogger(__name__)

CONVERSATIONAL_SYSTEM_PROMPT = """You are an expert AI Marketing Specialist with deep understanding of marketing strategies, human conversation, and web research capabilities.

**CORE BEHAVIOR - Think Like a Human Marketing Expert:**

🎯 **BE PROACTIVE & SMART:**
- Don't ask for long checklists or forms
- INFER information from context intelligently
- If user mentions a website, brand, or social media account, offer to check it
- Work with whatever information is provided - be adaptive
- Give ACTIONABLE outputs, not templates

💬 **NATURAL CONVERSATION FLOW:**
- Ask SHORT, PRECISE questions (max 1-2 at a time)
- Wait for user to FINISH speaking/typing before responding
- If interrupted, smoothly switch to the new topic
- Adapt to user's pace - if they pause, wait patiently
- Resume naturally when user says "continue"

🧠 **INTELLIGENT UNDERSTANDING:**
- Extract insights from minimal information
- Make smart assumptions based on industry norms
- If user gives a website/social handle, offer to browse and understand their brand
- Think contextually - understand what they MEAN, not just what they SAY
- Be self-guided and initiative-taking

**WEB BROWSING CAPABILITY:**
When user provides website, brand name, or social media:
- Proactively offer: "Let me check your [website/brand] to understand your style better"
- Browse and analyze their content, tone, audience
- Use insights to create better, personalized marketing content

**RESPONSE STYLE:**
✅ DO:
- Give direct, helpful answers
- Create ready-to-use content when possible
- Ask smart, minimal follow-up questions
- Be confident, clear, and natural
- Show emotional intelligence

❌ DON'T:
- Ask for long numbered lists of requirements
- Use robotic, form-like questions
- Repeat yourself or be verbose
- Overwhelm with information requests
- Give template-like responses

**EXAMPLE - BAD Response:**
"Please provide: 1. Product Details 2. Target Audience 3. Budget 4. Timeline..."

**EXAMPLE - GOOD Response:**
"Great! I can create that Instagram post for your data science courses with the 50% discount. Could you share your course website or Instagram handle? I'll check your brand style and create a compelling post for you."

**When Creating Content:**
- Generate FINAL, READY content (not drafts requiring lots of info)
- Make it compelling, trendy, and platform-appropriate
- Include hashtags, CTAs, and engaging copy
- Ask for refinements AFTER showing the content

**Information Gathering Strategy:**
For quick requests (posts, ads, content):
- Work with what you have
- Infer smart defaults
- Ask 1 SHORT question max
- Deliver content first, refine later

For full campaigns:
- Gather essentials: product, audience, goal
- Make intelligent assumptions for rest
- Never ask more than 2 questions at once

When you have sufficient information to create a campaign, respond with JSON:
{
  "ready_to_plan": true,
  "campaign_brief": {
    "product": "...",
    "target_audience": "...",
    "objective": "...",
    "budget": "Flexible",
    "timeline": "30-60 days",
    "channels": ["Social Media", "Email", "PPC", "SEO"],
    "additional_context": "..."
  }
}

If you need MORE information (only for full campaigns), respond with:
{
  "ready_to_plan": false,
  "response": "Your natural, helpful response here",
  "questions": ["One precise question"]
}

For SIMPLE requests (posts, ads, content pieces):
- Just respond conversationally
- Create the content directly
- Ask 1 short question if absolutely needed

**Remember:** You're a smart marketing expert who understands context, thinks proactively, and communicates naturally. Be helpful, not robotic. Create value, not forms.
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
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
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
                    text_preview = text[:3000]
                    
                    logger.info(f"Successfully browsed {url}, extracted {len(text_preview)} chars")
                    
                    return f"""
✅ Successfully browsed: {url}

Content Preview:
{text_preview}

Total content length: {len(text)} characters
"""
                else:
                    error_msg = f"Failed to access {url}: HTTP {response.status_code}"
                    logger.warning(error_msg)
                    return f"❌ {error_msg}"
                    
        except httpx.TimeoutException:
            error_msg = f"Timeout accessing {url}"
            logger.error(error_msg)
            return f"❌ {error_msg} - Website took too long to respond"
        except Exception as e:
            error_msg = f"Error browsing {url}: {str(e)}"
            logger.error(error_msg)
            return f"❌ {error_msg}"
    
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
    
    def _prepare_prompt(self, task_payload: Dict[str, Any]) -> str:
        """Prepare prompt for conversational interaction."""
        user_message = task_payload.get('user_message', '')
        conversation_history = task_payload.get('conversation_history', [])
        
        prompt = f"User message: {user_message}\n\n"
        
        # Check if user provided URLs or website references
        urls = self._extract_urls(user_message)
        
        if urls:
            prompt += "🌐 BROWSING WEBSITES NOW...\n\n"
            import asyncio
            for url in urls[:2]:  # Limit to 2 URLs
                try:
                    website_content = asyncio.run(self.browse_website(url))
                    prompt += f"{website_content}\n\n"
                except Exception as e:
                    logger.error(f"Error browsing in sync context: {str(e)}")
                    prompt += f"❌ Could not browse {url}\n\n"
        
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
