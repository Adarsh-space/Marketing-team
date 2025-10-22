from .base_agent import BaseAgent
from typing import Dict, Any, Optional
import base64
import logging
import os
from dotenv import load_dotenv
import httpx
import asyncio

load_dotenv()
logger = logging.getLogger(__name__)

VIDEO_GENERATION_SYSTEM_PROMPT = """You are an expert Video Generation Specialist for marketing content.

Create detailed, cinematic prompts for AI video generation that produce high-quality, engaging videos.

**YOUR TASK:**
When given marketing context, create a detailed prompt for video generation.

**OUTPUT FORMAT (JSON):**
{
  "prompt": "Detailed cinematic video prompt with camera movements, lighting, mood",
  "duration": 10,
  "resolution": "1080p",
  "style_notes": "Brief explanation of creative choices"
}
"""

class MultiModelVideoAgent(BaseAgent):
    """
    Agent responsible for generating videos using multiple AI models.
    Supports: OpenAI Sora, Runway Gen-3, Luma Dream Machine, Stability AI
    """
    
    def __init__(self):
        super().__init__(
            agent_name="MultiModelVideoAgent",
            system_prompt=VIDEO_GENERATION_SYSTEM_PROMPT,
            model="gpt-4o"
        )
        self.supported_models = {
            "sora": "OpenAI Sora (HD, up to 20s)",
            "runway-gen3": "Runway Gen-3 Alpha Turbo (720p/1080p, 5-10s)",
            "luma-dream": "Luma Dream Machine (1080p, up to 10s)",
            "stability": "Stability AI Stable Video (1024x576, ~2s)"
        }
    
    async def generate_video_from_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate video based on marketing context using Sora.
        
        Args:
            context: Dictionary containing:
                - content: Marketing content/description
                - brand_info: Brand information
                - platform: Target platform
                - duration: Video duration (default: 10 seconds)
                - resolution: Video resolution (default: 1080p)
        
        Returns:
            Dictionary with video_base64 and metadata
        """
        try:
            # Get marketing context
            content = context.get('content', '')
            brand_info = context.get('brand_info', '')
            duration = context.get('duration', 10)
            resolution = context.get('resolution', '1080p')
            
            # Create prompt using AI
            logger.info("Creating video prompt using AI...")
            prompt_context = f"""
Marketing Content: {content}
Brand Info: {brand_info}
Duration: {duration} seconds
Resolution: {resolution}

Create a detailed cinematic video prompt for professional marketing video.
"""
            
            # Get AI-generated prompt
            response = await self.execute({
                "user_message": prompt_context,
                "task_id": "video_prompt_generation"
            })
            
            result = response.get("result", {})
            
            # Extract prompt
            if isinstance(result, dict):
                video_prompt = result.get("prompt", str(result))
            elif isinstance(result, str):
                import json
                try:
                    parsed = json.loads(result)
                    video_prompt = parsed.get("prompt", result)
                except:
                    video_prompt = result
            else:
                video_prompt = str(result)
            
            logger.info(f"Generated video prompt: {video_prompt[:200]}...")
            
            # Try multiple video generation models in order of preference
            models_to_try = [
                ("sora", self._try_sora),
                ("runway-gen3", self._try_runway),
                ("luma-dream", self._try_luma),
                ("stability", self._try_stability)
            ]
            
            errors = []
            for model_name, model_func in models_to_try:
                try:
                    logger.info(f"Attempting video generation with {model_name}...")
                    result = await model_func(video_prompt, duration, resolution)
                    if result.get("status") == "success":
                        result["model_used"] = model_name
                        return result
                except Exception as e:
                    error_msg = f"{model_name}: {str(e)}"
                    errors.append(error_msg)
                    logger.warning(f"Failed to generate video with {model_name}: {str(e)}")
                    continue
            
            # All models failed - return concept
            logger.warning("All video generation models unavailable. Returning video concept.")
            return {
                "status": "concept_only",
                "video_concept": video_prompt,
                "duration": duration,
                "resolution": resolution,
                "message": "Video generation APIs not available. Here's the professional video concept you can use with any video generation tool.",
                "note": "Supported models: Sora, Runway Gen-3, Luma Dream Machine, Stability AI. All require API keys.",
                "errors": errors
            }
                
        except Exception as e:
            logger.error(f"Error generating video: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "message": f"Failed to generate video: {str(e)}"
            }
