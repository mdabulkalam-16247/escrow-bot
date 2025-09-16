# nowpayments_adapter.py
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class NowPaymentsAdapter:
    """Adapter for NowPayments API to handle different response formats"""
    
    @staticmethod
    def extract_payment_id(data: Dict[str, Any]) -> Optional[str]:
        """
        Extract payment ID from NowPayments API response
        
        Args:
            data: API response data
            
        Returns:
            Payment ID or None if not found
        """
        # Try both old and new API formats
        payment_id = data.get("payment_id") or data.get("id")
        
        if payment_id:
            logger.debug(f"Extracted payment ID: {payment_id}")
            return payment_id
        else:
            logger.error(f"No payment ID found in response: {data}")
            return None
    
    @staticmethod
    def extract_payment_status(data: Dict[str, Any]) -> Optional[str]:
        """
        Extract payment status from NowPayments API response
        
        Args:
            data: API response data
            
        Returns:
            Payment status or None if not found
        """
        # Try both old and new API formats
        status = data.get("payment_status") or data.get("status")
        
        if status:
            logger.debug(f"Extracted payment status: {status}")
            return status
        else:
            logger.warning(f"No payment status found in response: {data}")
            return None
    
    @staticmethod
    def extract_invoice_url(data: Dict[str, Any]) -> Optional[str]:
        """
        Extract invoice URL from NowPayments API response
        
        Args:
            data: API response data
            
        Returns:
            Invoice URL or None if not found
        """
        invoice_url = data.get("invoice_url")
        
        if invoice_url:
            logger.debug(f"Extracted invoice URL: {invoice_url}")
            return invoice_url
        else:
            logger.error(f"No invoice URL found in response: {data}")
            return None
    
    @staticmethod
    def validate_invoice_response(data: Dict[str, Any]) -> tuple[bool, str, Optional[str], Optional[str]]:
        """
        Validate invoice creation response
        
        Args:
            data: API response data
            
        Returns:
            Tuple of (is_valid, error_message, payment_id, invoice_url)
        """
        payment_id = NowPaymentsAdapter.extract_payment_id(data)
        invoice_url = NowPaymentsAdapter.extract_invoice_url(data)
        
        if not payment_id:
            return False, "Missing payment ID in response", None, None
        
        if not invoice_url:
            return False, "Missing invoice URL in response", None, None
        
        return True, "", payment_id, invoice_url
    
    @staticmethod
    def validate_webhook_payload(data: Dict[str, Any]) -> tuple[bool, str, Optional[str], Optional[str]]:
        """
        Validate webhook payload
        
        Args:
            data: Webhook payload data
            
        Returns:
            Tuple of (is_valid, error_message, payment_id, payment_status)
        """
        payment_id = NowPaymentsAdapter.extract_payment_id(data)
        payment_status = NowPaymentsAdapter.extract_payment_status(data)
        
        if not payment_id:
            return False, "Missing payment ID in webhook payload", None, None
        
        if not payment_status:
            return False, "Missing payment status in webhook payload", None, None
        
        return True, "", payment_id, payment_status
    
    @staticmethod
    def format_payment_info(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format payment information for consistent use
        
        Args:
            data: Raw API response data
            
        Returns:
            Formatted payment information
        """
        return {
            "payment_id": NowPaymentsAdapter.extract_payment_id(data),
            "status": NowPaymentsAdapter.extract_payment_status(data),
            "invoice_url": NowPaymentsAdapter.extract_invoice_url(data),
            "amount": data.get("price_amount"),
            "currency": data.get("pay_currency"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "raw_data": data  # Keep original data for debugging
        }
    
    @staticmethod
    def log_response_info(data: Dict[str, Any], operation: str):
        """
        Log response information for debugging
        
        Args:
            data: API response data
            operation: Operation being performed
        """
        payment_id = NowPaymentsAdapter.extract_payment_id(data)
        status = NowPaymentsAdapter.extract_payment_status(data)
        
        logger.info(f"NowPayments {operation} - Payment ID: {payment_id}, Status: {status}")
        logger.debug(f"Full response data: {data}")

# Global adapter instance
nowpayments_adapter = NowPaymentsAdapter() 