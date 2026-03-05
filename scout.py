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

# Ensure 'briefs' folder exists for your Archive
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
        # Using a realistic user agent to avoid being blocked as a bot
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        
        try:
            print("Step 2: Navigating to RBI (Patient Mode)...")
            page.goto("https://www.rbi.org.in/Scripts/NotificationUser.aspx", 
                      wait_until="domcontentloaded", timeout=90000)
            
print("Step 3: Scanning for notification links...")
            try:
                # We'll wait for ANY link inside the main content area to be sure
                page.wait_for_load_state("networkidle") 
                # Broad selector: Look for links that point to 'NotificationUser.aspx?Id='
                target_element = page.locator("a[href*='NotificationUser.aspx?Id=']").first
                
                if target_element.count() > 0:
                    target_title = target_element.inner_text().strip()
                    print(f"✅ Found match: {target_title}")
                else:
                    raise Exception("No notification links found on page.")
                    
            except Exception as e:
                print(f"⚠️ Search failed: {e}. Saving screenshot for debug.")
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
                Research the RBI notification: '{target_title}'
                Provide a Sovereign Brief for a Fintech Founder:
                1. THE HEADLINE: The single most impactful change.
                2. THE FINTECH IMPACT: How this affects UPI, Lending, or KYC.
                3. THE 'CODE-RED' CHECK: Immediate compliance deadlines.
                4. PREVIOUS CONTEXT: What older policy does this update?
                """
                
                # Using the stable dictionary-style config for the search tool
                response = client.models.generate_content(
                    model="gemini-2.0-flash", 
                    contents=prompt,
                    config={'tools': [{'google_search': {}}]}
                )
                final_text = response.text

                # ARCHIVE FEATURE: Save as a Markdown file
                date_str = datetime.date.today().strftime("%Y-%m-%d")
                filename = f"briefs/rbi_brief_{date_str}.md"
                with open(filename, "w") as f:
                    f.write(f"# RBI Brief: {date_str}\n\n{final_text}")
                print(f"✅ Brief Archived: {filename}")

            except Exception as ai_err:
                print(f"⚠️ AI Tool Error: {ai_err}")
                final_text = f"*Title:* {target_title}\n\n_(Note: AI summary currently unavailable. Check RBI site for details.)_"
            
            # --- STEP 6: SENDING ---
            print("Step 6: Sending to Telegram...")
            send_to_telegram(f"🚨 *NEW SOVEREIGN BRIEF*\n\n{final_text}")
            print("Process Complete.")

        finally:
            browser.close()

if __name__ == "__main__":
    run_scout()