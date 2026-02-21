import os
import requests
from google import genai
from playwright.sync_api import sync_playwright

# 1. SETUP - Pulling secrets from GitHub Environment
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
MEMORY_FILE = "last_notif.txt"

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

def run_scout():
    with sync_playwright() as p:
        print("Step 1: Launching Stealth Browser...")
        browser = p.chromium.launch(headless=True)
        # Using a real User Agent so the RBI site thinks we are a human
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        
        try:
            print("Step 2: Navigating to RBI Website...")
            page.goto("https://www.rbi.org.in/Scripts/NotificationUser.aspx", wait_until="networkidle", timeout=90000)
            
            print("Step 3: Deep Scanning for Notification Links...")
            page.wait_for_selector("a", timeout=30000)
            all_links = page.locator("a").all()
            
            target_title = None
            for link in all_links:
                text = link.inner_text().strip()
                # Looking for current year or specific keywords to find the latest news
                if len(text) > 30 and ("2026" in text or "Feb" in text or "Circular" in text):
                    target_title = text
                    print(f"✅ Found match: {target_title}")
                    break
            
            if not target_title:
                print("Deep scan failed, trying fallback selector...")
                target_title = page.locator("a.sectionheader").first.inner_text().strip()

            # --- SMART MEMORY ---
            if os.path.exists(MEMORY_FILE):
                with open(MEMORY_FILE, "r") as f:
                    last_title = f.read().strip()
                if target_title == last_title:
                    print("Step 4: No new updates. System going to sleep.")
                    return 

            print("Step 4: NEW Update Detected!")
            with open(MEMORY_FILE, "w") as f:
                f.write(target_title)

            # --- STEP 5: THE AI BRAIN (WITH BACKUP PLAN) ---
            print("Step 5: Asking Gemini to summarize...")
            try:
                prompt = f"""
                Analyze this RBI Notification: '{target_title}'
                Provide a 'Sovereign Brief' for high-level executives:
                1. THE CORE: What is the single biggest change? (1 sentence)
                2. SECTOR IMPACT: Who wins and who loses? (Banks, Fintech, or NBFCs?)
                3. ACTIONABLE: What should a CEO do by 11:00 AM today?
                4. RISK LEVEL: Low, Medium, or High?
                """
                # Using Gemini 2.0 Flash as it's the 2026 standard
                response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
                final_text = response.text
            except Exception as ai_err:
                # If Gemini is tired (429 error), we don't crash! We just send the title.
                print(f"⚠️ Gemini Quota full/error. Sending title only. Error: {ai_err}")
                final_text = f"*Title:* {target_title}\n\n_(Note: AI summary unavailable due to daily limit. Please check the RBI site for details.)_"

            # --- STEP 6: THE MESSENGER ---
            print("Step 6: Sending report to Telegram...")
            report = f"🚨 *NEW RBI UPDATE*\n\n{final_text}"
            send_to_telegram(report)
            print("DONE: Notification sent!")

        except Exception as e:
            print(f"❌ ERROR DURING SCOUTING: {e}")
            page.screenshot(path="debug_screenshot.png")
            
        finally:
            browser.close()

if __name__ == "__main__":
    run_scout()