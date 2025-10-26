"""
Quick Test Script for Image and Video Generation
Run this to verify everything is working
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from agents.fixed_image_agent import FixedImageAgent
from agents.fixed_video_agent import FixedVideoAgent


async def test_image_generation():
    """Test image generation"""
    print("\n" + "="*60)
    print("TESTING IMAGE GENERATION")
    print("="*60)

    try:
        agent = FixedImageAgent()
        print("✓ Image agent initialized")

        print("\nGenerating test image...")
        result = await agent.generate_image_from_context({
            "content": "A modern coffee shop with cozy atmosphere",
            "brand_info": "Friendly, warm, welcoming",
            "platform": "Instagram"
        })

        if result.get("status") == "success":
            print("✓ IMAGE GENERATION SUCCESSFUL!")
            print(f"  Model: {result.get('model')}")
            print(f"  Size: {result.get('size')}")
            print(f"  Prompt: {result.get('prompt_used', '')[:100]}...")
            print(f"  Image data length: {len(result.get('image_base64', ''))} characters")
            return True
        else:
            print("✗ IMAGE GENERATION FAILED")
            print(f"  Error: {result.get('error')}")
            print(f"  Message: {result.get('message')}")
            return False

    except Exception as e:
        print(f"✗ EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_video_generation():
    """Test video generation"""
    print("\n" + "="*60)
    print("TESTING VIDEO GENERATION")
    print("="*60)

    try:
        agent = FixedVideoAgent()
        print("✓ Video agent initialized")

        print("\nGenerating test video concept...")
        result = await agent.generate_video_from_context({
            "content": "Product launch announcement for new smartphone",
            "brand_info": "Tech, innovative, modern",
            "platform": "Instagram Reels",
            "duration": 15
        })

        if result.get("status") in ["success", "concept_only"]:
            print("✓ VIDEO CONCEPT GENERATION SUCCESSFUL!")
            print(f"  Status: {result.get('status')}")
            print(f"  Duration: {result.get('duration')} seconds")

            video_concept = result.get("video_concept", {})
            if isinstance(video_concept, dict):
                scenes = video_concept.get("scenes", [])
                print(f"  Scenes: {len(scenes)}")

                if scenes:
                    print("\n  Scene breakdown:")
                    for scene in scenes[:3]:  # Show first 3 scenes
                        print(f"    Scene {scene.get('scene_number')}: {scene.get('description', '')[:60]}...")

            prompt = result.get("video_prompt", "")
            if prompt:
                print(f"\n  Video prompt: {prompt[:150]}...")

            print(f"\n  Note: {result.get('note', 'N/A')}")
            return True
        else:
            print("✗ VIDEO GENERATION FAILED")
            print(f"  Error: {result.get('error')}")
            print(f"  Message: {result.get('message')}")
            return False

    except Exception as e:
        print(f"✗ EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   IMAGE & VIDEO GENERATION TEST SUITE                     ║")
    print("╚════════════════════════════════════════════════════════════╝")

    # Check environment
    print("\nChecking environment...")
    openai_key = os.getenv('OPENAI_API_KEY')
    emergent_key = os.getenv('EMERGENT_LLM_KEY')

    if openai_key:
        print("✓ OPENAI_API_KEY found")
    elif emergent_key:
        print("✓ EMERGENT_LLM_KEY found")
    else:
        print("✗ No API key found!")
        print("  Please set OPENAI_API_KEY or EMERGENT_LLM_KEY in .env file")
        return

    # Run tests
    image_ok = await test_image_generation()
    video_ok = await test_video_generation()

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Image Generation: {'✓ PASS' if image_ok else '✗ FAIL'}")
    print(f"Video Generation: {'✓ PASS' if video_ok else '✗ FAIL'}")

    if image_ok and video_ok:
        print("\n✓ ALL TESTS PASSED!")
        print("\nYour image and video generation is working correctly.")
        print("You can now use these features in the application.")
    else:
        print("\n✗ SOME TESTS FAILED")
        print("\nPlease check:")
        print("1. API key is set correctly in .env")
        print("2. OpenAI SDK is installed: pip install --upgrade openai")
        print("3. You have credits in your OpenAI account")
        print("\nSee IMAGE_VIDEO_FIX_GUIDE.md for detailed troubleshooting")

    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
