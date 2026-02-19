import os
from google import genai
from playwright.sync_api import sync_playwright

# 1. SETUP THE BRAIN (2026 New SDK)
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def run_scout():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        
        print("Scouting RBI Notifications...")
        # Going to the main list which is more stable
        page.goto("https://www.rbi.org.in/Scripts/NotificationUser.aspx", wait_until="networkidle")
        
        # SMARTER SEARCH: Instead of a specific table, find the first link that has a date-like pattern
        # or is inside the main content area.
        try:
            # We wait for any link inside the content area to appear
            page.wait_for_selector("a.sectionheader", timeout=15000) 
            first_notif = page.locator("a.sectionheader").first
            
            title = first_notif.inner_text()
            link = "https://www.rbi.org.in/Scripts/" + first_notif.get_attribute("href")
            
            print(f"Target Found: {title}")

            # 2. THE ANALYST (Using Gemini 2.0/1.5 Flash via New SDK)
            prompt = f"Analyze this RBI notification title: '{title}'. Extract: 1. Effective Date, 2. Affected Entities, 3. Penalties. Summarize in 3 short bullets."
            
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )
            
            print("\n--- GOV-INTELLIGENCE REPORT ---")
            print(response.text)
            print("------------------------------")

        except Exception as e:
            print(f"Scout Error: {e}")
            # Take a screenshot so we can see what the robot saw (helpful for debugging!)
            page.screenshot(path="error_screen.png")
        
        browser.close()

if __name__ == "__main__":
    run_scout()