# config.py

# Database
DATABASE_NAME = 'bot.db'

# Telegram
BOT_TOKEN = "7742672497:AAH7HbJB9oQ8XmO-GIUs_fgbrN_HfNOeCpc"
ADMIN_USER_ID = 7480108404
GROUP_USERNAME = "lagit_airdropgroup"  # Updated group username

# NowPayments
NOWPAYMENTS_API_KEY = "30XSMW0-87RMFQM-G875626-9F7BZ7F"
NOWPAYMENTS_API_URL = "https://api.nowpayments.io/v1"
SUCCESS_URL = "https://escrow-bot-webhook.ngrok.io/webhook/success"
CANCEL_URL = "https://escrow-bot-webhook.ngrok.io/webhook/cancel"
WEBHOOK_SECRET = "EsDSoSYfTm5eEBLtbm0xOqM41laHLqou"  # Set this in production

# Bot Settings
MIN_DEPOSIT_AMOUNT = 10.0
DEPOSIT_FEE_PERCENTAGE = 3.0  # 3% fee
MIN_WITHDRAWAL_AMOUNT = 5.0

# Escrow Settings
ESCROW_FEE_PERCENTAGE = 2.0  # 2% escrow fee
MAX_DEAL_AMOUNT = 10000.0  # Maximum deal amount in USD
DEAL_TIMEOUT_HOURS = 72  # Auto-cancel deals after 72 hours

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "bot.log"