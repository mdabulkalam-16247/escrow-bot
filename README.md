# Escrow Bot - Telegram Bot

A secure escrow service bot for Telegram that facilitates safe transactions between buyers and sellers.

## Features

- 🔐 **Secure Escrow Service** - Funds held safely until deal completion
- 💳 **Multiple Payment Methods** - Support for USDT, Bitcoin, Ethereum, and more
- 👤 **User Management** - Profile management and transaction history
- 📊 **Admin Panel** - Comprehensive admin controls and monitoring
- 🔔 **Real-time Notifications** - Payment confirmations and deal updates
- 📈 **Transaction Tracking** - Complete history of all transactions

## Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- Telegram Bot Token (from @BotFather)
- NowPayments API Key
- Domain with SSL (for webhooks)

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd escrow_bot_code

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Edit `config.py` with your settings:

```python
# Telegram Bot Token
BOT_TOKEN = "your_bot_token_here"

# NowPayments Configuration
NOWPAYMENTS_API_KEY = "your_nowpayments_api_key"
WEBHOOK_SECRET = "your_webhook_secret"

# Admin User ID
ADMIN_USER_ID = your_admin_user_id

# Group Username
GROUP_USERNAME = "your_group_username"
```

### 4. Database Setup

The database will be automatically created when you run the bot for the first time.

### 5. Running the Bot

```bash
# Start the main bot
python bot.py

# Start webhook handler (in separate terminal)
python webhook.py
```

## File Structure

```
escrow_bot_code/
├── bot.py              # Main bot logic
├── config.py           # Configuration settings
├── db.py              # Database operations
├── payment.py         # Payment processing
├── utils.py           # Utility functions
├── webhook.py         # Webhook handler
├── requirements.txt   # Python dependencies
├── README.md          # This file
└── bot.db            # SQLite database (auto-generated)
```

## Database Schema

### Users Table
- `user_id` - Telegram user ID (Primary Key)
- `username` - Telegram username
- `first_name` - User's first name
- `balance` - Current balance in USDT
- `deals_done` - Number of completed deals
- `created_at` - Account creation timestamp
- `updated_at` - Last update timestamp

### Deals Table
- `id` - Deal ID (Primary Key)
- `buyer_id` - Buyer's user ID
- `seller_username` - Seller's Telegram username
- `description` - Deal description
- `amount` - Deal amount in USDT
- `status` - Deal status (waiting/active/completed/cancelled/disputed)
- `created_at` - Deal creation timestamp
- `updated_at` - Last update timestamp
- `completed_at` - Completion timestamp
- `dispute_reason` - Reason for dispute
- `admin_notes` - Admin notes

### Payments Table
- `id` - Payment ID (Primary Key)
- `user_id` - User ID
- `payment_id` - NowPayments payment ID
- `amount` - Payment amount
- `currency` - Payment currency
- `status` - Payment status
- `invoice_url` - Payment invoice URL
- `created_at` - Payment creation timestamp
- `updated_at` - Last update timestamp

### Withdrawal History Table
- `id` - Withdrawal ID (Primary Key)
- `user_id` - User ID
- `amount` - Withdrawal amount
- `status` - Withdrawal status
- `admin_notes` - Admin notes
- `timestamp` - Withdrawal timestamp

## API Endpoints

### Webhook Endpoint
- `POST /webhook/nowpayments` - NowPayments webhook handler

### Health Check
- `GET /health` - Health check endpoint
- `GET /` - Root endpoint

## Bot Commands

- `/start` - Start the bot and show welcome message
- `/admin` - Access admin panel (admin only)

## Admin Features

- 📊 Dashboard - Overview of bot statistics
- 💰 Pending Withdrawals - Manage withdrawal requests
- ⚖️ Disputes - Handle deal disputes
- 👥 Users - View user information
- 📈 Statistics - Bot usage statistics

## Security Features

- 🔐 Webhook signature verification
- 🛡️ Input validation and sanitization
- 📝 Comprehensive logging
- ⏰ Transaction timeouts
- 🔒 Admin-only access controls

## Payment Processing

The bot uses NowPayments for cryptocurrency payments:

1. **Invoice Creation** - User selects amount and currency
2. **Payment Processing** - NowPayments handles the payment
3. **Webhook Notification** - Payment status updates via webhook
4. **Balance Update** - User balance updated upon confirmation

## Deal Flow

1. **Deal Creation** - Buyer creates deal with seller details
2. **Fund Escrow** - Amount held in escrow from buyer's balance
3. **Seller Notification** - Seller notified of pending deal
4. **Deal Completion** - Buyer confirms completion or raises dispute
5. **Fund Release** - Funds released to seller or returned to buyer

## Error Handling

- Comprehensive error logging
- User-friendly error messages
- Graceful failure handling
- Database transaction rollback

## Logging

The bot uses Python's logging module with the following levels:
- INFO - General information
- WARNING - Warning messages
- ERROR - Error messages
- DEBUG - Debug information (when enabled)

## Support

For support and questions:
- Telegram: @Abul_kalam2025
- Email: support@yourdomain.com

## License

This project is licensed under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Changelog

### Version 1.0.0
- Initial release
- Basic escrow functionality
- Payment integration
- Admin panel
- Webhook support 