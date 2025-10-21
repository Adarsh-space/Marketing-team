#!/usr/bin/env python3
"""
Verify Image Generation Response Fields
Tests the specific fields mentioned in the review request
"""

import requests
import json
import base64

BASE_URL = "https://marketing-minds.preview.emergentagent.com/api"

def test_image_response_fields():
    """Test that image generation response contains all required fields"""
    
    print("Testing image generation response fields...")
    
    # Send image generation request
    chat_data = {
        "message": "Generate an image of a modern tech startup office",
        "user_id": "field_test_user"
    }
    
    response = requests.post(f"{BASE_URL}/chat", json=chat_data, timeout=60)
    
    if response.status_code == 200:
        data = response.json()
        
        print("Response received:")
        print(json.dumps(data, indent=2))
        
        # Check required fields
        required_fields = {
            "message": "text response",
            "image_base64": "base64 encoded PNG image data", 
            "prompt_used": "the DALL-E prompt",
            "conversation_id": "conversation identifier"
        }
        
        print("\nField verification:")
        all_present = True
        
        for field, description in required_fields.items():
            if field in data and data[field]:
                print(f"✅ {field}: Present ({description})")
                
                # Additional validation for specific fields
                if field == "image_base64":
                    try:
                        # Verify it's valid base64
                        decoded = base64.b64decode(data[field])
                        print(f"   - Valid base64 data: {len(decoded)} bytes")
                        
                        # Check if it starts with PNG header
                        if decoded.startswith(b'\x89PNG'):
                            print(f"   - Valid PNG image format")
                        else:
                            print(f"   - Warning: Not PNG format (starts with {decoded[:8]})")
                    except Exception as e:
                        print(f"   - Error: Invalid base64 data: {e}")
                        all_present = False
                        
                elif field == "prompt_used":
                    print(f"   - Prompt length: {len(data[field])} characters")
                    print(f"   - Prompt preview: {data[field][:100]}...")
                    
            else:
                print(f"❌ {field}: Missing or empty ({description})")
                all_present = False
        
        # Check image data size
        if "image_base64" in data and data["image_base64"]:
            image_size = len(data["image_base64"])
            print(f"\nImage data analysis:")
            print(f"- Base64 string length: {image_size:,} characters")
            print(f"- Estimated image size: {(image_size * 3 / 4):,.0f} bytes")
            
            if image_size > 100000:  # Reasonable size for an image
                print(f"✅ Image size appears reasonable")
            else:
                print(f"⚠️  Image size seems small, may not be a real image")
        
        print(f"\nOverall result: {'✅ ALL FIELDS PRESENT' if all_present else '❌ MISSING FIELDS'}")
        return all_present
        
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        print(f"Response: {response.text}")
        return False

if __name__ == "__main__":
    test_image_response_fields()