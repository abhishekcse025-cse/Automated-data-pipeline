import os
import requests
import datetime
from google import genai
from playwright.sync_api import sync_playwright

# 1. SETUP & AUTH
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
MEMORY_FILE = "last_notif.txt"

if not os.path.exists('briefs'): 
    os.makedirs('briefs')

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

def run_scout():
    with sync_playwright() as p:
        print("Step 1: Launching Stealth Browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        
        try:
            print("Step 2: Navigating to RBI (Patient Mode)...")
            page.goto("https://www.rbi.org.in/Scripts/NotificationUser.aspx", 
                      wait_until="domcontentloaded", timeout=90000)
            
            print("Step 3: Scanning for notification links...")
            # We use a nested try/except here to handle the specific scraping logic
            try:
                # Give the page a moment to settle
                page.wait_for_load_state("networkidle", timeout=30000)
                
                # Broad Net: Look for the first link that looks like an RBI Notification
                target_element = page.locator("a[href*='NotificationUser.aspx?Id=']").first
                
                if target_element.count() > 0:
                    target_title = target_element.inner_text().strip()
                    print(f"✅ Found headline: {target_title}")
                else:
                    print("⚠️ No notification links found on page layout.")
                    page.screenshot(path="error_screenshot.png")
                    return

            except Exception as e:
                print(f"⚠️ Search failed: {e}. Saving screenshot.")
                page.screenshot(path="error_screenshot.png")
                return 

            # --- SMART MEMORY ---
            if os.path.exists(MEMORY_FILE):
                with open(MEMORY_FILE, "r") as f:
                    if target_title == f.read().strip():
                        print("Step 4: No new updates. System going to sleep.")
                        return 

            print("Step 4: NEW Update Detected!")
            with open(MEMORY_FILE, "w") as f:
                f.write(target_title)

        # --- STEP 5: THE SOVEREIGN BRIEF (AI RESEARCH) ---
            print("Step 5: Generating Deep Intelligence...")
            try:
                prompt = f"""
                Analyze the RBI notification: '{target_title}'
                Provide a Sovereign Brief for a Fintech Founder:
                1. THE HEADLINE: The single most impactful change.
                2. THE FINTECH IMPACT: How this affects UPI, Lending, or KYC.
                3. THE 'CODE-RED' CHECK: Immediate compliance deadlines.
                4. PREVIOUS CONTEXT: What older policy does this update?
                """
                
                try:
                    # ATTEMPT 1: Try with Google Search (the "Satellite" approach)
                    response = client.models.generate_content(
                        model="gemini-2.0-flash", 
                        contents=prompt,
                        config={'tools': [{'google_search': {}}]}
                    )
                    print("✅ AI Research successful via Google Search.")
                except Exception as search_err:
                    # ATTEMPT 2: Fallback to direct AI summary (the "Internal" approach)
                    print(f"⚠️ Search tool failed ({search_err}). Falling back to direct AI summary...")
                    response = client.models.generate_content(
                        model="gemini-2.0-flash", 
                        contents=prompt
                    )
                    print("✅ AI Summary successful (Direct).")

                final_text = response.text

                # ARCHIVING
                date_str = datetime.date.today().strftime("%Y-%m-%d")
                filename = f"briefs/rbi_brief_{date_str}.md"
                with open(filename, "w") as f:
                    f.write(f"# RBI Brief: {date_str}\n\n{final_text}")
                print(f"✅ Brief Archived: {filename}")

            except Exception as ai_err:
                # If BOTH attempts fail (likely a total API quota outage)
                print(f"❌ Total AI Failure: {ai_err}")
                final_text = f"*Title:* {target_title}\n\n_(Note: AI summary currently unavailable. Please check the RBI site directly for details.)_"
            # --- STEP 6: SENDING ---
            print("Step 6: Sending to Telegram...")
            send_to_telegram(f"🚨 *NEW SOVEREIGN BRIEF*\n\n{final_text}")
            print("Process Complete.")

        except Exception as main_err:
            print(f"❌ Critical Error: {main_err}")
        finally:
            browser.close()

if __name__ == "__main__":
    run_scout()