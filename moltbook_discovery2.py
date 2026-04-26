#!/usr/bin/env python3
"""
Moltbook API Discovery Script - Part 2
Tests more endpoint patterns for profile, comments, upvotes.
"""

import httpx
import json

API_KEY = "moltbook_sk_3LqlCw3WwauNQmUzWKdlKZ9XpAdoK1XN"
BASE_URL = "https://www.moltbook.com/api/v1"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def test_endpoint(client, method, endpoint, data=None, params=None):
    """Test a single endpoint."""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = client.get(url, params=params, timeout=15.0)
        elif method == "POST":
            response = client.post(url, json=data, params=params, timeout=15.0)
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
    print("MOL TBOOK API DISCOVERY - PART 2")
    print("=" * 60)
    
    # First get a post ID to test comments/upvotes
    print("\nFetching a post ID for testing...")
    with httpx.Client(headers=HEADERS) as client:
        response = client.get(f"{BASE_URL}/posts", params={"limit": 1}, timeout=15.0)
        if response.status_code == 200:
            data = response.json()
            if data.get("posts") and len(data["posts"]) > 0:
                test_post_id = data["posts"][0]["id"]
                print(f"Using post ID: {test_post_id}")
            else:
                test_post_id = None
                print("No posts found")
        else:
            test_post_id = None
            print(f"Failed to get posts: {response.status_code}")
    
    endpoints_to_test = [
        # Profile/Agent endpoints
        ("GET", "/auth/me", None),
        ("GET", "/agent", None),
        ("GET", "/agents/me", None),
        ("GET", "/my-agent", None),
        ("GET", "/whoami", None),
        
        # Comments endpoints
        ("GET", f"/posts/{test_post_id}/comments" if test_post_id else "/posts/test/comments", None),
        ("POST", f"/posts/{test_post_id}/comments" if test_post_id else "/posts/test/comments", {"content": "Test comment"}),
        ("POST", f"/posts/{test_post_id}/comment" if test_post_id else "/posts/test/comment", {"content": "Test comment"}),
        ("POST", "/comments", {"post_id": test_post_id, "content": "Test comment"} if test_post_id else {}),
        
        # Upvote endpoints
        ("POST", f"/posts/{test_post_id}/upvote" if test_post_id else "/posts/test/upvote", None),
        ("POST", f"/posts/{test_post_id}/vote" if test_post_id else "/posts/test/vote", {"vote": 1}),
        ("POST", "/votes", {"post_id": test_post_id, "vote": 1} if test_post_id else {}),
        ("POST", f"/posts/{test_post_id}/upvotes" if test_post_id else "/posts/test/upvotes", None),
        
        # Submolts list
        ("GET", "/submolts", None),
        ("GET", "/submolts/list", None),
        
        # More posts patterns
        ("GET", "/posts", {"limit": 5}),
        ("GET", "/posts", {"offset": 0, "limit": 5}),
    ]
    
    with httpx.Client(headers=HEADERS) as client:
        results = []
        for method, endpoint, data in endpoints_to_test:
            params = data if method == "GET" and isinstance(data, dict) else None
            post_data = data if method == "POST" else None
            
            print(f"\nTesting {method} {endpoint}...")
            result = test_endpoint(client, method, endpoint, post_data, params if method == "GET" else None)
            results.append(result)
            
            status = result["status"]
            print(f"  Status: {status}")
            
            if result["response"]:
                if isinstance(result["response"], dict):
                    # Print first few keys
                    keys = list(result["response"].keys())[:5]
                    print(f"  Response keys: {keys}")
                    # Print a sample of the response
                    preview = json.dumps(result["response"], indent=2)[:400]
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
