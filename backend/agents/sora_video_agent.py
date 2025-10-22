from .base_agent import BaseAgent
from typing import Dict, Any
import base64
import logging
import os
from dotenv import load_dotenv

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

class SoraVideoAgent(BaseAgent):
    """Agent responsible for generating videos using OpenAI Sora."""
    
    def __init__(self):
        super().__init__(
            agent_name="SoraVideoAgent",
            system_prompt=VIDEO_GENERATION_SYSTEM_PROMPT,
            model="gpt-4o"
        )
    
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
            
            # Check if Sora is available
            try:
                from emergentintegrations.llm.openai.video_generation import OpenAIVideoGeneration
                
                api_key = os.environ.get('EMERGENT_LLM_KEY')
                
                # Generate video using Sora
                logger.info("Generating video with Sora...")
                video_gen = OpenAIVideoGeneration(api_key=api_key)
                
                # Generate video (this will use Sora when available)
                videos = await video_gen.generate_video(
                    prompt=video_prompt,
                    model="sora-2",
                    duration=duration,
                    resolution=resolution
                )
                
                if videos and len(videos) > 0:
                    # Convert to base64
                    video_base64 = base64.b64encode(videos[0]).decode('utf-8')
                    
                    logger.info("Video generated successfully!")
                    
                    return {
                        "status": "success",
                        "video_base64": video_base64,
                        "prompt_used": video_prompt,
                        "duration": duration,
                        "resolution": resolution,
                        "message": "Video generated successfully!"
                    }
                else:
                    raise Exception("No video was generated")
                    
            except ImportError:
                # Sora not available yet - return video concept
                logger.warning("Sora API not available. Returning video concept only.")
                return {
                    "status": "concept_only",
                    "video_concept": video_prompt,
                    "duration": duration,
                    "resolution": resolution,
                    "message": "Sora API not available yet. Here's the video concept you can use with other video generation tools.",
                    "note": "To actually generate videos, Sora API access is required"
                }
                
        except Exception as e:
            logger.error(f"Error generating video: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "message": f"Failed to generate video: {str(e)}"
            }
