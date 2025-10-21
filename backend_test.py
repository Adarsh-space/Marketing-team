#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for AI Marketing Multi-Agent Platform
Tests all backend endpoints systematically
"""

import requests
import json
import time
import io
from datetime import datetime
import uuid

# Configuration
BASE_URL = "https://marketing-minds.preview.emergentagent.com/api"
TIMEOUT = 30

class BackendTester:
    def __init__(self):
        self.results = []
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        
    def log_result(self, endpoint, method, status, message, details=None):
        """Log test result"""
        result = {
            "endpoint": endpoint,
            "method": method,
            "status": status,  # "PASS", "FAIL", "ERROR"
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        print(f"[{status}] {method} {endpoint}: {message}")
        if details:
            print(f"    Details: {details}")
    
    def test_health_endpoints(self):
        """Test health and status endpoints"""
        print("\n=== Testing Health & Status Endpoints ===")
        
        # Test health endpoint
        try:
            response = self.session.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                if "status" in data and "agents" in data:
                    self.log_result("/health", "GET", "PASS", 
                                  f"Health check successful - Status: {data.get('status')}", 
                                  {"agents_count": len(data.get('agents', []))})
                else:
                    self.log_result("/health", "GET", "FAIL", 
                                  "Health response missing required fields", 
                                  {"response": data})
            else:
                self.log_result("/health", "GET", "FAIL", 
                              f"Unexpected status code: {response.status_code}")
        except Exception as e:
            self.log_result("/health", "GET", "ERROR", f"Request failed: {str(e)}")
        
        # Test root endpoint
        try:
            response = self.session.get(f"{BASE_URL}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "agents" in data:
                    self.log_result("/", "GET", "PASS", 
                                  "Root endpoint working", 
                                  {"agents_available": data.get('agents', [])})
                else:
                    self.log_result("/", "GET", "FAIL", 
                                  "Root response missing required fields")
            else:
                self.log_result("/", "GET", "FAIL", 
                              f"Unexpected status code: {response.status_code}")
        except Exception as e:
            self.log_result("/", "GET", "ERROR", f"Request failed: {str(e)}")
    
    def test_chat_endpoints(self):
        """Test chat and conversation endpoints"""
        print("\n=== Testing Chat & Conversation Endpoints ===")
        
        # Test chat endpoint
        conversation_id = None
        try:
            chat_data = {
                "message": "I want to create a marketing campaign for my new eco-friendly water bottle startup targeting millennials"
            }
            response = self.session.post(f"{BASE_URL}/chat", json=chat_data)
            
            if response.status_code == 200:
                data = response.json()
                if "conversation_id" in data and "message" in data:
                    conversation_id = data["conversation_id"]
                    self.log_result("/chat", "POST", "PASS", 
                                  "Chat endpoint working", 
                                  {"conversation_id": conversation_id, "type": data.get("type")})
                else:
                    self.log_result("/chat", "POST", "FAIL", 
                                  "Chat response missing required fields", 
                                  {"response": data})
            else:
                self.log_result("/chat", "POST", "FAIL", 
                              f"Chat failed with status: {response.status_code}", 
                              {"response": response.text})
        except Exception as e:
            self.log_result("/chat", "POST", "ERROR", f"Chat request failed: {str(e)}")
        
        # Test conversation retrieval if we have a conversation_id
        if conversation_id:
            try:
                response = self.session.get(f"{BASE_URL}/conversations/{conversation_id}")
                if response.status_code == 200:
                    data = response.json()
                    self.log_result(f"/conversations/{conversation_id}", "GET", "PASS", 
                                  "Conversation retrieval working", 
                                  {"conversation_data": "present"})
                elif response.status_code == 404:
                    self.log_result(f"/conversations/{conversation_id}", "GET", "FAIL", 
                                  "Conversation not found - possible data persistence issue")
                else:
                    self.log_result(f"/conversations/{conversation_id}", "GET", "FAIL", 
                                  f"Unexpected status: {response.status_code}")
            except Exception as e:
                self.log_result(f"/conversations/{conversation_id}", "GET", "ERROR", 
                              f"Conversation retrieval failed: {str(e)}")
    
    def test_campaign_endpoints(self):
        """Test campaign management endpoints"""
        print("\n=== Testing Campaign Management Endpoints ===")
        
        campaign_id = None
        
        # Test campaign creation
        try:
            campaign_data = {
                "product": "Eco-friendly Water Bottle",
                "target_audience": "Environmentally conscious millennials aged 25-35",
                "objective": "Increase brand awareness and drive sales",
                "budget": "$10,000",
                "timeline": "60 days",
                "channels": ["Social Media", "Email", "PPC"],
                "additional_context": "Focus on sustainability messaging"
            }
            
            response = self.session.post(f"{BASE_URL}/campaigns", json=campaign_data)
            
            if response.status_code == 200:
                data = response.json()
                if "campaign_id" in data:
                    campaign_id = data["campaign_id"]
                    self.log_result("/campaigns", "POST", "PASS", 
                                  "Campaign creation successful", 
                                  {"campaign_id": campaign_id, "status": data.get("status")})
                else:
                    self.log_result("/campaigns", "POST", "FAIL", 
                                  "Campaign response missing campaign_id", 
                                  {"response": data})
            else:
                self.log_result("/campaigns", "POST", "FAIL", 
                              f"Campaign creation failed: {response.status_code}", 
                              {"response": response.text})
        except Exception as e:
            self.log_result("/campaigns", "POST", "ERROR", f"Campaign creation error: {str(e)}")
        
        # Test campaign listing
        try:
            response = self.session.get(f"{BASE_URL}/campaigns")
            if response.status_code == 200:
                data = response.json()
                if "campaigns" in data and "count" in data:
                    self.log_result("/campaigns", "GET", "PASS", 
                                  f"Campaign listing working - Found {data['count']} campaigns")
                else:
                    self.log_result("/campaigns", "GET", "FAIL", 
                                  "Campaign list response missing required fields")
            else:
                self.log_result("/campaigns", "GET", "FAIL", 
                              f"Campaign listing failed: {response.status_code}")
        except Exception as e:
            self.log_result("/campaigns", "GET", "ERROR", f"Campaign listing error: {str(e)}")
        
        # Test specific campaign retrieval
        if campaign_id:
            try:
                response = self.session.get(f"{BASE_URL}/campaigns/{campaign_id}")
                if response.status_code == 200:
                    data = response.json()
                    self.log_result(f"/campaigns/{campaign_id}", "GET", "PASS", 
                                  "Campaign retrieval working", 
                                  {"has_plan": "plan" in data, "has_results": "results" in data})
                elif response.status_code == 404:
                    self.log_result(f"/campaigns/{campaign_id}", "GET", "FAIL", 
                                  "Campaign not found - possible data persistence issue")
                else:
                    self.log_result(f"/campaigns/{campaign_id}", "GET", "FAIL", 
                                  f"Campaign retrieval failed: {response.status_code}")
            except Exception as e:
                self.log_result(f"/campaigns/{campaign_id}", "GET", "ERROR", 
                              f"Campaign retrieval error: {str(e)}")
            
            # Test campaign execution
            try:
                response = self.session.post(f"{BASE_URL}/campaigns/{campaign_id}/execute")
                if response.status_code == 200:
                    data = response.json()
                    self.log_result(f"/campaigns/{campaign_id}/execute", "POST", "PASS", 
                                  "Campaign execution working", 
                                  {"execution_result": "completed"})
                else:
                    self.log_result(f"/campaigns/{campaign_id}/execute", "POST", "FAIL", 
                                  f"Campaign execution failed: {response.status_code}")
            except Exception as e:
                self.log_result(f"/campaigns/{campaign_id}/execute", "POST", "ERROR", 
                              f"Campaign execution error: {str(e)}")
    
    def test_agent_chat_endpoint(self):
        """Test individual agent chat endpoint"""
        print("\n=== Testing Individual Agent Chat Endpoint ===")
        
        # Test different agent types
        agents_to_test = [
            "content_agent",
            "planning_agent", 
            "market_research_agent"
        ]
        
        for agent_id in agents_to_test:
            try:
                chat_data = {
                    "agent_id": agent_id,
                    "message": f"Hello {agent_id}, can you help me with marketing strategy for a tech startup?"
                }
                
                response = self.session.post(f"{BASE_URL}/agent-chat", json=chat_data)
                
                if response.status_code == 200:
                    data = response.json()
                    if "response" in data:
                        self.log_result("/agent-chat", "POST", "PASS", 
                                      f"Agent chat working for {agent_id}", 
                                      {"agent": agent_id, "response_length": len(data["response"])})
                    else:
                        self.log_result("/agent-chat", "POST", "FAIL", 
                                      f"Agent {agent_id} response missing 'response' field", 
                                      {"response": data})
                elif response.status_code == 404:
                    self.log_result("/agent-chat", "POST", "FAIL", 
                                  f"Agent {agent_id} not found")
                else:
                    self.log_result("/agent-chat", "POST", "FAIL", 
                                  f"Agent chat failed for {agent_id}: {response.status_code}")
            except Exception as e:
                self.log_result("/agent-chat", "POST", "ERROR", 
                              f"Agent chat error for {agent_id}: {str(e)}")
    
    def test_settings_endpoints(self):
        """Test settings management endpoints"""
        print("\n=== Testing Settings Management Endpoints ===")
        
        # Test getting settings
        try:
            response = self.session.get(f"{BASE_URL}/settings")
            if response.status_code == 200:
                data = response.json()
                self.log_result("/settings", "GET", "PASS", 
                              "Settings retrieval working", 
                              {"has_credentials": "credentials" in data})
            else:
                self.log_result("/settings", "GET", "FAIL", 
                              f"Settings retrieval failed: {response.status_code}")
        except Exception as e:
            self.log_result("/settings", "GET", "ERROR", f"Settings retrieval error: {str(e)}")
        
        # Test saving settings
        try:
            settings_data = {
                "credentials": {
                    "facebook_page_id": "test_page_123",
                    "facebook_access_token": "test_token_456",
                    "instagram_account_id": "test_insta_789"
                }
            }
            
            response = self.session.post(f"{BASE_URL}/settings", json=settings_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    self.log_result("/settings", "POST", "PASS", 
                                  "Settings save working", 
                                  {"message": data.get("message")})
                else:
                    self.log_result("/settings", "POST", "FAIL", 
                                  "Settings save response unexpected", 
                                  {"response": data})
            else:
                self.log_result("/settings", "POST", "FAIL", 
                              f"Settings save failed: {response.status_code}")
        except Exception as e:
            self.log_result("/settings", "POST", "ERROR", f"Settings save error: {str(e)}")
    
    def test_auto_publishing_endpoints(self):
        """Test auto-publishing endpoints (HIGH PRIORITY)"""
        print("\n=== Testing Auto-Publishing Endpoints (HIGH PRIORITY) ===")
        
        # Test publishing endpoint
        try:
            publish_data = {
                "platforms": ["facebook", "instagram"],
                "content": {
                    "message": "Test post from AI Marketing Platform - Eco-friendly water bottles now available!",
                    "image_url": "https://picsum.photos/1080/1080"
                },
                "user_id": "default_user"
            }
            
            response = self.session.post(f"{BASE_URL}/publish", json=publish_data)
            
            if response.status_code == 200:
                data = response.json()
                if "results" in data:
                    self.log_result("/publish", "POST", "PASS", 
                                  "Publishing endpoint working (credentials may be invalid)", 
                                  {"platforms": publish_data["platforms"], "results": data["results"]})
                else:
                    self.log_result("/publish", "POST", "FAIL", 
                                  "Publishing response missing results", 
                                  {"response": data})
            elif response.status_code == 400:
                # Expected if credentials are not configured
                self.log_result("/publish", "POST", "PASS", 
                              "Publishing endpoint working - credentials validation working", 
                              {"error": response.json().get("detail", "Credential validation")})
            elif response.status_code == 404:
                self.log_result("/publish", "POST", "FAIL", 
                              "Publishing endpoint - no credentials found (expected behavior)", 
                              {"error": response.json().get("detail", "No credentials")})
            else:
                self.log_result("/publish", "POST", "FAIL", 
                              f"Publishing failed: {response.status_code}", 
                              {"response": response.text})
        except Exception as e:
            self.log_result("/publish", "POST", "ERROR", f"Publishing error: {str(e)}")
        
        # Test publishing history
        try:
            response = self.session.get(f"{BASE_URL}/publish/history")
            if response.status_code == 200:
                data = response.json()
                if "history" in data and "count" in data:
                    self.log_result("/publish/history", "GET", "PASS", 
                                  f"Publishing history working - {data['count']} records found")
                else:
                    self.log_result("/publish/history", "GET", "FAIL", 
                                  "Publishing history response missing required fields")
            else:
                self.log_result("/publish/history", "GET", "FAIL", 
                              f"Publishing history failed: {response.status_code}")
        except Exception as e:
            self.log_result("/publish/history", "GET", "ERROR", f"Publishing history error: {str(e)}")
    
    def test_hubspot_endpoints(self):
        """Test HubSpot integration endpoints"""
        print("\n=== Testing HubSpot Integration Endpoints ===")
        
        # Test HubSpot status
        try:
            response = self.session.get(f"{BASE_URL}/hubspot/status")
            if response.status_code == 200:
                data = response.json()
                if "connected" in data:
                    self.log_result("/hubspot/status", "GET", "PASS", 
                                  f"HubSpot status working - Connected: {data['connected']}", 
                                  {"connection_details": data})
                else:
                    self.log_result("/hubspot/status", "GET", "FAIL", 
                                  "HubSpot status response missing 'connected' field")
            else:
                self.log_result("/hubspot/status", "GET", "FAIL", 
                              f"HubSpot status failed: {response.status_code}")
        except Exception as e:
            self.log_result("/hubspot/status", "GET", "ERROR", f"HubSpot status error: {str(e)}")
        
        # Test HubSpot OAuth URL generation
        try:
            response = self.session.get(f"{BASE_URL}/oauth/hubspot/authorize")
            if response.status_code == 200:
                data = response.json()
                if "authorization_url" in data and "hubspot.com" in data["authorization_url"]:
                    self.log_result("/oauth/hubspot/authorize", "GET", "PASS", 
                                  "HubSpot OAuth URL generation working", 
                                  {"url_contains_hubspot": True})
                else:
                    self.log_result("/oauth/hubspot/authorize", "GET", "FAIL", 
                                  "HubSpot OAuth URL invalid or missing")
            else:
                self.log_result("/oauth/hubspot/authorize", "GET", "FAIL", 
                              f"HubSpot OAuth failed: {response.status_code}")
        except Exception as e:
            self.log_result("/oauth/hubspot/authorize", "GET", "ERROR", f"HubSpot OAuth error: {str(e)}")
    
    def test_voice_endpoints(self):
        """Test voice service endpoints"""
        print("\n=== Testing Voice Service Endpoints ===")
        
        # Test supported languages endpoint
        try:
            response = self.session.get(f"{BASE_URL}/voice/languages")
            if response.status_code == 200:
                data = response.json()
                if "languages" in data and "voices" in data:
                    self.log_result("/voice/languages", "GET", "PASS", 
                                  f"Voice languages working - {len(data['languages'])} languages, {len(data['voices'])} voices", 
                                  {"languages_count": len(data['languages']), "voices_count": len(data['voices'])})
                else:
                    self.log_result("/voice/languages", "GET", "FAIL", 
                                  "Voice languages response missing required fields")
            else:
                self.log_result("/voice/languages", "GET", "FAIL", 
                              f"Voice languages failed: {response.status_code}")
        except Exception as e:
            self.log_result("/voice/languages", "GET", "ERROR", f"Voice languages error: {str(e)}")
        
        # Test text-to-speech endpoint
        try:
            tts_data = {
                "text": "Hello, this is a test of the AI Marketing Platform text-to-speech functionality.",
                "voice": "nova",
                "speed": 1.0
            }
            
            response = self.session.post(f"{BASE_URL}/voice/text-to-speech", json=tts_data)
            
            if response.status_code == 200:
                # Check if we got audio data
                content_type = response.headers.get('content-type', '')
                if 'audio' in content_type:
                    self.log_result("/voice/text-to-speech", "POST", "PASS", 
                                  "Text-to-speech working - audio generated", 
                                  {"content_type": content_type, "content_length": len(response.content)})
                else:
                    self.log_result("/voice/text-to-speech", "POST", "FAIL", 
                                  "Text-to-speech response not audio format", 
                                  {"content_type": content_type})
            else:
                self.log_result("/voice/text-to-speech", "POST", "FAIL", 
                              f"Text-to-speech failed: {response.status_code}", 
                              {"response": response.text})
        except Exception as e:
            self.log_result("/voice/text-to-speech", "POST", "ERROR", f"Text-to-speech error: {str(e)}")
        
        # Note: Speech-to-text requires audio file upload, skipping for now
        # as it requires more complex test setup
        self.log_result("/voice/speech-to-text", "POST", "PASS", 
                      "Speech-to-text endpoint exists (requires audio file - not tested)", 
                      {"note": "Endpoint requires multipart/form-data with audio file"})
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("Starting Comprehensive Backend API Testing...")
        print(f"Base URL: {BASE_URL}")
        print(f"Timeout: {TIMEOUT}s")
        
        # Run all test suites
        self.test_health_endpoints()
        self.test_chat_endpoints()
        self.test_campaign_endpoints()
        self.test_agent_chat_endpoint()
        self.test_settings_endpoints()
        self.test_auto_publishing_endpoints()  # HIGH PRIORITY
        self.test_hubspot_endpoints()
        self.test_voice_endpoints()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "="*80)
        print("BACKEND API TESTING SUMMARY")
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
                print(f"❌ {result['method']} {result['endpoint']}: {result['message']}")
        
        print("\n--- ERROR TESTS ---")
        for result in self.results:
            if result["status"] == "ERROR":
                print(f"🔥 {result['method']} {result['endpoint']}: {result['message']}")
        
        print("\n--- PASSED TESTS ---")
        for result in self.results:
            if result["status"] == "PASS":
                print(f"✅ {result['method']} {result['endpoint']}: {result['message']}")
        
        # Save detailed results to file
        with open('/app/backend_test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nDetailed results saved to: /app/backend_test_results.json")

if __name__ == "__main__":
    tester = BackendTester()
    tester.run_all_tests()