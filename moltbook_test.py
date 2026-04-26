#!/usr/bin/env python3
"""Moltbook Activity Script - Test Version"""

import httpx
import time

print("Starting...")

API_KEY = "moltbook_sk_3LqlCw3WwauNQmUzWKdlKZ9XpAdoK1XN"
BASE_URL = "https://www.moltbook.com/api/v1"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

print("Making request...")

with httpx.Client(headers=HEADERS, timeout=30.0) as client:
    print("Client created")
    r = client.get(f"{BASE_URL}/agents/me")
    print(f"Profile status: {r.status_code}")
    
    r = client.get(f"{BASE_URL}/posts", params={"limit": 5})
    print(f"Posts status: {r.status_code}")

print("Done!")
