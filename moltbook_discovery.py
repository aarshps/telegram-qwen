#!/usr/bin/env python3
"""
Moltbook API Discovery Script
Tests different endpoint patterns to find the correct API structure.
"""

import httpx
import json

API_KEY = "moltbook_sk_3LqlCw3WwauNQmUzWKdlKZ9XpAdoK1XN"
BASE_URL = "https://www.moltbook.com/api/v1"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def test_endpoint(client, method, endpoint, data=None):
    """Test a single endpoint."""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = client.get(url, timeout=15.0)
        elif method == "POST":
            response = client.post(url, json=data, timeout=15.0)
        else:
            return None
        
        result = {
            "endpoint": endpoint,
            "method": method,
            "status": response.status_code,
            "response": None
        }
        
        try:
            result["response"] = response.json()
        except:
            result["response"] = response.text[:500] if response.text else None
        
        return result
    except Exception as e:
        return {
            "endpoint": endpoint,
            "method": method,
            "status": "ERROR",
            "response": str(e)
        }

def main():
    print("=" * 60)
    print("MOL TBOOK API DISCOVERY")
    print("=" * 60)
    
    endpoints_to_test = [
        # Profile endpoints
        ("GET", "/agent/profile", None),
        ("GET", "/agent/me", None),
        ("GET", "/profile", None),
        ("GET", "/me", None),
        ("GET", "/auth/me", None),
        
        # Feed/Posts endpoints
        ("GET", "/feed", None),
        ("GET", "/posts", None),
        ("GET", "/posts/recent", None),
        ("GET", "/posts/feed", None),
        ("GET", "/submolts/feed", None),
        
        # Create post (with submolt_name)
        ("POST", "/posts", {"title": "Test", "content": "Test content", "submolt_name": "general"}),
        ("POST", "/posts", {"title": "Test", "content": "Test content"}),
        
        # Submolts
        ("GET", "/submolts", None),
        ("GET", "/submolts/general", None),
    ]
    
    with httpx.Client(headers=HEADERS) as client:
        results = []
        for method, endpoint, data in endpoints_to_test:
            print(f"\nTesting {method} {endpoint}...")
            result = test_endpoint(client, method, endpoint, data)
            results.append(result)
            
            status = result["status"]
            print(f"  Status: {status}")
            
            if result["response"]:
                if isinstance(result["response"], dict):
                    # Print first few keys
                    keys = list(result["response"].keys())[:5]
                    print(f"  Response keys: {keys}")
                    # Print a sample of the response
                    preview = json.dumps(result["response"], indent=2)[:300]
                    print(f"  Preview: {preview}...")
                else:
                    print(f"  Response: {str(result['response'])[:200]}")
    
    print("\n" + "=" * 60)
    print("DISCOVERY COMPLETE")
    print("=" * 60)
    
    # Find working endpoints
    print("\nWorking endpoints (2xx status):")
    for r in results:
        if isinstance(r["status"], int) and 200 <= r["status"] < 300:
            print(f"  {r['method']} {r['endpoint']}")

if __name__ == "__main__":
    main()
