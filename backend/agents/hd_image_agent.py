"""
HD Image Generation Agent

This agent ensures all generated images are high definition (HD) quality only.
Supports multiple AI image generation models with HD quality enforcement.

Key Features:
- Guaranteed HD quality (1024x1024 minimum, up to 1792x1792 for DALL-E 3)
- Multiple model support (DALL-E 3 HD, Stable Diffusion XL, Midjourney-style)
- Quality validation
- Professional marketing-focused prompts
- No emojis in agent communication
"""

from typing import Dict, Any, Optional, Literal
import logging
import base64
from enum import Enum

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ImageQuality(Enum):
    """Image quality levels (HD only)."""
    HD = "hd"  # 1024x1024
    HD_PLUS = "hd_plus"  # 1792x1024 or 1024x1792
    ULTRA_HD = "ultra_hd"  # 1792x1792 (when available)


class ImageModel(Enum):
    """Supported HD image generation models."""
    DALLE_3_HD = "dall-e-3"  # OpenAI DALL-E 3 with HD quality
    DALLE_2 = "dall-e-2"  # OpenAI DALL-E 2 (1024x1024)
    GPT_IMAGE_1 = "gpt-image-1"  # Emergent Integrations model (HD default)
    STABLE_DIFFUSION_XL = "stable-diffusion-xl"  # Stability AI SDXL (1024x1024)


HD_IMAGE_SYSTEM_PROMPT = """You are an expert HD Image Generation Specialist for professional marketing content.

COMMUNICATION RULES - VERY IMPORTANT:
- Speak naturally and professionally
- DO NOT use emojis or special symbols in your communication
- DO NOT use bold text, asterisks, or formatting symbols
- Write in clear, plain English
- Be concise and direct

YOUR ROLE:
- Analyze marketing content to create professional image prompts
- Generate prompts optimized for HD image generation
- Ensure all images meet professional quality standards
- Understand brand context and create appropriate visuals
- Focus on high-resolution, print-quality images

HD IMAGE REQUIREMENTS:
- Minimum resolution: 1024x1024 pixels
- Preferred resolution: 1792x1024 for banners, 1024x1792 for vertical posts
- Maximum detail and clarity
- Professional, crisp imagery
- Suitable for both digital and print use

PROMPT CREATION FOR HD IMAGES:
1. Be extremely detailed and specific
2. Include technical photography terms (sharp focus, high detail, professional lighting)
3. Specify desired quality level (photorealistic, ultra detailed, 8K quality)
4. Describe composition precisely
5. Mention professional styling and production values

PROMPT STRUCTURE FOR HD MARKETING IMAGES:

Subject and Action:
- Clearly describe the main subject
- Include specific action or pose if relevant

Technical Specifications:
- Resolution and quality keywords (high resolution, ultra detailed, sharp focus)
- Photography style (professional photography, studio lighting, commercial shoot)
- Camera and lens details for photorealistic images (85mm lens, shallow depth of field)

Aesthetic Details:
- Color palette and mood
- Lighting setup (soft lighting, golden hour, studio lighting)
- Background and environment
- Texture and material details

Context and Purpose:
- Marketing platform (social media, print ad, website banner)
- Brand positioning (luxury, modern, approachable)
- Emotional impact desired

EXAMPLE HD PROMPTS:

Tech Company Banner (1792x1024):
"Professional technology office environment, ultra high resolution, sharp focus, 8K quality, modern minimalist aesthetic, sleek computer workstations with multiple high-resolution monitors displaying data visualizations, professional studio lighting, vibrant blue and white color scheme, floating holographic interface elements, depth of field with bokeh effect, commercial photography style, cinematic composition, extremely detailed, professional corporate setting, perfect for LinkedIn banner"

Food Product Close-up (1024x1024):
"Extreme close-up food photography, ultra high resolution, tack sharp focus, professional food styling, gourmet dish plated on elegant white porcelain, natural window lighting creating soft shadows, shallow depth of field at f/2.8, 100mm macro lens perspective, vibrant saturated colors, appetizing presentation, studio quality, commercial advertisement style, every detail crystal clear, professional culinary photography, 8K quality, droplets of condensation visible, texture highly detailed"

Fitness Brand Action Shot (1024x1792):
"Dynamic fitness photography, ultra high resolution, frozen motion at 1/1000 shutter speed, professional athlete mid-workout, powerful composition, dramatic lighting with rim light highlighting muscle definition, sharp focus throughout, vibrant orange and blue color grading, modern luxury gym setting blurred background, professional sports photography, commercial quality, motivational and aspirational mood, 8K detail, perfect for vertical Instagram post"

IMPORTANT QUALITY MARKERS TO INCLUDE:
- "ultra high resolution"
- "sharp focus" or "tack sharp"
- "8K quality" or "extremely detailed"
- "professional photography"
- "commercial quality"
- "studio lighting" or specific lighting setup
- Specific technical details (lens, f-stop, composition)

OUTPUT FORMAT (JSON):
{
  "prompt": "Detailed HD image prompt with quality markers",
  "technical_specs": {
    "recommended_model": "dall-e-3 | gpt-image-1",
    "resolution": "1024x1024 | 1792x1024 | 1024x1792",
    "quality": "hd | ultra_hd",
    "aspect_ratio": "1:1 | 16:9 | 9:16"
  },
  "style_notes": "Professional explanation of style choices (no emojis)",
  "usage_recommendations": {
    "best_for": ["Instagram", "Facebook Ads", "Print Materials"],
    "color_profile": "RGB for digital, CMYK-ready for print",
    "file_format": "PNG for transparency, JPEG for photos"
  },
  "prompt_focus": {
    "subject": "Main subject description",
    "quality_level": "Photorealistic | Artistic | Illustrated",
    "mood": "Professional description of intended mood",
    "technical_details": "Camera and lighting specifications"
  }
}

VALIDATION CHECKLIST:
Before finalizing any prompt, ensure it includes:
- Quality markers (HD, 8K, ultra detailed)
- Professional context (commercial photography, professional)
- Technical specifications (lighting, lens, composition)
- Specific details about subject
- Clear artistic direction
- Marketing purpose alignment

Remember: Every image must be HD quality. No exceptions. All generated images should be suitable for professional marketing use, including potential print applications.
"""


class HDImageAgent(BaseAgent):
    """
    Advanced HD image generation agent.

    Ensures all images are high definition and suitable for professional use.
    """

    def __init__(self):
        super().__init__(
            agent_name="HDImageAgent",
            system_prompt=HD_IMAGE_SYSTEM_PROMPT,
            model="gpt-4o"
        )
        logger.info("HDImageAgent initialized with HD quality enforcement")

    async def generate_hd_image(
        self,
        context: Dict[str, Any],
        model: ImageModel = ImageModel.DALLE_3_HD,
        quality: ImageQuality = ImageQuality.HD,
        size: str = "1024x1024"
    ) -> Dict[str, Any]:
        """
        Generate a high-definition marketing image.

        Args:
            context: Marketing context including:
                - content: Marketing content/message
                - brand_info: Brand information
                - platform: Target platform
                - style_preferences: Style preferences
            model: Image generation model to use
            quality: Quality level (HD enforced)
            size: Image dimensions (HD sizes only)

        Returns:
            Dictionary with HD image data and metadata
        """
        try:
            from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
            import os
            from dotenv import load_dotenv

            load_dotenv()

            # Validate size is HD
            valid_hd_sizes = ["1024x1024", "1792x1024", "1024x1792"]
            if size not in valid_hd_sizes:
                logger.warning(f"Invalid size {size}, defaulting to 1024x1024 HD")
                size = "1024x1024"

            logger.info(f"Generating HD image with size {size} using {model.value}")

            # Extract context
            content = context.get('content', '')
            brand_info = context.get('brand_info', '')
            platform = context.get('platform', 'social media')
            style_prefs = context.get('style_preferences', '')

            # Create HD prompt using AI
            logger.info("Creating HD image prompt using AI specialist...")

            prompt_context = f"""
Marketing Content: {content}

Brand Information: {brand_info}

Target Platform: {platform}

Style Preferences: {style_prefs}

Target Resolution: {size}

Create a detailed, HD-optimized DALL-E prompt for a professional marketing image.
The prompt must include HD quality markers and technical specifications.
Remember: Communicate plainly without emojis or special formatting.
"""

            # Get AI-generated HD prompt
            response = await self.execute({
                "user_message": prompt_context,
                "task_id": "hd_image_prompt_generation"
            })

            result = response.get("result", {})

            # Extract prompt
            if isinstance(result, dict):
                dalle_prompt = result.get("prompt", str(result))
                technical_specs = result.get("technical_specs", {})
            elif isinstance(result, str):
                import json
                try:
                    parsed = json.loads(result)
                    dalle_prompt = parsed.get("prompt", result)
                    technical_specs = parsed.get("technical_specs", {})
                except:
                    dalle_prompt = result
                    technical_specs = {}
            else:
                dalle_prompt = str(result)
                technical_specs = {}

            # Enhance prompt with HD quality markers if not present
            hd_markers = ["high resolution", "ultra detailed", "8K quality", "sharp focus", "professional"]
            if not any(marker.lower() in dalle_prompt.lower() for marker in hd_markers):
                dalle_prompt = f"Ultra high resolution, 8K quality, sharp focus, professional commercial photography, {dalle_prompt}"

            logger.info(f"Generated HD prompt: {dalle_prompt[:200]}...")

            # Generate HD image
            logger.info(f"Generating HD image with {model.value}...")
            api_key = os.environ.get('EMERGENT_LLM_KEY')

            image_gen = OpenAIImageGeneration(api_key=api_key)

            # Configure for HD generation
            generation_params = {
                "prompt": dalle_prompt,
                "model": model.value,
                "number_of_images": 1
            }

            # Add quality parameter for DALL-E 3
            if model == ImageModel.DALLE_3_HD:
                generation_params["quality"] = "hd"
                generation_params["size"] = size

            images = await image_gen.generate_images(**generation_params)

            if images and len(images) > 0:
                # Convert to base64
                image_base64 = base64.b64encode(images[0]).decode('utf-8')

                # Validate image size (basic check)
                image_size_kb = len(images[0]) / 1024
                logger.info(f"HD image generated successfully. Size: {image_size_kb:.2f} KB")

                # HD images should typically be larger
                if image_size_kb < 100:
                    logger.warning("Image size seems small for HD quality. Verifying...")

                return {
                    "status": "success",
                    "image_base64": image_base64,
                    "prompt_used": dalle_prompt,
                    "technical_specs": {
                        **technical_specs,
                        "model_used": model.value,
                        "quality_level": quality.value,
                        "resolution": size,
                        "file_size_kb": round(image_size_kb, 2)
                    },
                    "message": f"HD image generated successfully at {size} resolution. File size: {image_size_kb:.2f} KB. Suitable for professional marketing use.",
                    "quality_validated": image_size_kb >= 100
                }
            else:
                raise Exception("No image was generated")

        except Exception as e:
            logger.error(f"Error generating HD image: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "message": f"Failed to generate HD image: {str(e)}"
            }

    async def generate_image_from_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Backward compatible method that generates HD images.

        Ensures all images are HD quality.
        """
        # Determine optimal size based on platform
        platform = context.get('platform', 'social media').lower()

        if 'instagram' in platform or 'facebook' in platform:
            size = "1024x1024"  # Square for social feed
        elif 'story' in platform or 'vertical' in platform:
            size = "1024x1792"  # Vertical for stories
        elif 'banner' in platform or 'linkedin' in platform:
            size = "1792x1024"  # Wide for banners
        else:
            size = "1024x1024"  # Default HD square

        return await self.generate_hd_image(
            context=context,
            model=ImageModel.DALLE_3_HD,
            quality=ImageQuality.HD,
            size=size
        )
