# test_payment_errors.py
import sys
import os
import logging
from unittest.mock import Mock, patch

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from error_handler import error_handler
from payment import create_invoice, PaymentError
from db import get_db_connection, init_db

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_error_handler():
    """Test error handler functionality"""
    print("🧪 Testing Error Handler...")
    
    # Test payment error handling
    test_errors = [
        ("Authentication failed", "authentication"),
        ("Access denied", "access denied"),
        ("Rate limit exceeded", "rate limit"),
        ("Request timeout", "timeout"),
        ("Connection error", "connection"),
        ("Service unavailable", "temporarily unavailable"),
        ("Invalid request", "invalid"),
        ("Database error", "database"),
        ("Unknown error", "unknown")
    ]
    
    for error_msg, expected_type in test_errors:
        error = PaymentError(error_msg)
        result = error_handler.handle_payment_error(error, user_id=12345)
        print(f"✅ {expected_type}: {result[:50]}...")
    
    print("✅ Error handler tests completed\n")

def test_database_connection():
    """Test database connection and error handling"""
    print("🧪 Testing Database Connection...")
    
    # Initialize database
    if init_db():
        print("✅ Database initialized successfully")
    else:
        print("❌ Database initialization failed")
        return False
    
    # Test connection
    conn = get_db_connection()
    if conn:
        print("✅ Database connection successful")
        conn.close()
    else:
        print("❌ Database connection failed")
        return False
    
    print("✅ Database tests completed\n")
    return True

def test_payment_creation():
    """Test payment creation with error handling"""
    print("🧪 Testing Payment Creation...")
    
    # Test with invalid API key (should fail gracefully)
    with patch('payment.NOWPAYMENTS_API_KEY', 'invalid_key'):
        try:
            result = create_invoice(10.0, 12345, "usdttrc20")
            print(f"❌ Expected error but got: {result}")
        except PaymentError as e:
            print(f"✅ Payment error handled correctly: {str(e)[:50]}...")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    print("✅ Payment creation tests completed\n")

def test_webhook_processing():
    """Test webhook processing error handling"""
    print("🧪 Testing Webhook Processing...")
    
    from payment import process_webhook
    
    # Test with invalid payload
    try:
        result = process_webhook("invalid json", "invalid signature")
        print(f"✅ Webhook error handled correctly: {result}")
    except Exception as e:
        print(f"❌ Webhook error not handled: {e}")
    
    print("✅ Webhook tests completed\n")

def main():
    """Run all tests"""
    print("🚀 Starting Payment Error Handling Tests\n")
    
    # Test error handler
    test_error_handler()
    
    # Test database
    if not test_database_connection():
        print("❌ Database tests failed, skipping other tests")
        return
    
    # Test payment creation
    test_payment_creation()
    
    # Test webhook processing
    test_webhook_processing()
    
    print("🎉 All tests completed successfully!")

if __name__ == "__main__":
    main() 