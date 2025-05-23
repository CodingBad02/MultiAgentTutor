#!/usr/bin/env python3
"""
Deployment test script to verify the deployed application works correctly.
Usage: python deployment_test.py <your-deployed-url>
"""

import requests
import sys
import json
import time

def test_deployment(base_url):
    """Test the deployed multi-agent tutor system."""
    
    print(f"🧪 Testing deployment at: {base_url}")
    print("=" * 60)
    
    # Test 1: Health Check
    print("\n1️⃣ Testing Health Check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=30)
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: Root Endpoint
    print("\n2️⃣ Testing Root Endpoint...")
    try:
        response = requests.get(f"{base_url}/", timeout=30)
        if response.status_code == 200:
            print("✅ Root endpoint passed")
            data = response.json()
            print(f"   Version: {data.get('version', 'unknown')}")
            print(f"   Features: {len(data.get('features', []))}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
    
    # Test 3: Math Agent - Equation Solving
    print("\n3️⃣ Testing Math Agent (Equation Solving)...")
    try:
        payload = {"query": "Solve 2x + 5 = 15"}
        response = requests.post(
            f"{base_url}/ask", 
            json=payload, 
            timeout=60,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            print("✅ Math equation solving passed")
            print(f"   Agent: {data.get('agent_used', 'unknown')}")
            print(f"   Confidence: {data.get('confidence', 0)}")
            print(f"   Execution time: {data.get('execution_time_ms', 0):.0f}ms")
            
            # Check if tools were used
            if "equation_solver" in data.get('answer', '').lower():
                print("✅ Tool usage detected!")
            else:
                print("⚠️ Tool usage not clearly detected")
                
            print(f"   Answer preview: {data.get('answer', '')[:150]}...")
        else:
            print(f"❌ Math test failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Math test error: {e}")
    
    # Test 4: Physics Agent - Formula Lookup
    print("\n4️⃣ Testing Physics Agent (Formula Lookup)...")
    try:
        payload = {"query": "What is the formula for kinetic energy?"}
        response = requests.post(
            f"{base_url}/ask", 
            json=payload, 
            timeout=60,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            print("✅ Physics formula lookup passed")
            print(f"   Agent: {data.get('agent_used', 'unknown')}")
            print(f"   Confidence: {data.get('confidence', 0)}")
            print(f"   Execution time: {data.get('execution_time_ms', 0):.0f}ms")
            
            # Check if tools were used
            if "formula_lookup" in data.get('answer', '').lower():
                print("✅ Tool usage detected!")
            else:
                print("⚠️ Tool usage not clearly detected")
                
            print(f"   Answer preview: {data.get('answer', '')[:150]}...")
        else:
            print(f"❌ Physics test failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Physics test error: {e}")
    
    # Test 5: Agent Information
    print("\n5️⃣ Testing Agent Information...")
    try:
        response = requests.get(f"{base_url}/agents", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print("✅ Agent information passed")
            print(f"   Total agents: {data.get('total_agents', 0)}")
            print(f"   Routing method: {data.get('routing_method', 'unknown')}")
        else:
            print(f"❌ Agent info failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Agent info error: {e}")
    
    print("\n🏁 Deployment testing complete!")
    print("\n💡 Tips:")
    print("   - If tests fail, check your GEMINI_API_KEY environment variable")
    print("   - Check deployment logs for detailed error information")
    print("   - Ensure all dependencies are properly installed")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python deployment_test.py <your-deployed-url>")
        print("Example: python deployment_test.py https://your-app.railway.app")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    test_deployment(base_url) 