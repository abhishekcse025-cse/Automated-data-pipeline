import os
from google import genai
from playwright.sync_api import sync_playwright

# 1. SETUP THE BRAIN (2026 Modern SDK)
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def run_scout():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Act like a real person browsing from a laptop
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        
        print("Scouting RBI for the latest notifications...")
        
        try:
            # Go to the RBI page and wait for it to stop 'spinning'
            page.goto("https://www.rbi.org.in/Scripts/NotificationUser.aspx", wait_until="networkidle", timeout=60000)
            
            # SMART SEARCH: Find the first bolded notification link
            # 'sectionheader' is the tag RBI uses in 2026 for their link titles
            target_link = page.locator("a.sectionheader").first
            
            # Wait until it's actually visible on screen
            target_link.wait_for(state="visible", timeout=20000)
            
            title = target_link.inner_text()
            url = "https://www.rbi.org.in/Scripts/" + target_link.get_attribute("href")
            
            print(f"Target Found: {title}")

            # 2. THE ANALYST (Gemini)
            prompt = f"Analyze this RBI notification: '{title}'. Extract: 1. Effective Date, 2. Affected Entities, 3. Penalties. Format in 3 short bullets."
            
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )
            
            print("\n--- GOV-INTELLIGENCE REPORT ---")
            print(response.text)
            print("------------------------------")

        except Exception as e:
            print(f"Scout Error: {e}")
            # This 'takes a picture' so you can see why it failed
            page.screenshot(path="error_visual.png")
            
        browser.close()

if __name__ == "__main__":
    run_scout()