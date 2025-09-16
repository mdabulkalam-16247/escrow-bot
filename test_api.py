# test_api.py
import requests
import json
from datetime import datetime

# Configuration
API_KEY = "30XSMW0-87RMFQM-G875626-9F7BZ7F"
API_URL = "https://api.nowpayments.io/v1"
SUCCESS_URL = "https://escrow-bot-webhook.ngrok.io/webhook/success"
CANCEL_URL = "https://escrow-bot-webhook.ngrok.io/webhook/cancel"

def test_api_connection():
    """Test API connection and key validity"""
    print("🔍 Testing API Connection...")
    
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{API_URL}/status", headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ API Key is valid!")
            return True
        else:
            print("❌ API Key validation failed!")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_invoice_creation():
    """Test invoice creation with proper headers and body"""
    print("\n🔍 Testing Invoice Creation...")
    
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "price_amount": 10.0,
        "price_currency": "USD",
        "pay_currency": "usdttrc20",
        "order_id": f"test_{int(datetime.now().timestamp())}",
        "order_description": "Test deposit for Escrow Bot",
        "success_url": SUCCESS_URL,
        "cancel_url": CANCEL_URL,
        "is_fixed_rate": True,
        "is_fee_paid_by_user": True
    }
    
    print("📤 Request Headers:")
    for key, value in headers.items():
        print(f"  {key}: {value}")
    
    print("\n📤 Request Body:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(
            f"{API_URL}/invoice",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        print(f"\n📥 Response Body:")
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2))
            
            if response.status_code == 200:
                print("✅ Invoice created successfully!")
                return True
            else:
                print("❌ Invoice creation failed!")
                return False
                
        except json.JSONDecodeError:
            print(f"Raw response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request error: {e}")
        return False

def test_currencies():
    """Test supported currencies"""
    print("\n🔍 Testing Supported Currencies...")
    
    headers = {
        "x-api-key": API_KEY
    }
    
    try:
        response = requests.get(f"{API_URL}/currencies", headers=headers, timeout=30)
        
        if response.status_code == 200:
            currencies = response.json()
            print("✅ Supported currencies:")
            for currency in currencies.get('currencies', []):
                print(f"  - {currency}")
            
            # Check if usdttrc20 is supported
            if 'usdttrc20' in currencies.get('currencies', []):
                print("✅ usdttrc20 is supported!")
            else:
                print("❌ usdttrc20 is NOT supported!")
                print("Available USDT variants:")
                for currency in currencies.get('currencies', []):
                    if 'usdt' in currency.lower():
                        print(f"  - {currency}")
        else:
            print(f"❌ Failed to get currencies: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting currencies: {e}")

def test_minimum_amount():
    """Test minimum payment amount"""
    print("\n🔍 Testing Minimum Payment Amount...")
    
    headers = {
        "x-api-key": API_KEY
    }
    
    try:
        response = requests.get(f"{API_URL}/min-amount/usdttrc20", headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Minimum amount for usdttrc20: {data}")
        else:
            print(f"❌ Failed to get minimum amount: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting minimum amount: {e}")

if __name__ == "__main__":
    print("🚀 NowPayments API Testing Suite")
    print("=" * 50)
    
    # Test 1: API Connection
    if test_api_connection():
        # Test 2: Currencies
        test_currencies()
        
        # Test 3: Minimum Amount
        test_minimum_amount()
        
        # Test 4: Invoice Creation
        test_invoice_creation()
    else:
        print("❌ Cannot proceed with other tests due to API connection failure") 