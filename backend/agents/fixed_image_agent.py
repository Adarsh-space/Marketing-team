"""
Fixed Image Generation Agent with proper OpenAI SDK integration
Works with standard OpenAI SDK - no custom dependencies needed
"""

from .base_agent import BaseAgent
from typing import Dict, Any
import base64
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

IMAGE_GENERATION_SYSTEM_PROMPT = """You are an expert Image Generation Specialist for marketing content.

COMMUNICATION RULES:
- Speak naturally and professionally
- DO NOT use emojis or special symbols in your communication
- Write in clear, plain English

YOUR ROLE:
- Analyze marketing content and context to create perfect image prompts
- Generate DALL-E prompts that create professional, engaging marketing images
- Understand brand context and create appropriate visuals

PROMPT CREATION PRINCIPLES:
1. Be Specific: Include details about style, mood, colors, composition
2. Marketing Focus: Create images that grab attention and convey message
3. Professional Quality: High-quality, professional, modern aesthetics
4. Brand Appropriate: Match the brand's industry and target audience
5. Social Media Optimized: Create visually striking images for social platforms

PROMPT STRUCTURE:
Always include:
- Subject (what to show)
- Style (modern, professional, minimalist, vibrant, etc.)
- Colors (brand colors if known, or appropriate palette)
- Composition (centered, dynamic, balanced, etc.)
- Mood/Emotion (energetic, trustworthy, innovative, etc.)
- Context (for social media, marketing, business, etc.)

OUTPUT FORMAT (JSON):
{
  "prompt": "Detailed DALL-E prompt here",
  "style_notes": "Brief explanation of style choices",
  "recommended_platforms": ["Instagram", "Facebook", "LinkedIn"]
}
"""

class FixedImageAgent(BaseAgent):
    """
    Fixed image generation agent using standard OpenAI SDK.
    Generates HD marketing images reliably.
    """

    def __init__(self):
        super().__init__(
            agent_name="FixedImageAgent",
            system_prompt=IMAGE_GENERATION_SYSTEM_PROMPT,
            model="gpt-4o"
        )
        logger.info("FixedImageAgent initialized with OpenAI SDK")

    async def generate_image_from_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a high-quality marketing image.

        Args:
            context: Dictionary containing:
                - content: Marketing content/post text
                - brand_info: Brand information
                - platform: Target platform (Instagram, Facebook, etc.)
                - style_preferences: Any style preferences

        Returns:
            Dictionary with image_base64 and metadata
        """
        try:
            # Extract context
            content = context.get('content', '')
            brand_info = context.get('brand_info', '')
            platform = context.get('platform', 'social media')

            logger.info("Creating image prompt using AI...")

            # Create prompt using AI
            prompt_context = f"""
Marketing Content: {content}
Brand Info: {brand_info}
Target Platform: {platform}

Create a detailed DALL-E prompt for a professional marketing image.
Remember: Communicate plainly without emojis or special formatting.
"""

            # Get AI-generated prompt
            response = await self.execute({
                "user_message": prompt_context,
                "task_id": "image_prompt_generation"
            })

            result = response.get("result", {})

            # Extract prompt (handle both JSON and plain text responses)
            if isinstance(result, dict):
                dalle_prompt = result.get("prompt", str(result))
            elif isinstance(result, str):
                # Try to extract JSON
                import json
                try:
                    parsed = json.loads(result)
                    dalle_prompt = parsed.get("prompt", result)
                except:
                    dalle_prompt = result
            else:
                dalle_prompt = str(result)

            logger.info(f"Generated prompt: {dalle_prompt[:200]}...")

            # Generate image using OpenAI SDK directly
            logger.info("Generating image with DALL-E...")

            # Use standard OpenAI SDK
            try:
                from openai import AsyncOpenAI

                api_key = os.environ.get('OPENAI_API_KEY')
                if not api_key:
                    # Try EMERGENT_LLM_KEY as fallback
                    api_key = os.environ.get('EMERGENT_LLM_KEY')

                if not api_key:
                    raise Exception("No API key found. Set OPENAI_API_KEY or EMERGENT_LLM_KEY in .env")

                client = AsyncOpenAI(api_key=api_key)

                # Generate image with DALL-E 3 (HD quality)
                response = await client.images.generate(
                    model="dall-e-3",
                    prompt=dalle_prompt,
                    size="1024x1024",  # HD quality
                    quality="standard",  # Use "hd" for even higher quality
                    n=1
                )

                # Get the image URL
                image_url = response.data[0].url

                # Download the image
                import httpx
                async with httpx.AsyncClient() as http_client:
                    img_response = await http_client.get(image_url)
                    image_bytes = img_response.content

                # Convert to base64
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')

                logger.info("Image generated successfully with DALL-E 3!")

                return {
                    "status": "success",
                    "image_base64": image_base64,
                    "prompt_used": dalle_prompt,
                    "model": "dall-e-3",
                    "size": "1024x1024",
                    "message": "Image generated successfully with HD quality!"
                }

            except ImportError:
                raise Exception("OpenAI SDK not installed. Run: pip install openai")
            except Exception as e:
                logger.error(f"OpenAI SDK error: {str(e)}")
                raise

        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "message": f"Failed to generate image: {str(e)}. Check that your OPENAI_API_KEY is set correctly."
            }
