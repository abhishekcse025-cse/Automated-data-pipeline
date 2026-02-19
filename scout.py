import os
import requests
from google import genai
from playwright.sync_api import sync_playwright

# 1. SETUP
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
MEMORY_FILE = "last_notif.txt"

def send_to_telegram(text):
    if TELEGRAM_TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
        requests.post(url, data=data)

def run_scout():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto("https://www.rbi.org.in/Scripts/NotificationUser.aspx", wait_until="networkidle")
            target_link = page.locator("a.sectionheader").first
            title = target_link.inner_text()

            # --- THE MEMORY BRICK ---
            if os.path.exists(MEMORY_FILE):
                with open(MEMORY_FILE, "r") as f:
                    last_title = f.read().strip()
                if title == last_title:
                    print("No new notifications since last check.")
                    return # Exit early!

            # If we reach here, it's a NEW notification
            print(f"New Notification Found: {title}")
            
            # Save the new title to memory
            with open(MEMORY_FILE, "w") as f:
                f.write(title)

            # 2. THE BRAIN
            prompt = f"Analyze this RBI notification: '{title}'. Extract: 1. Effective Date, 2. Affected Entities, 3. Penalties. Summarize in 3 short bullets."
            response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
            
            # 3. SEND REPORT
            report = f"🚨 *NEW RBI ALERT*\n\n{response.text}"
            send_to_telegram(report)

        except Exception as e:
            print(f"Scout Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run_scout()