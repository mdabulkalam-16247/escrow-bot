# webhook.py
import logging
from flask import Flask, request, jsonify, redirect
from payment import process_webhook
from config import WEBHOOK_SECRET

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/webhook/nowpayments', methods=['POST'])
def nowpayments_webhook():
    """
    Handle NowPayments webhook notifications with improved error handling
    """
    try:
        # Log incoming webhook
        logger.info("Received NowPayments webhook")
        
        # Get the raw payload
        payload = request.get_data(as_text=True)
        
        if not payload:
            logger.error("Empty webhook payload received")
            return jsonify({"error": "Empty payload"}), 400
        
        # Log payload for debugging (remove sensitive data in production)
        logger.debug(f"Webhook payload: {payload[:200]}...")
        
        # Get the signature from headers
        signature = request.headers.get('x-nowpayments-sig')
        
        if not signature:
            logger.error("No signature found in webhook headers")
            return jsonify({"error": "No signature"}), 400
        
        # Log signature for debugging
        logger.debug(f"Webhook signature: {signature[:20]}...")
        
        # Process the webhook
        try:
            if process_webhook(payload, signature):
                logger.info("Webhook processed successfully")
                return jsonify({"status": "success"}), 200
            else:
                logger.error("Failed to process webhook")
                return jsonify({"error": "Processing failed"}), 400
                
        except Exception as e:
            logger.error(f"Error during webhook processing: {e}")
            return jsonify({"error": "Processing error"}), 500
            
    except Exception as e:
        logger.error(f"Webhook handler error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/webhook/success', methods=['GET'])
def success_webhook():
    """Handle successful payment redirect"""
    logger.info("Payment success webhook called")
    return jsonify({
        "status": "success",
        "message": "Payment completed successfully"
    }), 200

@app.route('/webhook/cancel', methods=['GET'])
def cancel_webhook():
    """Handle cancelled payment redirect"""
    logger.info("Payment cancelled webhook called")
    return jsonify({
        "status": "cancelled",
        "message": "Payment was cancelled"
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        "message": "Escrow Bot Webhook Handler",
        "status": "running",
        "webhook_url": "/webhook/nowpayments",
        "success_url": "/webhook/success",
        "cancel_url": "/webhook/cancel"
    }), 200

if __name__ == '__main__':
    logger.info("Starting webhook server...")
    app.run(host='0.0.0.0', port=5000, debug=False) 