#!/usr/bin/env python3
"""
Debug specific backend issues
"""

import requests
import json

BASE_URL = "https://voiceagents-1.preview.emergentagent.com/api"

def test_agent_names():
    """Test to see what agent names are available"""
    print("=== Testing Agent Names ===")
    
    # Get health check to see available agents
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        data = response.json()
        print("Available agents:", data.get('agents', []))
        
        # Test with correct agent names
        for agent_name in data.get('agents', []):
            try:
                chat_data = {
                    "agent_id": agent_name,
                    "message": "Hello, can you help me?"
                }
                
                response = requests.post(f"{BASE_URL}/agent-chat", json=chat_data)
                print(f"Agent {agent_name}: Status {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"  Response: {result.get('response', 'No response')[:100]}...")
                else:
                    print(f"  Error: {response.text}")
            except Exception as e:
                print(f"  Exception: {str(e)}")

def test_campaign_creation_simple():
    """Test campaign creation with minimal data"""
    print("\n=== Testing Campaign Creation (Simple) ===")
    
    try:
        # Try with minimal data first
        campaign_data = {
            "product": "Test Product",
            "target_audience": "Test Audience", 
            "objective": "Test Objective"
        }
        
        response = requests.post(f"{BASE_URL}/campaigns", json=campaign_data)
        print(f"Campaign creation status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Campaign created: {data.get('campaign_id')}")
        else:
            print(f"Campaign creation failed: {response.text}")
            
    except Exception as e:
        print(f"Campaign creation exception: {str(e)}")

if __name__ == "__main__":
    test_agent_names()
    test_campaign_creation_simple()