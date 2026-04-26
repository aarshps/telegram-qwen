#!/usr/bin/env python3
import httpx, time, sys

API_KEY = "moltbook_sk_3LqlCw3WwauNQmUzWKdlKZ9XpAdoK1XN"
BASE = "https://www.moltbook.com/api/v1"
HDR = {"Authorization": f"Bearer {API_KEY}"}

def req(m, path, j=None, p=None):
    for _ in range(2):
        try:
            with httpx.Client(headers=HDR, timeout=20) as c:
                return c.get(BASE+path, params=p) if m=="GET" else c.post(BASE+path, json=j)
        except: time.sleep(1)
    return None

print("=== MOL TBOOK ACTIVITY ===", flush=True)
start = time.time()

# Profile
print("\n[1] Profile...", flush=True)
r = req("GET", "/agents/me")
profile = None
if r and r.status_code == 200:
    profile = r.json()
    a = profile.get("agent", {})
    print(f"  Name: {a.get('name')}", flush=True)
    print(f"  Karma: {a.get('karma')}", flush=True)
else:
    print(f"  Failed: {r.status_code if r else 'timeout'}", flush=True)

# Posts
print("\n[2] Posts...", flush=True)
r = req("GET", "/posts", p={"limit": 15})
ids = []
if r and r.status_code == 200:
    posts = r.json().get("posts", [])
    ids = [p["id"] for p in posts if "id" in p]
    print(f"  Found {len(ids)} posts", flush=True)
else:
    print(f"  Failed: {r.status_code if r else 'timeout'}", flush=True)

# Create Post
print("\n[3] Create Post...", flush=True)
post_created = False
r = req("POST", "/posts", j={"submolt_name": "general", "title": "AI Agents Future", "content": "AI agents are changing social networking."})
if r and r.status_code in [200, 201]:
    post_created = True
    print(f"  Created: {r.json().get('id', '')[:8]}", flush=True)
elif r:
    err = r.json().get('message', str(r.status_code))
    print(f"  Failed: {err}", flush=True)
else:
    print(f"  Failed: timeout", flush=True)

# Comments
print("\n[4] Comments...", flush=True)
cmts = 0
for i, pid in enumerate(ids[:3]):
    r = req("POST", f"/posts/{pid}/comments", j={"content": f"Great post!"})
    if r and r.status_code in [200, 201]:
        cmts += 1
        print(f"  Comment {i+1}: OK", flush=True)
    else:
        print(f"  Comment {i+1}: {r.status_code if r else 'timeout'}", flush=True)
    time.sleep(0.5)

# Upvotes
print("\n[5] Upvotes...", flush=True)
ups = 0
for pid in ids[:10]:
    r = req("POST", f"/posts/{pid}/upvote")
    if r and r.status_code in [200, 201]:
        ups += 1
        print(f"  {ups}", flush=True)
    time.sleep(0.3)
    if ups >= 8: break

# More upvotes if needed
if ups < 5:
    r = req("GET", "/posts", p={"limit": 10, "offset": 15})
    if r and r.status_code == 200:
        for p in r.json().get("posts", []):
            if ups >= 5: break
            if "id" in p and p["id"] not in ids:
                r = req("POST", f"/posts/{p['id']}/upvote")
                if r and r.status_code in [200, 201]:
                    ups += 1
                    print(f"  {ups}", flush=True)
                time.sleep(0.3)

# Summary
elapsed = time.time() - start
print(f"\n=== SUMMARY ({elapsed:.1f}s) ===", flush=True)
print(f"Posts Created: {1 if post_created else 0}", flush=True)
if post_created:
    print(f"  - AI Agents Future", flush=True)
print(f"Comments Made: {cmts}", flush=True)
print(f"Posts Upvoted: {ups}", flush=True)

if profile and profile.get("agent"):
    a = profile["agent"]
    print(f"\n=== AGENT PROFILE ===", flush=True)
    print(f"  Name: {a.get('name')}", flush=True)
    print(f"  Display: {a.get('display_name')}", flush=True)
    print(f"  Description: {a.get('description')}", flush=True)
    print(f"  Karma: {a.get('karma')}", flush=True)
    print(f"  Posts: {a.get('posts_count')}", flush=True)
    print(f"  Comments: {a.get('comments_count')}", flush=True)
    print(f"  Verified: {a.get('is_verified')}", flush=True)

print("\n=== COMPLETE ===", flush=True)
