#!/usr/bin/env python3
"""
Image Generation Testing for AI Marketing Platform
Tests the image generation functionality through the /api/chat endpoint
"""

import requests
import json
import base64
import time
from datetime import datetime

# Configuration
BASE_URL = "https://marketing-minds.preview.emergentagent.com/api"
TIMEOUT = 60  # Longer timeout for image generation

class ImageGenerationTester:
    def __init__(self):
        self.results = []
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        
    def log_result(self, test_name, status, message, details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,  # "PASS", "FAIL", "ERROR"
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        print(f"[{status}] {test_name}: {message}")
        if details:
            print(f"    Details: {details}")
    
    def is_valid_base64(self, data):
        """Check if string is valid base64"""
        try:
            if isinstance(data, str):
                # Check if it looks like base64
                if len(data) % 4 == 0 and data.replace('+', '').replace('/', '').replace('=', '').isalnum():
                    base64.b64decode(data)
                    return True
            return False
        except Exception:
            return False
    
    def test_image_generation_request(self):
        """Test image generation through chat endpoint"""
        print("\n=== Testing Image Generation via Chat Endpoint ===")
        
        try:
            # Test image generation request
            chat_data = {
                "message": "Generate an image of a modern tech startup office with open workspace, natural lighting, and innovative design elements",
                "user_id": "test_user_image"
            }
            
            print("Sending image generation request...")
            response = self.session.post(f"{BASE_URL}/chat", json=chat_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ["message", "conversation_id"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Image Generation Request", "FAIL", 
                                  f"Missing required fields: {missing_fields}", 
                                  {"response": data})
                    return None
                
                # Check if image was generated
                if "image_base64" in data and data["image_base64"]:
                    image_data = data["image_base64"]
                    
                    # Validate base64 image data
                    if self.is_valid_base64(image_data):
                        self.log_result("Image Generation Request", "PASS", 
                                      "Image generated successfully with valid base64 data", 
                                      {
                                          "conversation_id": data["conversation_id"],
                                          "image_size_bytes": len(image_data),
                                          "has_prompt": "prompt_used" in data,
                                          "prompt_used": data.get("prompt_used", "")[:100] + "..." if data.get("prompt_used") else None
                                      })
                        return data["conversation_id"]
                    else:
                        self.log_result("Image Generation Request", "FAIL", 
                                      "Image data is not valid base64", 
                                      {"image_data_preview": str(image_data)[:100]})
                        return None
                else:
                    # Check if it's a regular conversation response
                    if data.get("type") == "conversation":
                        self.log_result("Image Generation Request", "FAIL", 
                                      "No image generated - received conversation response instead", 
                                      {"response_message": data.get("message", "")})
                    else:
                        self.log_result("Image Generation Request", "FAIL", 
                                      "No image_base64 field in response or empty image data", 
                                      {"response": data})
                    return None
            else:
                self.log_result("Image Generation Request", "FAIL", 
                              f"HTTP error: {response.status_code}", 
                              {"response": response.text})
                return None
                
        except Exception as e:
            self.log_result("Image Generation Request", "ERROR", 
                          f"Request failed: {str(e)}")
            return None
    
    def test_regular_chat_functionality(self):
        """Test that regular chat still works without image requests"""
        print("\n=== Testing Regular Chat Functionality ===")
        
        try:
            chat_data = {
                "message": "Hello, I need help with marketing strategy for my business",
                "user_id": "test_user_regular"
            }
            
            response = self.session.post(f"{BASE_URL}/chat", json=chat_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                if "message" in data and "conversation_id" in data:
                    # Should NOT have image data for regular chat
                    if "image_base64" not in data or data.get("image_base64") is None:
                        self.log_result("Regular Chat", "PASS", 
                                      "Regular chat working correctly without image data", 
                                      {
                                          "conversation_id": data["conversation_id"],
                                          "response_type": data.get("type", "unknown"),
                                          "message_preview": data.get("message", "")[:100]
                                      })
                    else:
                        self.log_result("Regular Chat", "FAIL", 
                                      "Regular chat unexpectedly returned image data", 
                                      {"response": data})
                else:
                    self.log_result("Regular Chat", "FAIL", 
                                  "Regular chat missing required fields", 
                                  {"response": data})
            else:
                self.log_result("Regular Chat", "FAIL", 
                              f"Regular chat HTTP error: {response.status_code}", 
                              {"response": response.text})
                
        except Exception as e:
            self.log_result("Regular Chat", "ERROR", 
                          f"Regular chat request failed: {str(e)}")
    
    def test_multiple_image_requests(self):
        """Test multiple different image generation requests"""
        print("\n=== Testing Multiple Image Generation Requests ===")
        
        image_requests = [
            "Create an image of a professional business meeting",
            "Generate a picture of eco-friendly products for social media",
            "Make a visual for a fitness brand campaign",
            "Design a graphic for a food delivery app"
        ]
        
        successful_generations = 0
        
        for i, request in enumerate(image_requests):
            try:
                chat_data = {
                    "message": request,
                    "user_id": f"test_user_multi_{i}"
                }
                
                print(f"Testing request {i+1}: {request[:50]}...")
                response = self.session.post(f"{BASE_URL}/chat", json=chat_data)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "image_base64" in data and data["image_base64"] and self.is_valid_base64(data["image_base64"]):
                        successful_generations += 1
                        self.log_result(f"Multi-Image Test {i+1}", "PASS", 
                                      f"Image generated for: {request[:30]}...", 
                                      {
                                          "image_size": len(data["image_base64"]),
                                          "has_prompt": bool(data.get("prompt_used"))
                                      })
                    else:
                        self.log_result(f"Multi-Image Test {i+1}", "FAIL", 
                                      f"No valid image for: {request[:30]}...", 
                                      {"response": data})
                else:
                    self.log_result(f"Multi-Image Test {i+1}", "FAIL", 
                                  f"HTTP error for: {request[:30]}... - {response.status_code}")
                    
                # Small delay between requests
                time.sleep(2)
                
            except Exception as e:
                self.log_result(f"Multi-Image Test {i+1}", "ERROR", 
                              f"Error for: {request[:30]}... - {str(e)}")
        
        # Summary of multiple tests
        success_rate = (successful_generations / len(image_requests)) * 100
        if success_rate >= 75:
            self.log_result("Multi-Image Summary", "PASS", 
                          f"Multiple image generation successful: {successful_generations}/{len(image_requests)} ({success_rate:.1f}%)")
        else:
            self.log_result("Multi-Image Summary", "FAIL", 
                          f"Multiple image generation low success rate: {successful_generations}/{len(image_requests)} ({success_rate:.1f}%)")
    
    def test_conversation_flow_with_images(self):
        """Test conversation flow that includes image generation"""
        print("\n=== Testing Conversation Flow with Images ===")
        
        conversation_id = None
        
        try:
            # Step 1: Start conversation
            chat_data = {
                "message": "I'm launching a new sustainable fashion brand",
                "user_id": "test_user_flow"
            }
            
            response = self.session.post(f"{BASE_URL}/chat", json=chat_data)
            
            if response.status_code == 200:
                data = response.json()
                conversation_id = data.get("conversation_id")
                
                if conversation_id:
                    self.log_result("Conversation Flow Step 1", "PASS", 
                                  "Initial conversation started", 
                                  {"conversation_id": conversation_id})
                else:
                    self.log_result("Conversation Flow Step 1", "FAIL", 
                                  "No conversation_id returned")
                    return
            else:
                self.log_result("Conversation Flow Step 1", "FAIL", 
                              f"Initial conversation failed: {response.status_code}")
                return
            
            # Step 2: Request image in same conversation
            chat_data = {
                "message": "Generate an image for my sustainable fashion brand showing eco-friendly clothing",
                "conversation_id": conversation_id,
                "user_id": "test_user_flow"
            }
            
            response = self.session.post(f"{BASE_URL}/chat", json=chat_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Should maintain same conversation_id
                if data.get("conversation_id") == conversation_id:
                    if "image_base64" in data and data["image_base64"] and self.is_valid_base64(data["image_base64"]):
                        self.log_result("Conversation Flow Step 2", "PASS", 
                                      "Image generated within existing conversation", 
                                      {
                                          "conversation_maintained": True,
                                          "image_generated": True,
                                          "prompt_included": bool(data.get("prompt_used"))
                                      })
                    else:
                        self.log_result("Conversation Flow Step 2", "FAIL", 
                                      "No image generated in conversation flow", 
                                      {"response": data})
                else:
                    self.log_result("Conversation Flow Step 2", "FAIL", 
                                  "Conversation ID not maintained", 
                                  {
                                      "expected": conversation_id,
                                      "received": data.get("conversation_id")
                                  })
            else:
                self.log_result("Conversation Flow Step 2", "FAIL", 
                              f"Image request in conversation failed: {response.status_code}")
                
        except Exception as e:
            self.log_result("Conversation Flow", "ERROR", 
                          f"Conversation flow test failed: {str(e)}")
    
    def run_all_tests(self):
        """Run all image generation tests"""
        print("Starting Image Generation Testing...")
        print(f"Base URL: {BASE_URL}")
        print(f"Timeout: {TIMEOUT}s")
        
        # Run all test suites
        self.test_image_generation_request()
        self.test_regular_chat_functionality()
        self.test_multiple_image_requests()
        self.test_conversation_flow_with_images()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "="*80)
        print("IMAGE GENERATION TESTING SUMMARY")
        print("="*80)
        
        total_tests = len(self.results)
        passed = len([r for r in self.results if r["status"] == "PASS"])
        failed = len([r for r in self.results if r["status"] == "FAIL"])
        errors = len([r for r in self.results if r["status"] == "ERROR"])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Errors: {errors}")
        print(f"Success Rate: {(passed/total_tests)*100:.1f}%")
        
        print("\n--- FAILED TESTS ---")
        for result in self.results:
            if result["status"] == "FAIL":
                print(f"❌ {result['test']}: {result['message']}")
        
        print("\n--- ERROR TESTS ---")
        for result in self.results:
            if result["status"] == "ERROR":
                print(f"🔥 {result['test']}: {result['message']}")
        
        print("\n--- PASSED TESTS ---")
        for result in self.results:
            if result["status"] == "PASS":
                print(f"✅ {result['test']}: {result['message']}")
        
        # Save detailed results to file
        with open('/app/image_generation_test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nDetailed results saved to: /app/image_generation_test_results.json")

if __name__ == "__main__":
    tester = ImageGenerationTester()
    tester.run_all_tests()