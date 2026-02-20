import os
import requests

def send_test():
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    print(f"Attempting to send message to Chat ID: {chat_id}")
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": "✅ CONNECTION TEST: Your GitHub Cloud is talking to Telegram!"}
    
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("SUCCESS: Check your Telegram!")
        else:
            print(f"FAILED: Telegram said: {response.text}")
    except Exception as e:
        print(f"ERROR: Could not connect to Telegram: {e}")

if __name__ == "__main__":
    send_test()