print("Hello from test script!")
import httpx
print("httpx imported")
r = httpx.get("https://httpbin.org/get", timeout=10)
print(f"Response: {r.status_code}")
