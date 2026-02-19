import os
from google import genai
from playwright.sync_api import sync_playwright

# 1. SETUP THE BRAIN (Modern 2026 SDK)
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def run_scout():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # We act like a real Chrome browser to avoid being blocked
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        
        print("Scouting RBI Notifications...")
        try:
            # Go to the site and wait for it to actually finish loading
            page.goto("https://www.rbi.org.in/Scripts/NotificationUser.aspx", wait_until="networkidle", timeout=60000)
            
            # FLEXIBLE SEARCH: Instead of a specific table name, 
            # we look for the "sectionheader" class which RBI uses for notification titles.
            page.wait_for_selector("a.sectionheader", timeout=20000)
            first_notif = page.locator("a.sectionheader").first
            
            title = first_notif.inner_text()
            link = "https://www.rbi.org.in/Scripts/" + first_notif.get_attribute("href")
            
            print(f"Target Found: {title}")

            # 2. THE ANALYST
            prompt = f"Analyze this RBI notification: '{title}'. Extract: 1. Effective Date, 2. Who it affects, 3. Penalties. Format in 3 short bullets."
            
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )
            
            print("\n--- ANALYSIS REPORT ---")
            print(response.text)
            print("-----------------------")

        except Exception as e:
            print(f"Scout Error: {e}")
            # This saves a picture of the error so you can see what the robot saw!
            page.screenshot(path="error.png")
            
        browser.close()

if __name__ == "__main__":
    run_scout()