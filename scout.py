import os
from google import genai
from playwright.sync_api import sync_playwright

# 1. SETUP THE BRAIN (2026 New SDK)
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def run_scout():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # We add a "User Agent" to look like a real person, not a robot
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        
        print("Scouting RBI...")
        page.goto("https://www.rbi.org.in/Scripts/NotificationUser.aspx", wait_until="domcontentloaded")
        
        try:
            # SMARTER SEARCH: Find the first link that looks like a notification
            # This is more stable than looking for a specific table ID
            first_notif = page.locator("a.sectionheader").first
            
            title = first_notif.inner_text()
            relative_url = first_notif.get_attribute("href")
            full_url = "https://www.rbi.org.in/Scripts/" + relative_url
            
            print(f"Found Notification: {title}")

            # 2. THE ANALYST
            prompt = f"Analyze this RBI notification title: '{title}'. Extract: 1. Effective Date, 2. Affected Entities, 3. Penalties. Summarize in 3 short bullets."
            
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )
            
            print("\n--- ANALYSIS REPORT ---")
            print(response.text)
            print("-----------------------")

        except Exception as e:
            print(f"Scout encountered a hurdle: {e}")
            # This helps us see what the robot saw
            page.screenshot(path="error_view.png")
            
        browser.close()

if __name__ == "__main__":
    run_scout()