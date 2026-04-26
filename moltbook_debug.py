#!/usr/bin/env python3
"""
Moltbook API Debug Script
"""

import httpx
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

API_KEY = "moltbook_sk_3LqlCw3WwauNQmUzWKdlKZ9XpAdoK1XN"
BASE_URL = "https://www.moltbook.com/api/v1"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def main():
    print("=" * 60)
    print("MOL TBOOK API DEBUG")
    print("=" * 60)
    
    with httpx.Client(headers=HEADERS, timeout=30.0) as client:
        # Test 1: Get posts to find a valid post ID
        print("\n[1] Getting posts...")
        response = client.get(f"{BASE_URL}/posts", params={"limit": 5})
        print(f"    Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            posts = data.get("posts", [])
            print(f"    Found {len(posts)} posts")
            if posts:
                test_post_id = posts[0]["id"]
                print(f"    Test post ID: {test_post_id}")
            else:
                test_post_id = None
        else:
            print(f"    Response: {response.text[:500]}")
            test_post_id = None
        
        # Test 2: Try creating a post with different payloads
        print("\n[2] Testing POST /posts with different payloads...")
        
        test_payloads = [
            {"submolt": "general", "title": "Test", "content": "Test content"},
            {"submolt": "general", "title": "Short", "content": "A"},
            {"submolt": "general", "title": "A" * 120, "content": "Test"},
            {"submolt": "general", "title": "Test Post Title Here", "content": "This is a longer test content to see if the API accepts it."},
        ]
        
        for i, payload in enumerate(test_payloads):
            print(f"\n    Payload {i+1}: title_len={len(payload['title'])}, content_len={len(payload['content'])}")
            response = client.post(f"{BASE_URL}/posts", json=payload)
            print(f"    Status: {response.status_code}")
            try:
                resp_data = response.json()
                if response.status_code != 200:
                    print(f"    Error: {resp_data}")
                else:
                    print(f"    Success! Post ID: {resp_data.get('id')}")
                    # Delete the test post if created
                    # (we won't actually delete to avoid complications)
            except Exception as e:
                print(f"    Parse error: {e}")
                print(f"    Raw: {response.text[:200]}")
        
        # Test 3: Try commenting
        if test_post_id:
            print(f"\n[3] Testing POST /posts/{test_post_id[:8]}.../comments...")
            comment_payloads = [
                {"content": "Test comment"},
                {"content": "A"},
                {"content": "This is a longer test comment to see if the API accepts it properly."},
            ]
            
            for i, payload in enumerate(comment_payloads):
                print(f"\n    Comment {i+1}: content_len={len(payload['content'])}")
                response = client.post(f"{BASE_URL}/posts/{test_post_id}/comments", json=payload)
                print(f"    Status: {response.status_code}")
                try:
                    resp_data = response.json()
                    if response.status_code != 200:
                        print(f"    Error: {resp_data}")
                    else:
                        print(f"    Success! Comment ID: {resp_data.get('id')}")
                except Exception as e:
                    print(f"    Parse error: {e}")
                    print(f"    Raw: {response.text[:200]}")
        
        # Test 4: Try upvoting
        if test_post_id:
            print(f"\n[4] Testing POST /posts/{test_post_id[:8]}.../upvote...")
            response = client.post(f"{BASE_URL}/posts/{test_post_id}/upvote")
            print(f"    Status: {response.status_code}")
            try:
                resp_data = response.json()
                print(f"    Response: {resp_data}")
            except Exception as e:
                print(f"    Parse error: {e}")
                print(f"    Raw: {response.text[:200]}")

if __name__ == "__main__":
    main()
