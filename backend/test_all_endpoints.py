import sys
import os
import json

# Ensure backend root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

results = {}

def log_test(name, success, details=""):
    results[name] = {"success": success, "details": details}
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} [{name}] {details}")

print("\n==========================================")
print("🚀 RUNNING COMPREHENSIVE END-TO-END TESTS")
print("==========================================\n")

# 1. Health Check
try:
    res = client.get("/health")
    if res.status_code == 200 and res.json().get("status") == "ok":
        log_test("Health Check", True, str(res.json()))
    else:
        log_test("Health Check", False, f"Status: {res.status_code}, Body: {res.text}")
except Exception as e:
    log_test("Health Check", False, str(e))

# 2. Auth: Register / Login / Me
test_email = f"test_{os.getpid()}@example.com"
test_password = "SecurePassword123!"
auth_token = None

try:
    # Register
    res_reg = client.post("/api/v1/auth/register", json={"email": test_email, "password": test_password})
    if res_reg.status_code in (200, 201):
        log_test("Auth Register", True, f"Registered: {test_email}")
    else:
        log_test("Auth Register", False, f"Status {res_reg.status_code}: {res_reg.text}")

    # Login
    res_login = client.post("/api/v1/auth/login", json={"email": test_email, "password": test_password})
    if res_login.status_code == 200:
        auth_token = res_login.json().get("access_token")
        log_test("Auth Login", True, f"Token received (length: {len(auth_token)})")
    else:
        log_test("Auth Login", False, f"Status {res_login.status_code}: {res_login.text}")

    headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}

    # Me
    res_me = client.get("/api/v1/auth/me", headers=headers)
    if res_me.status_code == 200 and res_me.json().get("email") == test_email:
        log_test("Auth Me", True, f"User ID: {res_me.json().get('id')}")
    else:
        log_test("Auth Me", False, f"Status {res_me.status_code}: {res_me.text}")

    # Change Password
    res_cp = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": test_password, "new_password": "NewPassword123!"},
        headers=headers,
    )
    if res_cp.status_code == 200:
        log_test("Auth Change Password", True, res_cp.json().get("message", "Success"))
    else:
        log_test("Auth Change Password", False, f"Status {res_cp.status_code}: {res_cp.text}")

    # Settings Get
    res_set = client.get("/api/v1/auth/settings", headers=headers)
    if res_set.status_code == 200:
        log_test("Auth Get Settings", True, f"Theme: {res_set.json().get('theme')}, Exchange: {res_set.json().get('default_exchange')}")
    else:
        log_test("Auth Get Settings", False, f"Status {res_set.status_code}: {res_set.text}")

    # Settings Patch
    res_patch = client.patch(
        "/api/v1/auth/settings",
        json={"theme": "dark", "default_exchange": "NSE", "email_alerts": True},
        headers=headers,
    )
    if res_patch.status_code == 200 and res_patch.json().get("email_alerts") is True:
        log_test("Auth Update Settings", True, f"Alerts: {res_patch.json().get('email_alerts')}")
    else:
        log_test("Auth Update Settings", False, f"Status {res_patch.status_code}: {res_patch.text}")
except Exception as e:
    log_test("Auth Suite", False, str(e))

headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}

# 3. Market Service & Endpoints
try:
    # Quote
    res_q = client.get("/api/v1/market/quote/AAPL", headers=headers)
    if res_q.status_code == 200 and ("price" in res_q.json() or "close" in res_q.json()):
        log_test("Market Quote (AAPL)", True, f"Price: {res_q.json().get('price') or res_q.json().get('close')}")
    else:
        log_test("Market Quote (AAPL)", False, f"Status {res_q.status_code}: {res_q.text}")

    # Technical Analysis
    res_ta = client.get("/api/v1/market/analysis/AAPL", headers=headers)
    if res_ta.status_code == 200 and "rsi" in res_ta.json():
        ta_data = res_ta.json()
        log_test("Market Analysis (AAPL)", True, f"RSI: {ta_data.get('rsi')}, Trend: {ta_data.get('trend')}, EMA20: {ta_data.get('ema20')}")
    else:
        log_test("Market Analysis (AAPL)", False, f"Status {res_ta.status_code}: {res_ta.text}")

    # Risk Analysis
    res_risk = client.get("/api/v1/market/risk/AAPL", headers=headers)
    if res_risk.status_code == 200 and "confidence_score" in res_risk.json():
        risk_data = res_risk.json()
        log_test("Market Risk (AAPL)", True, f"Confidence: {risk_data.get('confidence_score')}/100, Risk: {risk_data.get('risk_level')}")
    else:
        log_test("Market Risk (AAPL)", False, f"Status {res_risk.status_code}: {res_risk.text}")

    # Suggestion
    res_sug = client.get("/api/v1/market/suggest/TATAPOWERR", headers=headers)
    if res_sug.status_code == 200:
        log_test("Market Suggest", True, f"Suggestions: {res_sug.json()}")
    else:
        log_test("Market Suggest", False, f"Status {res_sug.status_code}: {res_sug.text}")
except Exception as e:
    log_test("Market Suite", False, str(e))

# 4. OCR Upload
image_id = None
try:
    image_path = os.path.join(os.path.dirname(__file__), "test_image", "image.png")
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            files = {"file": ("image.png", f, "image/png")}
            res_ocr = client.post("/api/v1/ocr/upload", files=files, headers=headers)
            if res_ocr.status_code == 200:
                ocr_json = res_ocr.json()
                image_id = ocr_json.get("image_id")
                log_test("OCR Upload & Parsing", True, f"Image ID: {image_id}, Symbol: {ocr_json.get('symbol')}, Exchange: {ocr_json.get('exchange')}, Timeframe: {ocr_json.get('timeframe')}")
            else:
                log_test("OCR Upload & Parsing", False, f"Status {res_ocr.status_code}: {res_ocr.text}")
    else:
        log_test("OCR Upload & Parsing", False, f"Image file not found at {image_path}")
except Exception as e:
    log_test("OCR Upload & Parsing", False, str(e))

# 5. Report Creation & Retrieval & PDF Download
report_id = None
try:
    if image_id:
        report_payload = {
            "image_id": image_id,
            "symbol": "AAPL",
            "timeframe": "1day"
        }
        res_rep = client.post("/api/v1/reports", json=report_payload, headers=headers)
        if res_rep.status_code == 200:
            rep_json = res_rep.json()
            report_id = rep_json.get("id")
            log_test("Report Creation (LLM)", True, f"Report ID: {report_id}, Model: {rep_json.get('llm_model')}, Score: {rep_json.get('confidence_score')}")
        else:
            log_test("Report Creation (LLM)", False, f"Status {res_rep.status_code}: {res_rep.text}")

        # Fetch Report
        if report_id:
            res_get_rep = client.get(f"/api/v1/reports/{report_id}", headers=headers)
            if res_get_rep.status_code == 200:
                log_test("Report Get", True, f"Report symbol: {res_get_rep.json().get('symbol')}")
            else:
                log_test("Report Get", False, f"Status {res_get_rep.status_code}: {res_get_rep.text}")

            # PDF Download
            res_pdf = client.get(f"/api/v1/reports/{report_id}/pdf", headers=headers)
            if res_pdf.status_code == 200 and res_pdf.headers.get("content-type") == "application/pdf":
                log_test("Report PDF Generation", True, f"PDF bytes received: {len(res_pdf.content)} bytes")
            else:
                log_test("Report PDF Generation", False, f"Status {res_pdf.status_code}: {res_pdf.text}")
    else:
        log_test("Report Creation", False, "Skipped due to no image_id")
except Exception as e:
    log_test("Report Suite", False, str(e))

# 6. Chat Grounded Q&A
try:
    if report_id:
        chat_payload = {"message": "Why is the risk level medium?"}
        res_chat = client.post(f"/api/v1/chat/{report_id}", json=chat_payload, headers=headers)
        if res_chat.status_code == 200:
            chat_json = res_chat.json()
            log_test("Chat Q&A (LLM)", True, f"Answer: {chat_json.get('content')[:120]}...")
        else:
            log_test("Chat Q&A (LLM)", False, f"Status {res_chat.status_code}: {res_chat.text}")

        # Chat History
        res_chathist = client.get(f"/api/v1/chat/{report_id}", headers=headers)
        if res_chathist.status_code == 200:
            hist_msgs = res_chathist.json().get("messages", [])
            log_test("Chat History", True, f"Total messages in thread: {len(hist_msgs)}")
        else:
            log_test("Chat History", False, f"Status {res_chathist.status_code}: {res_chathist.text}")
    else:
        log_test("Chat Suite", False, "Skipped due to no report_id")
except Exception as e:
    log_test("Chat Suite", False, str(e))

# 7. Analysis History
try:
    res_hist = client.get("/api/v1/history", headers=headers)
    if res_hist.status_code == 200:
        entries = res_hist.json().get("entries", [])
        log_test("Analysis History", True, f"Found {len(entries)} history entries")
    else:
        log_test("Analysis History", False, f"Status {res_hist.status_code}: {res_hist.text}")
except Exception as e:
    log_test("Analysis History", False, str(e))

# 8. Watchlist
try:
    # Add to watchlist
    res_wl_add = client.post("/api/v1/watchlist", json={"symbol": "AAPL"}, headers=headers)
    wl_item_id = None
    if res_wl_add.status_code == 200:
        wl_item_id = res_wl_add.json().get("id")
        log_test("Watchlist Add", True, f"Added AAPL, Item ID: {wl_item_id}")
    else:
        log_test("Watchlist Add", False, f"Status {res_wl_add.status_code}: {res_wl_add.text}")

    # List watchlist
    res_wl_list = client.get("/api/v1/watchlist", headers=headers)
    if res_wl_list.status_code == 200:
        items = res_wl_list.json().get("items", [])
        log_test("Watchlist List", True, f"Watchlist has {len(items)} items")
    else:
        log_test("Watchlist List", False, f"Status {res_wl_list.status_code}: {res_wl_list.text}")

    # Remove from watchlist
    if wl_item_id:
        res_wl_del = client.delete(f"/api/v1/watchlist/{wl_item_id}", headers=headers)
        if res_wl_del.status_code == 200:
            log_test("Watchlist Remove", True, "Item removed successfully")
        else:
            log_test("Watchlist Remove", False, f"Status {res_wl_del.status_code}: {res_wl_del.text}")
except Exception as e:
    log_test("Watchlist Suite", False, str(e))

print("\n==========================================")
total_tests = len(results)
passed_tests = sum(1 for r in results.values() if r["success"])
print(f"📊 SUMMARY: {passed_tests}/{total_tests} Tests Passed ({(passed_tests/total_tests)*100:.1f}%)")
print("==========================================\n")
