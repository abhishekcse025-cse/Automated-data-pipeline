import os
import requests
from google import genai
from playwright.sync_api import sync_playwright

# ... the rest of your code follows below ...

def run_scout():
    send_to_telegram("Test: The Ghost Pipeline is active!")
    with sync_playwright() as p:
        # 1. STEALTH SETUP: Acting like a real human browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            # 2. PATIENT LOADING: Give the government site up to 90 seconds
            print("Accessing RBI Portal...")
            page.goto("https://www.rbi.org.in/Scripts/NotificationUser.aspx", wait_until="domcontentloaded", timeout=90000)
            
            # 3. FLEXIBLE SEARCH: Look for 'sectionheader' or standard links
            page.wait_for_selector("a.sectionheader", timeout=30000)
            target_link = page.locator("a.sectionheader").first
            title = target_link.inner_text().strip()

            # --- THE MEMORY BRICK (Your replacement starts here) ---
            if os.path.exists(MEMORY_FILE):
                with open(MEMORY_FILE, "r") as f:
                    last_title = f.read().strip()
                if title == last_title:
                    print(f"Skipping: '{title}' has already been reported.")
                    return # This stops the bot from messaging you
            
            # If we reach here, it's a NEW notification
            print(f"New Notification Found: {title}")
            with open(MEMORY_FILE, "w") as f:
                f.write(title)
            # --- THE MEMORY BRICK ENDS ---

            # 4. THE BRAIN: Gemini analysis
            prompt = f"Summarize this RBI law: '{title}' in 3 bullet points for a busy bank manager."
            response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
            
            # 5. THE DISTRIBUTOR: Send to Telegram
            report = f"🚨 *NEW RBI UPDATE*\n\n{response.text}"
            send_to_telegram(report)
            print("Report sent successfully!")

        except Exception as e:
            print(f"Scout Error: {e}")
            # If it fails, take a picture of the error for us to see
            page.screenshot(path="error_debug.png")
            
        finally:
            browser.close()