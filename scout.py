import os
import requests
import datetime
from google import genai
from google.genai import types
from playwright.sync_api import sync_playwright

# 1. SETUP
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
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        
        try:
            print("Step 2: Navigating to RBI...")
            page.goto("https://www.rbi.org.in/Scripts/NotificationUser.aspx", wait_until="networkidle", timeout=90000)
            
            print("Step 3: Scanning...")
            page.wait_for_selector("a", timeout=30000)
            target_title = page.locator("a.sectionheader").first.inner_text().strip()

            # --- SMART MEMORY ---
            if os.path.exists(MEMORY_FILE):
                with open(MEMORY_FILE, "r") as f:
                    if target_title == f.read().strip():
                        print("Step 4: No new updates.")
                        return 

            print("Step 4: NEW Update Detected!")
            with open(MEMORY_FILE, "w") as f:
                f.write(target_title)

            # --- STEP 5: THE SOVEREIGN BRIEF (WITH SEARCH & ARCHIVE) ---
            print("Step 5: Generating Deep Intelligence...")
            try:
                # Combining your new code's prompt with our scraper's target
                prompt = f"""
                Research the RBI notification: '{target_title}'
                Provide a Sovereign Brief for a Fintech Founder:
                1. THE HEADLINE: The single most impactful change.
                2. THE FINTECH IMPACT: How this affects UPI, Lending, or KYC.
                3. THE 'CODE-RED' CHECK: Immediate compliance deadlines.
                4. PREVIOUS CONTEXT: What older policy does this update?
                """
                
                # Using the 2026 SDK search tool configuration
                google_search_tool = types.Tool(google_search=types.GoogleSearch())
                config = types.GenerateContentConfig(tools=[google_search_tool])
                
                response = client.models.generate_content(
                    model="gemini-2.0-flash", 
                    contents=prompt,
                    config=config
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
                final_text = f"Title: {target_title}\n\n(AI Research failed, sending raw title.)"
            
            # --- STEP 6: SENDING ---
            print("Step 6: Sending to Telegram...")
            send_to_telegram(f"🚨 *NEW SOVEREIGN BRIEF*\n\n{final_text}")
            print("DONE!")

        finally:
            browser.close()

if __name__ == "__main__":
    run_scout()