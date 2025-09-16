# payment.py
import requests
import logging
import hashlib
import hmac
import json
import time
from datetime import datetime
from config import NOWPAYMENTS_API_KEY, NOWPAYMENTS_API_URL, SUCCESS_URL, CANCEL_URL, WEBHOOK_SECRET
from db import add_payment, update_payment_status, update_balance, get_user
from nowpayments_adapter import nowpayments_adapter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaymentError(Exception):
    """Custom exception for payment errors"""
    pass

def create_invoice(amount, user_id, currency="usdttrc20"):
    """
    Create a payment invoice using NowPayments API
    
    Args:
        amount (float): Payment amount in USD
        user_id (int): Telegram user ID
        currency (str): Payment currency (default: usdttrc20)
    
    Returns:
        dict: Invoice data with payment_id and invoice_url
    """
    headers = {
        "x-api-key": NOWPAYMENTS_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "price_amount": abs(float(amount)),
        "price_currency": "USD",
        "pay_currency": currency.lower(),  # Ensure lowercase
        "order_id": f"user_{user_id}_{int(datetime.now().timestamp())}",
        "order_description": f"Deposit for Escrow Bot - User {user_id}",
        "success_url": SUCCESS_URL,
        "cancel_url": CANCEL_URL,
        "is_fixed_rate": True,
        "is_fee_paid_by_user": True
    }

    # Retry logic for network issues
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Creating invoice for user {user_id}, attempt {attempt + 1}/{max_retries}")
            
            response = requests.post(
                f"{NOWPAYMENTS_API_URL}/invoice", 
                headers=headers, 
                json=payload,
                timeout=30
            )
            
            # Log response for debugging
            logger.info(f"NowPayments API response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Use adapter to validate response
                is_valid, error_msg, payment_id, invoice_url = nowpayments_adapter.validate_invoice_response(data)
                
                if is_valid and payment_id and invoice_url:
                    # Save payment record to database
                    if add_payment(user_id, payment_id, amount, currency, invoice_url):
                        logger.info(f"Invoice created successfully for user {user_id}: {payment_id}")
                        return {
                            "payment_id": payment_id,
                            "invoice_url": invoice_url,
                            "amount": amount,
                            "currency": currency
                        }
                    else:
                        raise PaymentError("Failed to save payment record to database. Please try again.")
                else:
                    logger.error(f"Invalid response from payment service: {error_msg}")
                    logger.error(f"Response data: {data}")
                    raise PaymentError(error_msg)
                    
            elif response.status_code == 401:
                raise PaymentError("Payment service authentication failed. Please contact support.")
            elif response.status_code == 403:
                raise PaymentError("Payment service access denied. Please contact support.")
            elif response.status_code == 429:
                if attempt < max_retries - 1:
                    logger.warning(f"Rate limited, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    raise PaymentError("Payment service is busy. Please try again in a few minutes.")
            elif response.status_code >= 500:
                if attempt < max_retries - 1:
                    logger.warning(f"Server error {response.status_code}, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    raise PaymentError("Payment service is temporarily unavailable. Please try again later.")
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', f'Payment service error: {response.status_code}')
                except:
                    error_msg = f"Payment service error: {response.status_code}"
                
                logger.error(f"NowPayments API error: {response.status_code} - {response.text}")
                raise PaymentError(error_msg)
                
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                logger.warning(f"Request timeout, retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2
                continue
            else:
                raise PaymentError("Payment service request timed out. Please try again.")
                
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                logger.warning(f"Connection error, retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2
                continue
            else:
                raise PaymentError("Cannot connect to payment service. Please check your internet connection.")
                
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                logger.warning(f"Network error: {e}, retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2
                continue
            else:
                raise PaymentError(f"Network error while creating payment: {str(e)}")
                
        except Exception as e:
            logger.error(f"Unexpected error while creating invoice: {e}")
            raise PaymentError(f"Unexpected error while creating payment: {str(e)}")
    
    # If we get here, all retries failed
    raise PaymentError("Failed to create payment after multiple attempts. Please try again later.")

def verify_payment(payment_id):
    """
    Verify payment status using NowPayments API
    
    Args:
        payment_id (str): Payment ID from NowPayments
    
    Returns:
        dict: Payment status information
    """
    headers = {
        "x-api-key": NOWPAYMENTS_API_KEY
    }

    try:
        response = requests.get(
            f"{NOWPAYMENTS_API_URL}/payment/{payment_id}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            # Use adapter to extract payment status
            payment_status = nowpayments_adapter.extract_payment_status(data)
            logger.info(f"Payment verification successful for {payment_id}: {payment_status}")
            return data
        else:
            error_msg = f"NowPayments API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise PaymentError(error_msg)
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error while verifying payment: {e}"
        logger.error(error_msg)
        raise PaymentError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error while verifying payment: {e}"
        logger.error(error_msg)
        raise PaymentError(error_msg)

def process_webhook(payload, signature):
    """
    Process webhook from NowPayments with improved error handling and validation
    
    Args:
        payload (str): Raw webhook payload
        signature (str): Webhook signature for verification
    
    Returns:
        bool: True if webhook processed successfully
    """
    try:
        # Verify webhook signature first
        if not verify_webhook_signature(payload, signature):
            logger.error("Invalid webhook signature - potential security threat")
            return False
        
        # Parse JSON payload
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook payload: {e}")
            return False
        
        # Use adapter to validate webhook payload
        is_valid, error_msg, payment_id, payment_status = nowpayments_adapter.validate_webhook_payload(data)
        
        if not is_valid:
            logger.error(f"Invalid webhook payload: {error_msg}")
            return False
        
        logger.info(f"Processing webhook for payment {payment_id}: {payment_status}")
        
        # Get existing payment record
        existing_payment = get_payment_by_id(payment_id)
        if not existing_payment:
            logger.error(f"Payment {payment_id} not found in database")
            return False
        
        # Check if status has already been processed
        if existing_payment.get("status") == payment_status:
            logger.info(f"Payment {payment_id} status already {payment_status}, skipping")
            return True
        
        # Update payment status in database with transaction safety
        if not update_payment_status(payment_id, payment_status):
            logger.error(f"Failed to update payment status for {payment_id}")
            return False
        
        # Process confirmed payments
        if payment_status == "confirmed":
            user_id = existing_payment.get("user_id")
            amount = existing_payment.get("amount")
            
            if user_id and amount:
                logger.info(f"Processing confirmed payment: user {user_id}, amount {amount}")
                
                # Update user balance with transaction safety
                if update_balance(user_id, amount):
                    logger.info(f"Balance updated successfully for user {user_id}: +{amount} USD")
                    
                    # Send notification to user (optional)
                    try:
                        from bot import bot
                        bot.send_message(
                            user_id,
                            f"✅ Payment Confirmed!\n\n"
                            f"💰 Amount: {amount} USD\n"
                            f"🆔 Payment ID: {payment_id}\n\n"
                            f"Your balance has been updated successfully."
                        )
                    except Exception as e:
                        logger.warning(f"Failed to send payment confirmation to user {user_id}: {e}")
                else:
                    logger.error(f"Failed to update balance for user {user_id}")
                    return False
            else:
                logger.error(f"Missing user_id or amount in payment {payment_id}")
                return False
        
        # Process failed/cancelled payments
        elif payment_status in ["failed", "cancelled", "expired"]:
            logger.info(f"Payment {payment_id} {payment_status}")
            # Could add logic here to handle failed payments (e.g., refund processing)
        
        logger.info(f"Webhook processed successfully for payment {payment_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return False

def verify_webhook_signature(payload, signature):
    """
    Verify webhook signature from NowPayments
    
    Args:
        payload (str): Raw webhook payload
        signature (str): Webhook signature
    
    Returns:
        bool: True if signature is valid
    """
    try:
        if not WEBHOOK_SECRET:
            logger.warning("WEBHOOK_SECRET not configured, skipping signature verification")
            return True
        
        # Create expected signature
        expected_signature = hmac.new(
            WEBHOOK_SECRET.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {e}")
        return False

def get_payment_by_id(payment_id):
    """
    Get payment information from database
    
    Args:
        payment_id (str): Payment ID
    
    Returns:
        dict: Payment information or None
    """
    from db import get_db_connection
    
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,))
        result = c.fetchone()
        return dict(result) if result else None
    except Exception as e:
        logger.error(f"Error getting payment {payment_id}: {e}")
        return None
    finally:
        conn.close()

def get_payment_status(payment_id):
    """
    Get payment status from database
    
    Args:
        payment_id (str): Payment ID
    
    Returns:
        str: Payment status or None
    """
    payment_data = get_payment_by_id(payment_id)
    return payment_data.get("status") if payment_data else None

def refund_payment(payment_id, reason="User request"):
    """
    Request refund for a payment
    
    Args:
        payment_id (str): Payment ID
        reason (str): Refund reason
    
    Returns:
        bool: True if refund request successful
    """
    headers = {
        "x-api-key": NOWPAYMENTS_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "payment_id": payment_id,
        "refund_type": "full",
        "reason": reason
    }

    try:
        response = requests.post(
            f"{NOWPAYMENTS_API_URL}/refund",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Refund requested for payment {payment_id}: {data}")
            return True
        else:
            error_msg = f"NowPayments API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return False
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error while requesting refund: {e}"
        logger.error(error_msg)
        return False
    except Exception as e:
        error_msg = f"Unexpected error while requesting refund: {e}"
        logger.error(error_msg)
        return False

def get_minimum_payment_amount():
    """Get minimum payment amount from NowPayments"""
    return 10.0  # NowPayments minimum is usually $10

def get_supported_currencies():
    """Get list of supported payment currencies"""
    return [
        "USDTTRC20",
        "BTC",
        "ETH",
        "LTC",
        "BCH",
        "XRP",
        "ADA",
        "DOT",
        "LINK",
        "UNI"
    ]