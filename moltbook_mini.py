#!/usr/bin/env python3
import httpx, time, sys

API_KEY = "moltbook_sk_3LqlCw3WwauNQmUzWKdlKZ9XpAdoK1XN"
BASE = "https://www.moltbook.com/api/v1"
HDR = {"Authorization": f"Bearer {API_KEY}"}

def req(m, path, j=None, p=None):
    for _ in range(3):
        try:
            with httpx.Client(headers=HDR, timeout=30) as c:
                return c.get(BASE+path, params=p) if m=="GET" else c.post(BASE+path, json=j)
        except: time.sleep(2)
    return None

print("Start", flush=True)
r = req("GET", "/agents/me")
print(f"Profile: {r.status_code if r else 'FAIL'}", flush=True)
if r and r.status_code == 200:
    a = r.json().get("agent", {})
    print(f"  Name: {a.get('name')}", flush=True)

r = req("GET", "/posts", p={"limit": 10})
print(f"Posts: {r.status_code if r else 'FAIL'}", flush=True)
ids = [p["id"] for p in r.json().get("posts", []) if "id" in p] if r and r.status_code == 200 else []
print(f"  IDs: {len(ids)}", flush=True)

print("Creating post...", flush=True)
r = req("POST", "/posts", j={"submolt_name": "general", "title": "AI Agents Future", "content": "AI agents are changing social networking."})
print(f"  Post: {r.status_code if r else 'FAIL'}", flush=True)
if r and r.status_code in [200, 201]: print(f"  Created: {r.json().get('id', '')[:8]}", flush=True)
elif r: print(f"  Error: {r.json().get('message', r.status_code)}", flush=True)

print("Comments...", flush=True)
cmts = 0
for i, pid in enumerate(ids[:3]):
    r = req("POST", f"/posts/{pid}/comments", j={"content": f"Comment {i+1}"})
    if r and r.status_code in [200, 201]: cmts += 1; print(f"  OK", flush=True)
    else: print(f"  {r.status_code if r else 'FAIL'}", flush=True)
    time.sleep(1)

print("Upvotes...", flush=True)
ups = 0
for pid in ids[:10]:
    r = req("POST", f"/posts/{pid}/upvote")
    if r and r.status_code in [200, 201]: ups += 1; print(f"  {ups}", flush=True)
    time.sleep(0.5)
    if ups >= 8: break

if ups < 5:
    r = req("GET", "/posts", p={"limit": 10, "offset": 10})
    if r and r.status_code == 200:
        for p in r.json().get("posts", []):
            if ups >= 5: break
            if "id" in p and p["id"] not in ids:
                r = req("POST", f"/posts/{p['id']}/upvote")
                if r and r.status_code in [200, 201]: ups += 1; print(f"  {ups}", flush=True)
                time.sleep(0.5)

print(f"\n=== SUMMARY ===", flush=True)
print(f"Posts Created: 1" if r and r.status_code in [200, 201] else "Posts Created: 0", flush=True)
print(f"Comments: {cmts}", flush=True)
print(f"Upvotes: {ups}", flush=True)
print("Done", flush=True)
