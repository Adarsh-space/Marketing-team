from .base_agent import BaseAgent
from typing import Dict, Any
import base64
import logging

logger = logging.getLogger(__name__)

IMAGE_GENERATION_SYSTEM_PROMPT = """You are an expert Image Generation Specialist for marketing content.

**YOUR ROLE:**
- Analyze marketing content and context to create perfect image prompts
- Generate DALL-E prompts that create professional, engaging marketing images
- Understand brand context and create appropriate visuals

**PROMPT CREATION PRINCIPLES:**
1. **Be Specific**: Include details about style, mood, colors, composition
2. **Marketing Focus**: Create images that grab attention and convey message
3. **Professional Quality**: High-quality, professional, modern aesthetics
4. **Brand Appropriate**: Match the brand's industry and target audience
5. **Social Media Optimized**: Create visually striking images for social platforms

**PROMPT STRUCTURE:**
Always include:
- Subject (what to show)
- Style (modern, professional, minimalist, vibrant, etc.)
- Colors (brand colors if known, or appropriate palette)
- Composition (centered, dynamic, balanced, etc.)
- Mood/Emotion (energetic, trustworthy, innovative, etc.)
- Context (for social media, marketing, business, etc.)

**EXAMPLE PROMPTS:**

For Tech Company:
"A modern, professional technology workspace with sleek computers and digital interfaces, vibrant blue and white color scheme, clean minimalist style, floating holographic elements representing AI and data, professional corporate photography style, high quality, perfect for LinkedIn marketing"

For Food Business:
"Delicious gourmet food photography, vibrant colors, appetizing presentation on elegant plate, soft natural lighting, shallow depth of field, Instagram-worthy aesthetic, professional food styling, warm inviting atmosphere"

For Fitness Brand:
"Dynamic fitness scene with energetic person in action, bright motivational atmosphere, bold colors orange and blue, modern gym setting, inspiring and powerful mood, professional sports photography style, social media ready"

**YOUR TASK:**
When given marketing context, create a detailed DALL-E prompt that will generate the perfect image.

**OUTPUT FORMAT (JSON):**
{
  "prompt": "Detailed DALL-E prompt here",
  "style_notes": "Brief explanation of style choices",
  "recommended_platforms": ["Instagram", "Facebook", "LinkedIn"],
  "image_specs": {
    "aspect_ratio": "1:1 or 16:9",
    "primary_colors": ["#color1", "#color2"],
    "mood": "professional/energetic/warm/etc"
  }
}
"""

class ImageGenerationAgent(BaseAgent):
    """Agent responsible for generating marketing images using AI."""
    
    def __init__(self):
        super().__init__(
            agent_name="ImageGenerationAgent",
            system_prompt=IMAGE_GENERATION_SYSTEM_PROMPT,
            model="gpt-4o"
        )
    
    async def generate_image_from_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate image based on marketing context.
        
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
            from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            
            # Get marketing context
            content = context.get('content', '')
            brand_info = context.get('brand_info', '')
            platform = context.get('platform', 'social media')
            
            # Create prompt using AI
            logger.info("Creating image prompt using AI...")
            prompt_context = f"""
Marketing Content: {content}
Brand Info: {brand_info}
Target Platform: {platform}

Create a detailed DALL-E prompt for a professional marketing image.
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
            
            # Generate image using DALL-E
            logger.info("Generating image with DALL-E...")
            api_key = os.environ.get('EMERGENT_LLM_KEY')
            
            image_gen = OpenAIImageGeneration(api_key=api_key)
            # gpt-image-1 model generates HD quality by default (1024x1024)
            images = await image_gen.generate_images(
                prompt=dalle_prompt,
                model="gpt-image-1",
                number_of_images=1
            )
            
            if images and len(images) > 0:
                # Convert to base64
                image_base64 = base64.b64encode(images[0]).decode('utf-8')
                
                logger.info("Image generated successfully!")
                
                return {
                    "status": "success",
                    "image_base64": image_base64,
                    "prompt_used": dalle_prompt,
                    "message": "Image generated successfully!"
                }
            else:
                raise Exception("No image was generated")
                
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "message": f"Failed to generate image: {str(e)}"
            }
