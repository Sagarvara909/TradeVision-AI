import asyncio
import base64
import json
import os
import subprocess
import time
import urllib.request
import websockets

ARTIFACT_DIR = "/home/sagar/.gemini/antigravity-ide/brain/ee59197a-392d-444f-8790-92548c362540"

# 1. Get a valid JWT token from backend
import requests
LOGIN_URL = "http://127.0.0.1:8000/api/v1/auth/login"
REG_URL = "http://127.0.0.1:8000/api/v1/auth/register"

email = "ui_demo@tradevision.ai"
password = "Password123!"

try:
    requests.post(REG_URL, json={"email": email, "password": password})
except Exception:
    pass

res = requests.post(LOGIN_URL, json={"email": email, "password": password})
token_data = res.json()
access_token = token_data.get("access_token")
refresh_token = token_data.get("refresh_token")

print(f"Logged in, token length: {len(access_token) if access_token else 0}")

# 2. Launch Chrome headless with remote debugging
chrome_proc = subprocess.Popen([
    "google-chrome",
    "--headless=new",
    "--no-sandbox",
    "--disable-gpu",
    "--remote-debugging-port=9222",
    "--window-size=1440,900",
    "--user-data-dir=/tmp/chrome_cdp_profile"
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

time.sleep(2)

async def capture_pages():
    # Discover tab WebSocket URL
    try:
        tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json").read())
        ws_url = tabs[0]["webSocketDebuggerUrl"]
    except Exception as e:
        print("Failed to connect to Chrome CDP:", e)
        return

    async with websockets.connect(ws_url) as ws:
        msg_id = 1

        async def send(method, params=None):
            nonlocal msg_id
            payload = {"id": msg_id, "method": method, "params": params or {}}
            msg_id += 1
            await ws.send(json.dumps(payload))
            while True:
                resp = json.loads(await ws.recv())
                if resp.get("id") == payload["id"]:
                    return resp.get("result")

        await send("Page.enable")
        await send("DOM.enable")

        # Set localStorage on localhost:8082
        await send("Page.navigate", {"url": "http://localhost:8082/login"})
        await asyncio.sleep(2)

        set_tokens_js = f"""
        localStorage.setItem('tv_access_token', '{access_token}');
        localStorage.setItem('tv_refresh_token', '{refresh_token}');
        """
        await send("Runtime.evaluate", {"expression": set_tokens_js})
        await asyncio.sleep(1)

        pages = [
            ("dashboard", "http://localhost:8082/dashboard"),
            ("upload", "http://localhost:8082/upload"),
            ("watchlist", "http://localhost:8082/watchlist"),
            ("settings", "http://localhost:8082/settings"),
            ("profile", "http://localhost:8082/profile"),
        ]

        for name, url in pages:
            print(f"Navigating to {name}: {url}...")
            await send("Page.navigate", {"url": url})
            await asyncio.sleep(2.5)  # wait for React rendering & API fetch

            shot_data = await send("Page.captureScreenshot", {"format": "png"})
            if shot_data and "data" in shot_data:
                img_bytes = base64.b64decode(shot_data["data"])
                out_path = os.path.join(ARTIFACT_DIR, f"{name}_page.png")
                with open(out_path, "wb") as f:
                    f.write(img_bytes)
                print(f"✅ Saved screenshot: {out_path} ({len(img_bytes)} bytes)")

asyncio.run(capture_pages())

# Terminate Chrome
chrome_proc.terminate()
print("All screenshots captured successfully!")
