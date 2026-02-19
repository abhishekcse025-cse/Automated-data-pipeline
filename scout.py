import os
import google.generativeai as genai
from playwright.sync_api import sync_playwright

# 1. SETUP THE BRAIN
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

def run_scout():
    with sync_playwright() as p:
        # Open a "Ghost" Browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Go to the RBI Notifications page (Example)
        print("Scouting RBI...")
        page.goto("https://www.rbi.org.in/Scripts/NotificationUser.aspx")
        
        # Grab the first notification title and link
        first_link = page.locator(".table-g-notif a").first
        title = first_link.inner_text()
        url = "https://www.rbi.org.in/Scripts/" + first_link.get_attribute("href")
        
        print(f"Found: {title}")

        # 2. THE ANALYST (Gemini)
        prompt = f"""
        You are a Senior Compliance Officer. Analyze this regulation title: '{title}' 
        at this URL: {url}
        Extract:
        1. Effective Date
        2. Who it affects (Entities)
        3. Penalty for non-compliance (if mentioned)
        Format: 3 simple bullet points.
        """
        
        response = model.generate_content(prompt)
        print("--- ANALYSIS ---")
        print(response.text)
        
        browser.close()

if __name__ == "__main__":
    run_scout()