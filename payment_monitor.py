# payment_monitor.py
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from db import get_pending_payments, update_payment_status
from payment import verify_payment, PaymentError, get_payment_by_id
from error_handler import error_handler
from nowpayments_adapter import nowpayments_adapter

# Set up logging
logger = logging.getLogger(__name__)

class PaymentMonitor:
    """Background payment status monitor"""
    
    def __init__(self, check_interval: int = 300):  # 5 minutes default
        self.check_interval = check_interval
        self.running = False
        self.monitor_thread = None
        
    def start(self):
        """Start the payment monitor"""
        if self.running:
            logger.warning("Payment monitor is already running")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Payment monitor started")
    
    def stop(self):
        """Stop the payment monitor"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Payment monitor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                self._check_pending_payments()
                time.sleep(self.check_interval)
            except Exception as e:
                error_handler.log_error(e, {"action": "payment_monitor_loop"})
                time.sleep(60)  # Wait 1 minute on error before retrying
    
    def _check_pending_payments(self):
        """Check and update status of pending payments"""
        try:
            pending_payments = get_pending_payments()
            
            if not pending_payments:
                logger.debug("No pending payments to check")
                return
            
            logger.info(f"Checking {len(pending_payments)} pending payments")
            
            for payment in pending_payments:
                try:
                    self._check_single_payment(payment)
                except Exception as e:
                    error_handler.log_error(e, {
                        "payment_id": payment.get("payment_id"),
                        "action": "check_single_payment"
                    })
                    
        except Exception as e:
            error_handler.log_error(e, {"action": "check_pending_payments"})
    
    def _check_single_payment(self, payment: Dict[str, Any]):
        """Check status of a single payment"""
        payment_id = payment.get("payment_id")
        created_at = payment.get("created_at")
        
        if not payment_id:
            logger.error("Payment missing payment_id")
            return
        
        # Check if payment is too old (more than 24 hours)
        if created_at:
            try:
                created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                if datetime.now(created_time.tzinfo) - created_time > timedelta(hours=24):
                    logger.info(f"Payment {payment_id} is older than 24 hours, marking as expired")
                    update_payment_status(payment_id, "expired")
                    return
            except Exception as e:
                logger.warning(f"Could not parse payment creation time: {e}")
        
        try:
            # Verify payment status with NowPayments
            payment_info = verify_payment(payment_id)
            
            if payment_info:
                new_status = nowpayments_adapter.extract_payment_status(payment_info)
                if new_status and new_status != payment.get("status"):
                    logger.info(f"Payment {payment_id} status changed: {payment.get('status')} -> {new_status}")
                    update_payment_status(payment_id, new_status)
                    
                    # If payment is confirmed, update user balance
                    if new_status == "confirmed":
                        self._process_confirmed_payment(payment)
                        
        except PaymentError as e:
            logger.warning(f"Payment verification failed for {payment_id}: {e}")
        except Exception as e:
            error_handler.log_error(e, {
                "payment_id": payment_id,
                "action": "verify_payment"
            })
    
    def _process_confirmed_payment(self, payment: Dict[str, Any]):
        """Process a confirmed payment"""
        try:
            from db import update_balance
            from bot import bot
            
            user_id = payment.get("user_id")
            amount = payment.get("amount")
            payment_id = payment.get("payment_id")
            
            if user_id and amount:
                # Update user balance
                if update_balance(user_id, amount):
                    logger.info(f"Balance updated for user {user_id}: +{amount} USD")
                    
                    # Send notification to user
                    try:
                        bot.send_message(
                            user_id,
                            f"✅ Payment Confirmed!\n\n"
                            f"💰 Amount: {amount} USD\n"
                            f"🆔 Payment ID: {payment_id}\n\n"
                            f"Your balance has been updated successfully."
                        )
                    except Exception as e:
                        error_handler.log_error(e, {
                            "user_id": user_id,
                            "action": "send_payment_confirmation"
                        })
                else:
                    logger.error(f"Failed to update balance for user {user_id}")
                    
        except Exception as e:
            error_handler.log_error(e, {
                "payment_id": payment.get("payment_id"),
                "action": "process_confirmed_payment"
            })
    
    def force_check_payment(self, payment_id: str) -> bool:
        """
        Force check a specific payment status
        
        Args:
            payment_id: Payment ID to check
            
        Returns:
            bool: True if check was successful
        """
        try:
            payment = get_payment_by_id(payment_id)
            if not payment:
                logger.error(f"Payment {payment_id} not found")
                return False
            
            self._check_single_payment(payment)
            return True
            
        except Exception as e:
            error_handler.log_error(e, {
                "payment_id": payment_id,
                "action": "force_check_payment"
            })
            return False

# Global payment monitor instance
payment_monitor = PaymentMonitor()

def start_payment_monitor():
    """Start the payment monitor"""
    payment_monitor.start()

def stop_payment_monitor():
    """Stop the payment monitor"""
    payment_monitor.stop()

def check_payment_status(payment_id: str) -> bool:
    """Check status of a specific payment"""
    return payment_monitor.force_check_payment(payment_id) 