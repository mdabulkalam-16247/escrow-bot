# payment_config.py
import os
from typing import Dict, Any

# Payment Service Configuration
PAYMENT_CONFIG = {
    # NowPayments API settings
    "api_timeout": 30,  # seconds
    "max_retries": 3,
    "retry_delay": 2,  # seconds
    "exponential_backoff": True,
    
    # Payment limits
    "min_amount": 10.0,  # USD
    "max_amount": 10000.0,  # USD
    "min_withdrawal": 5.0,  # USD
    
    # Fee settings
    "deposit_fee_percentage": 3.0,
    "escrow_fee_percentage": 2.0,
    
    # Payment statuses
    "valid_statuses": [
        'pending',
        'confirming', 
        'confirmed',
        'failed',
        'cancelled',
        'expired'
    ],
    
    # Supported currencies
    "supported_currencies": [
        "usdttrc20",
        "btc",
        "eth",
        "ltc",
        "bch",
        "xrp",
        "ada",
        "dot",
        "link",
        "uni"
    ],
    
    # Webhook settings
    "webhook_timeout": 10,  # seconds
    "webhook_retries": 2,
    
    # Payment expiration
    "payment_expiry_hours": 24,
    
    # Monitoring settings
    "monitor_interval": 300,  # 5 minutes
    "max_pending_age_hours": 24,
}

# Error handling configuration
ERROR_CONFIG = {
    # Error message templates
    "error_messages": {
        "payment_service_unavailable": "Payment service is temporarily unavailable. Please try again later.",
        "network_error": "Network error. Please check your internet connection and try again.",
        "invalid_amount": "Invalid amount. Please enter a valid number.",
        "insufficient_balance": "Insufficient balance for this transaction.",
        "payment_not_found": "Payment not found or has expired.",
        "database_error": "Database error occurred. Please try again or contact support.",
        "authentication_error": "Payment service authentication failed. Please contact support.",
        "rate_limit_error": "Too many requests. Please try again in a few minutes.",
        "timeout_error": "Request timed out. Please try again.",
        "unknown_error": "An unexpected error occurred. Please try again or contact support."
    },
    
    # Error logging levels
    "log_levels": {
        "payment_error": "ERROR",
        "network_error": "WARNING", 
        "database_error": "ERROR",
        "webhook_error": "ERROR",
        "validation_error": "INFO",
        "timeout_error": "WARNING"
    },
    
    # Error recovery settings
    "retry_on_errors": [
        "network_error",
        "timeout_error",
        "rate_limit_error"
    ],
    
    "max_retry_attempts": 3,
    "retry_delay_seconds": 5,
}

# Database configuration
DB_CONFIG = {
    "connection_timeout": 20.0,
    "max_retries": 3,
    "retry_delay": 1,  # seconds
    "enable_foreign_keys": True,
    "journal_mode": "WAL",  # Write-Ahead Logging for better concurrency
    "synchronous": "NORMAL",  # Balance between safety and performance
    "cache_size": -64000,  # 64MB cache
    "temp_store": "MEMORY",  # Store temp tables in memory
}

# Monitoring configuration
MONITOR_CONFIG = {
    "check_interval": 300,  # 5 minutes
    "max_pending_age": 24,  # hours
    "batch_size": 50,  # payments per batch
    "enable_notifications": True,
    "notification_cooldown": 3600,  # 1 hour between notifications
}

def get_payment_config(key: str, default: Any = None) -> Any:
    """Get payment configuration value"""
    return PAYMENT_CONFIG.get(key, default)

def get_error_config(key: str, default: Any = None) -> Any:
    """Get error configuration value"""
    return ERROR_CONFIG.get(key, default)

def get_db_config(key: str, default: Any = None) -> Any:
    """Get database configuration value"""
    return DB_CONFIG.get(key, default)

def get_monitor_config(key: str, default: Any = None) -> Any:
    """Get monitoring configuration value"""
    return MONITOR_CONFIG.get(key, default)

def get_error_message(error_type: str) -> str:
    """Get error message for specific error type"""
    messages = ERROR_CONFIG.get("error_messages", {})
    return messages.get(error_type, messages.get("unknown_error", "An error occurred."))

def is_retryable_error(error_type: str) -> bool:
    """Check if error type is retryable"""
    retryable_errors = ERROR_CONFIG.get("retry_on_errors", [])
    return error_type in retryable_errors

def get_log_level(error_type: str) -> str:
    """Get log level for specific error type"""
    log_levels = ERROR_CONFIG.get("log_levels", {})
    return log_levels.get(error_type, "ERROR")

# Environment-specific overrides
if os.getenv("ENVIRONMENT") == "production":
    # Production settings
    PAYMENT_CONFIG["api_timeout"] = 60
    PAYMENT_CONFIG["max_retries"] = 5
    DB_CONFIG["synchronous"] = "FULL"  # Maximum safety
    MONITOR_CONFIG["check_interval"] = 180  # 3 minutes
elif os.getenv("ENVIRONMENT") == "development":
    # Development settings
    PAYMENT_CONFIG["api_timeout"] = 10
    PAYMENT_CONFIG["max_retries"] = 1
    DB_CONFIG["synchronous"] = "OFF"  # Maximum performance
    MONITOR_CONFIG["check_interval"] = 600  # 10 minutes 