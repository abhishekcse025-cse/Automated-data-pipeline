import os
from playwright.sync_api import sync_playwright
from google import genai 

# Configure the genai client using an environment variable (recommended)
# Ensure you have set the GEMINI_API_KEY environment variable in your terminal
# e.g., export GEMINI_API_KEY="YOUR_API_KEY" 
client = genai.Client() 

def run_scout():
    with sync_playwright() as p:
        try:
            # ... (rest of your existing playwright code) ...
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
            
            # This line will now work correctly with the initialized client
            response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
            
            print("\n--- GOV-INTELLIGENCE REPORT ---") 
            print(response.text)
            print("------------------------------")

        except Exception as e:
            print(f"An error occurred: {e}")

# Call the function to run the script
run_scout()
