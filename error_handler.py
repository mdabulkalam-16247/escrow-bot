# error_handler.py
import logging
import traceback
from typing import Optional, Dict, Any
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

class ErrorHandler:
    """Centralized error handling for the escrow bot"""
    
    @staticmethod
    def handle_payment_error(error: Exception, user_id: Optional[int] = None, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Handle payment-related errors and return user-friendly message
        
        Args:
            error: The exception that occurred
            user_id: Telegram user ID (optional)
            context: Additional context information (optional)
        
        Returns:
            str: User-friendly error message
        """
        error_msg = str(error)
        
        # Log the error with context
        log_context = f"User: {user_id}, " if user_id else ""
        log_context += f"Context: {context}, " if context else ""
        logger.error(f"{log_context}Payment Error: {error_msg}")
        
        # Categorize errors and return appropriate messages
        if "authentication" in error_msg.lower() or "401" in error_msg:
            return "❌ Payment service authentication failed. Please contact support: @Abul_kalam2025"
        
        elif "access denied" in error_msg.lower() or "403" in error_msg:
            return "❌ Payment service access denied. Please contact support: @Abul_kalam2025"
        
        elif "rate limit" in error_msg.lower() or "429" in error_msg or "busy" in error_msg.lower():
            return "❌ Payment service is busy. Please try again in a few minutes."
        
        elif "timeout" in error_msg.lower():
            return "❌ Payment request timed out. Please check your internet connection and try again."
        
        elif "connection" in error_msg.lower() or "network" in error_msg.lower():
            return "❌ Network error. Please check your internet connection and try again."
        
        elif "temporarily unavailable" in error_msg.lower() or "500" in error_msg:
            return "❌ Payment service is temporarily unavailable. Please try again later."
        
        elif "invalid" in error_msg.lower():
            return "❌ Invalid payment request. Please try again with valid information."
        
        elif "database" in error_msg.lower():
            return "❌ Database error occurred. Please try again or contact support: @Abul_kalam2025"
        
        else:
            return f"❌ Payment Error: {error_msg}\n\nPlease try again or contact support: @Abul_kalam2025"
    
    @staticmethod
    def handle_database_error(error: Exception, operation: str, user_id: Optional[int] = None) -> str:
        """
        Handle database-related errors
        
        Args:
            error: The exception that occurred
            operation: Description of the operation being performed
            user_id: Telegram user ID (optional)
        
        Returns:
            str: User-friendly error message
        """
        error_msg = str(error)
        
        logger.error(f"Database Error in {operation} for user {user_id}: {error_msg}")
        
        if "database is locked" in error_msg.lower():
            return "❌ Database is temporarily busy. Please try again in a moment."
        
        elif "no such table" in error_msg.lower():
            return "❌ Database configuration error. Please contact support: @Abul_kalam2025"
        
        elif "integrity" in error_msg.lower():
            return "❌ Data integrity error. Please try again or contact support: @Abul_kalam2025"
        
        else:
            return "❌ Database error occurred. Please try again or contact support: @Abul_kalam2025"
    
    @staticmethod
    def handle_webhook_error(error: Exception, payment_id: Optional[str] = None) -> str:
        """
        Handle webhook processing errors
        
        Args:
            error: The exception that occurred
            payment_id: Payment ID being processed (optional)
        
        Returns:
            str: Error message for logging
        """
        error_msg = str(error)
        
        log_context = f"Payment ID: {payment_id}, " if payment_id else ""
        logger.error(f"{log_context}Webhook Error: {error_msg}")
        
        return f"Webhook processing failed: {error_msg}"
    
    @staticmethod
    def handle_telegram_error(error: Exception, user_id: Optional[int] = None, action: str = "message") -> str:
        """
        Handle Telegram API errors
        
        Args:
            error: The exception that occurred
            user_id: Telegram user ID (optional)
            action: Action being performed (message, callback, etc.)
        
        Returns:
            str: Error message for logging
        """
        error_msg = str(error)
        
        log_context = f"User: {user_id}, Action: {action}, " if user_id else f"Action: {action}, "
        logger.error(f"{log_context}Telegram Error: {error_msg}")
        
        return f"Telegram API error in {action}: {error_msg}"
    
    @staticmethod
    def log_error(error: Exception, context: Optional[Dict[str, Any]] = None, level: str = "ERROR"):
        """
        Log errors with context information
        
        Args:
            error: The exception that occurred
            context: Additional context information (optional)
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        error_msg = str(error)
        error_traceback = traceback.format_exc()
        
        # Build log message
        log_msg = f"Error: {error_msg}"
        if context:
            log_msg += f"\nContext: {context}"
        log_msg += f"\nTraceback:\n{error_traceback}"
        
        # Log with appropriate level
        if level.upper() == "DEBUG":
            logger.debug(log_msg)
        elif level.upper() == "INFO":
            logger.info(log_msg)
        elif level.upper() == "WARNING":
            logger.warning(log_msg)
        elif level.upper() == "CRITICAL":
            logger.critical(log_msg)
        else:
            logger.error(log_msg)
    
    @staticmethod
    def create_error_report(error: Exception, user_id: Optional[int] = None, 
                          context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a detailed error report for debugging
        
        Args:
            error: The exception that occurred
            user_id: Telegram user ID (optional)
            context: Additional context information (optional)
        
        Returns:
            Dict containing error report
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "user_id": user_id,
            "context": context,
            "traceback": traceback.format_exc()
        }

# Global error handler instance
error_handler = ErrorHandler() 