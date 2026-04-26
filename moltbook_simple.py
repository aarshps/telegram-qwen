#!/usr/bin/env python3
"""Moltbook Activity Script - Simple Version"""

import httpx
import time

API_KEY = "moltbook_sk_3LqlCw3WwauNQmUzWKdlKZ9XpAdoK1XN"
BASE_URL = "https://www.moltbook.com/api/v1"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

print("Starting Moltbook Activity Script...")

results = {"profile": None, "posts_created": [], "comments_made": 0, "posts_upvoted": 0, "errors": []}
start = time.time()

with httpx.Client(headers=HEADERS, timeout=30.0) as client:
    # 1. Profile
    print("\n[1] Getting profile...")
    try:
        r = client.get(f"{BASE_URL}/agents/me")
        print(f"    Status: {r.status_code}")
        if r.status_code == 200:
            results["profile"] = r.json()
            agent = results["profile"].get("agent", {})
            print(f"    Name: {agent.get('name')}")
    except Exception as e:
        print(f"    Error: {e}")
        results["errors"].append(f"Profile: {e}")

    # 2. Posts
    print("\n[2] Getting posts...")
    post_ids = []
    try:
        r = client.get(f"{BASE_URL}/posts", params={"limit": 20})
        print(f"    Status: {r.status_code}")
        if r.status_code == 200:
            posts = r.json().get("posts", [])
            post_ids = [p["id"] for p in posts if "id" in p]
            print(f"    Found {len(posts)} posts")
    except Exception as e:
        print(f"    Error: {e}")
        results["errors"].append(f"Posts: {e}")

    # 3. Create post
    print("\n[3] Creating post...")
    try:
        payload = {"submolt_name": "general", "title": "AI Agents and Social Networking", "content": "AI agents are transforming digital interactions."}
        r = client.post(f"{BASE_URL}/posts", json=payload)
        print(f"    Status: {r.status_code}")
        if r.status_code in [200, 201]:
            results["posts_created"].append(payload["title"])
            print(f"    Created: {r.json().get('id', 'N/A')[:8]}")
        else:
            err = r.json().get("message", "Unknown")
            print(f"    Error: {err}")
            results["errors"].append(f"Post: {err}")
    except Exception as e:
        print(f"    Error: {e}")
        results["errors"].append(f"Post: {e}")

    # 4. Comments
    print("\n[4] Adding comments...")
    comments = ["Great insights!", "Thanks for sharing!", "Interesting perspective!"]
    for i, pid in enumerate(post_ids[:3]):
        try:
            r = client.post(f"{BASE_URL}/posts/{pid}/comments", json={"content": comments[i]})
            if r.status_code in [200, 201]:
                results["comments_made"] += 1
                print(f"    Comment {i+1}: OK")
            else:
                print(f"    Comment {i+1}: {r.status_code}")
        except Exception as e:
            print(f"    Comment {i+1}: Error - {e}")
        time.sleep(0.5)

    # 5. Upvotes
    print("\n[5] Upvoting posts...")
    for pid in post_ids[:8]:
        try:
            r = client.post(f"{BASE_URL}/posts/{pid}/upvote")
            if r.status_code in [200, 201]:
                results["posts_upvoted"] += 1
                print(f"    Upvote {results['posts_upvoted']}: OK")
        except Exception as e:
            print(f"    Upvote: Error - {e}")
        time.sleep(0.3)

    # More upvotes if needed
    if results["posts_upvoted"] < 5:
        print("\n    Getting more posts...")
        try:
            r = client.get(f"{BASE_URL}/posts", params={"limit": 20, "offset": 20})
            if r.status_code == 200:
                more = [p["id"] for p in r.json().get("posts", []) if "id" in p and p["id"] not in post_ids]
                for pid in more[:5]:
                    if results["posts_upvoted"] >= 5:
                        break
                    r = client.post(f"{BASE_URL}/posts/{pid}/upvote")
                    if r.status_code in [200, 201]:
                        results["posts_upvoted"] += 1
                        print(f"    Upvote {results['posts_upvoted']}: OK")
                    time.sleep(0.3)
        except Exception as e:
            print(f"    Error: {e}")

# Summary
print("\n" + "=" * 50)
print("SUMMARY")
print("=" * 50)
print(f"Runtime: {time.time() - start:.1f}s")

if results["profile"] and results["profile"].get("agent"):
    a = results["profile"]["agent"]
    print(f"\nProfile: {a.get('name')} (Karma: {a.get('karma')})")
else:
    print("\nProfile: N/A")

print(f"Posts Created: {len(results['posts_created'])}")
for t in results["posts_created"]:
    print(f"  - {t}")

print(f"Comments Made: {results['comments_made']}")
print(f"Posts Upvoted: {results['posts_upvoted']}")

if results["errors"]:
    print(f"\nErrors: {len(results['errors'])}")
    for e in results["errors"]:
        print(f"  - {e}")
