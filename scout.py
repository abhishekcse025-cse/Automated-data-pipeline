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
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

def run_scout():
    with sync_playwright() as p:
        print("Step 1: Launching Stealth Browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        
        try:
            print("Step 2: Navigating to RBI Website...")
            # We wait for the network to be quiet so the table is definitely there
            page.goto("https://www.rbi.org.in/Scripts/NotificationUser.aspx", wait_until="networkidle", timeout=90000)
            
            print("Step 3: Deep Scanning for Notification Links...")
            # We look for ANY link on the page and filter by content
            page.wait_for_selector("a", timeout=30000)
            all_links = page.locator("a").all()
            
            target_title = None
            for link in all_links:
                text = link.inner_text().strip()
                # 2026 logic: Look for long text containing dates or regulatory words
                if len(text) > 30 and ("2026" in text or "Feb" in text or "Circular" in text):
                    target_title = text
                    print(f"✅ Found match: {target_title}")
                    break
            
            if not target_title:
                # Emergency fallback if deep scan fails
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

            print("Step 5: Asking Gemini to summarize...")
            prompt = f"Summarize this RBI notification: '{target_title}' in 3 simple bullets: Date, Who is affected, and Action required."
            response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
            
            print("Step 6: Sending report to Telegram...")
            report = f"🚨 *NEW RBI UPDATE*\n\n{response.text}"
            send_to_telegram(report)
            print("DONE: Notification sent!")

        except Exception as e:
            print(f"❌ ERROR DURING SCOUTING: {e}")
            page.screenshot(path="debug_screenshot.png")
            
        finally:
            browser.close()

if __name__ == "__main__":
    run_scout()