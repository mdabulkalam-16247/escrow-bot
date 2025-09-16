# test_nowpayments_adapter.py
import sys
import os
import logging

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from nowpayments_adapter import nowpayments_adapter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_adapter():
    """Test NowPayments adapter functionality"""
    print("🧪 Testing NowPayments Adapter...")
    
    # Test data from your actual API response
    test_response = {
        'id': '4957197073',
        'token_id': '5603669597',
        'order_id': 'user_7480108404_1751204217',
        'order_description': 'Deposit for Escrow Bot - User 7480108404',
        'price_amount': '12.36',
        'price_currency': 'USD',
        'pay_currency': 'USDTTRC20',
        'ipn_callback_url': None,
        'invoice_url': 'https://nowpayments.io/payment/?iid=4957197073',
        'success_url': 'https://escrow-bot-webhook.ngrok.io/webhook/success',
        'cancel_url': 'https://escrow-bot-webhook.ngrok.io/webhook/cancel',
        'customer_email': None,
        'partially_paid_url': None,
        'payout_currency': None,
        'created_at': '2025-06-29T13:36:57.622Z',
        'updated_at': '2025-06-29T13:36:57.622Z',
        'is_fixed_rate': True,
        'is_fee_paid_by_user': True,
        'source': None,
        'collect_user_data': False
    }
    
    # Test payment ID extraction
    payment_id = nowpayments_adapter.extract_payment_id(test_response)
    print(f"✅ Extracted Payment ID: {payment_id}")
    
    # Test invoice URL extraction
    invoice_url = nowpayments_adapter.extract_invoice_url(test_response)
    print(f"✅ Extracted Invoice URL: {invoice_url}")
    
    # Test invoice response validation
    is_valid, error_msg, extracted_payment_id, extracted_invoice_url = nowpayments_adapter.validate_invoice_response(test_response)
    print(f"✅ Invoice Response Valid: {is_valid}")
    if not is_valid:
        print(f"❌ Error: {error_msg}")
    
    # Test webhook payload (simulated)
    webhook_payload = {
        'id': '4957197073',
        'payment_status': 'confirmed',
        'price_amount': '12.36',
        'pay_currency': 'USDTTRC20'
    }
    
    # Test webhook payload validation
    is_valid, error_msg, webhook_payment_id, webhook_status = nowpayments_adapter.validate_webhook_payload(webhook_payload)
    print(f"✅ Webhook Payload Valid: {is_valid}")
    if not is_valid:
        print(f"❌ Error: {error_msg}")
    else:
        print(f"✅ Webhook Payment ID: {webhook_payment_id}")
        print(f"✅ Webhook Status: {webhook_status}")
    
    # Test payment info formatting
    formatted_info = nowpayments_adapter.format_payment_info(test_response)
    print(f"✅ Formatted Payment Info: {formatted_info}")
    
    print("✅ NowPayments adapter tests completed\n")

def test_old_api_format():
    """Test old API format compatibility"""
    print("🧪 Testing Old API Format Compatibility...")
    
    # Old API format response
    old_format_response = {
        'payment_id': 'old_payment_123',
        'payment_status': 'pending',
        'invoice_url': 'https://old-api.example.com/pay/123',
        'price_amount': '10.00',
        'pay_currency': 'BTC'
    }
    
    # Test payment ID extraction
    payment_id = nowpayments_adapter.extract_payment_id(old_format_response)
    print(f"✅ Old Format Payment ID: {payment_id}")
    
    # Test payment status extraction
    status = nowpayments_adapter.extract_payment_status(old_format_response)
    print(f"✅ Old Format Status: {status}")
    
    # Test validation
    is_valid, error_msg, extracted_payment_id, extracted_invoice_url = nowpayments_adapter.validate_invoice_response(old_format_response)
    print(f"✅ Old Format Valid: {is_valid}")
    
    print("✅ Old API format tests completed\n")

def test_error_cases():
    """Test error handling cases"""
    print("🧪 Testing Error Cases...")
    
    # Missing payment ID
    invalid_response = {
        'invoice_url': 'https://example.com/pay/123',
        'price_amount': '10.00'
    }
    
    payment_id = nowpayments_adapter.extract_payment_id(invalid_response)
    print(f"✅ Missing Payment ID Result: {payment_id}")
    
    # Missing invoice URL
    invalid_response2 = {
        'id': 'test_123',
        'price_amount': '10.00'
    }
    
    invoice_url = nowpayments_adapter.extract_invoice_url(invalid_response2)
    print(f"✅ Missing Invoice URL Result: {invoice_url}")
    
    # Test validation with missing fields
    is_valid, error_msg, _, _ = nowpayments_adapter.validate_invoice_response(invalid_response)
    print(f"✅ Invalid Response Valid: {is_valid}")
    print(f"✅ Error Message: {error_msg}")
    
    print("✅ Error case tests completed\n")

def main():
    """Run all tests"""
    print("🚀 Starting NowPayments Adapter Tests\n")
    
    # Test new API format
    test_adapter()
    
    # Test old API format compatibility
    test_old_api_format()
    
    # Test error cases
    test_error_cases()
    
    print("🎉 All NowPayments adapter tests completed successfully!")

if __name__ == "__main__":
    main() 