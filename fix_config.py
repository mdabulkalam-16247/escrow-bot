import re

def update_ngrok_urls(new_url):
    """Update ngrok URLs in config.py"""
    try:
        # Read current config
        with open('config.py', 'r') as f:
            content = f.read()
        
        # Update URLs
        content = re.sub(
            r'SUCCESS_URL = "https://[^"]*"',
            f'SUCCESS_URL = "{new_url}/webhook/success"',
            content
        )
        content = re.sub(
            r'CANCEL_URL = "https://[^"]*"',
            f'CANCEL_URL = "{new_url}/webhook/cancel"',
            content
        )
        
        # Write updated config
        with open('config.py', 'w') as f:
            f.write(content)
        
        print(f"✅ Updated config.py with new ngrok URL: {new_url}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating config: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Ngrok URL Updater")
    print("=" * 30)
    
    # Get new URL from user
    new_url = input("Enter your new ngrok URL (e.g., https://abc123.ngrok.io): ").strip()
    
    if new_url.startswith("https://"):
        update_ngrok_urls(new_url)
    else:
        print("❌ Please enter a valid HTTPS URL") 