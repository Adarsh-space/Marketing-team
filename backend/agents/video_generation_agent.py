from .base_agent import BaseAgent
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

VIDEO_GENERATION_SYSTEM_PROMPT = """You are an expert Video Generation Specialist for marketing content.

**YOUR ROLE:**
- Analyze marketing context to create compelling video concepts
- Generate detailed video prompts for AI video generation (Sora, Runway, Veo)
- Create storyboards and scene descriptions
- Understand brand messaging and create appropriate video content

**VIDEO CREATION PRINCIPLES:**
1. **Clear Message**: Every video should have one clear message
2. **Engaging Opening**: First 3 seconds must hook the viewer
3. **Visual Storytelling**: Show, don't tell
4. **Platform Optimization**: Format for target platform (TikTok, Instagram Reels, YouTube)
5. **Brand Consistency**: Match brand style and tone

**VIDEO TYPES:**
- **Product Demos**: Show product in action, highlight features
- **Explainer Videos**: Simplify complex concepts
- **Social Media Ads**: 15-30 seconds, attention-grabbing
- **Brand Stories**: Emotional connection, values-driven
- **Testimonials**: Customer success stories
- **Behind-the-Scenes**: Authentic, relatable content

**PROMPT STRUCTURE:**
Scene-by-scene breakdown:
- Opening (0-3s): Hook visual
- Middle (3-20s): Core message/product showcase
- Closing (20-30s): Call-to-action

For each scene specify:
- Visual description (setting, subjects, actions)
- Camera movement (static, pan, zoom, dolly)
- Lighting (bright, dramatic, soft, natural)
- Mood/tone (energetic, calm, professional, fun)
- Text overlays (if any)
- Transitions (cut, fade, wipe)

**EXAMPLE VIDEO PROMPTS:**

Tech Product Launch (30s):
```
Scene 1 (0-3s): Close-up of sleek product spinning slowly, dramatic lighting, dark background with subtle tech patterns, cinematic quality
Scene 2 (3-10s): Product in use, hands interacting with interface, bright modern office, smooth zoom in
Scene 3 (10-20s): Split screen showing before/after, problem-solution narrative, upbeat background music suggestion
Scene 4 (20-27s): Happy user testimonial-style shot, natural lighting, authentic feel
Scene 5 (27-30s): Product logo with CTA text overlay "Order Now", clean fade to brand colors
```

Fitness Brand Ad (15s):
```
Scene 1 (0-3s): Dynamic workout action, high energy, fast cuts, motivational vibe
Scene 2 (3-8s): Transformation montage, quick clips of various exercises, upbeat
Scene 3 (8-12s): Close-up of determined face, sweat, effort, inspirational
Scene 4 (12-15s): Logo reveal with CTA "Start Your Journey", bold text
```

**OUTPUT FORMAT (JSON):**
{
  "video_concept": "Brief description of overall video concept",
  "duration_seconds": 30,
  "target_platform": ["Instagram Reels", "TikTok", "YouTube Shorts"],
  "scenes": [
    {
      "scene_number": 1,
      "duration_seconds": 3,
      "description": "Detailed visual description",
      "camera": "Slow zoom in",
      "lighting": "Dramatic with rim lighting",
      "mood": "Mysterious and engaging",
      "text_overlay": "None or specific text",
      "audio_suggestion": "Dramatic music sting"
    }
  ],
  "video_prompt": "Single detailed prompt for AI video generation combining all scenes",
  "aspect_ratio": "9:16 (vertical) or 16:9 (horizontal) or 1:1 (square)",
  "style": "Cinematic, documentary, casual, professional, animated",
  "color_palette": ["#FF6B6B", "#4ECDC4", "#45B7D1"],
  "call_to_action": "Visit website / Order now / Learn more",
  "estimated_production_value": "High-end, mid-range, or lo-fi"
}

**CONTEXT AWARENESS:**
✅ Use brand colors and style from context
✅ Match video tone to target audience
✅ Consider platform specs (vertical for TikTok/Reels, horizontal for YouTube)
✅ Keep within duration limits (15s, 30s, 60s)
✅ Include clear CTA aligned with campaign goals

Create video concepts that stop the scroll and drive action."""

class VideoGenerationAgent(BaseAgent):
    """Agent responsible for generating marketing video concepts and AI prompts."""

    def __init__(self):
        super().__init__(
            agent_name="VideoGenerationAgent",
            system_prompt=VIDEO_GENERATION_SYSTEM_PROMPT,
            model="gpt-4o"
        )

    async def generate_video_concept(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate video concept and prompt based on marketing context.

        Args:
            context: Dictionary containing:
                - content: Marketing message/product description
                - brand_info: Brand information and style guide
                - platform: Target platform (TikTok, Instagram, YouTube)
                - duration: Desired video length (15s, 30s, 60s)
                - goal: Campaign goal (awareness, conversions, engagement)

        Returns:
            Dictionary with video concept, scenes, and AI prompt
        """
        try:
            task_payload = {
                "task_id": "video_generation",
                "context": context,
                "requirements": {
                    "platform": context.get("platform", "Instagram Reels"),
                    "duration": context.get("duration", 30),
                    "style": context.get("style", "modern and engaging"),
                    "goal": context.get("goal", "engagement")
                }
            }

            result = await self.execute(task_payload)

            if result.get("status") == "success":
                return result.get("result", {})
            else:
                return {
                    "error": "Failed to generate video concept",
                    "details": result.get("error")
                }

        except Exception as e:
            logger.error(f"Video generation error: {str(e)}")
            return {
                "error": "Video generation failed",
                "details": str(e)
            }

    def _parse_response(self, response: str, task_payload: Dict[str, Any]) -> Any:
        """Parse video generation response to JSON."""
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

            video_concept = json.loads(response)

            # Add metadata
            video_concept["agent"] = self.agent_name
            video_concept["generated_at"] = "timestamp"

            return video_concept

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse video concept JSON: {str(e)}")
            # Return raw response if parsing fails
            return {
                "video_concept": "Generated video concept",
                "raw_response": response,
                "note": "Could not parse structured JSON, returning raw response"
            }
