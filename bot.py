# bot.py
import telebot
import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, ReplyKeyboardRemove
from config import BOT_TOKEN, GROUP_USERNAME, ADMIN_USER_ID, MIN_DEPOSIT_AMOUNT, DEPOSIT_FEE_PERCENTAGE, ESCROW_FEE_PERCENTAGE, MAX_DEAL_AMOUNT, SUCCESS_URL, CANCEL_URL
from db import init_db, get_user, update_balance, get_withdrawal_history, add_withdrawal_history, create_deal, get_user_deals, update_deal_status, update_user_info
from utils import check_subscription, main_menu, deposit_menu, escrow_menu, currency_menu, deal_status_menu, admin_menu, format_balance, format_amount, calculate_fee, calculate_total_with_fee, validate_amount, get_deal_list_text, format_deal_info
from payment import create_invoice, PaymentError, get_minimum_payment_amount
from error_handler import error_handler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)

# Initialize database
if not init_db():
    logger.error("Failed to initialize database")
    exit(1)

# Store deal creation state per user (in-memory for demo)
deal_creation_state = {}
# Store user's selected currency for deposit
user_currency = {}

@bot.message_handler(commands=['start'])
def start_handler(message: Message):
    """Handle /start command"""
    user_id = getattr(message.from_user, 'id', None)
    # --- Reset user state on /start ---
    if user_id is not None:
        deal_creation_state.pop(user_id, None)
        user_currency.pop(user_id, None)
    # --- End reset ---
    username = getattr(message.from_user, 'username', None)
    first_name = getattr(message.from_user, 'first_name', None)
    if user_id is None:
        bot.send_message(message.chat.id, "❌ Could not get your user ID. Please try again.")
        return
    # Update user info in database
    update_user_info(user_id, username, first_name)
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("➡ Go to Group", url="https://t.me/lagit_airdropgroup"))
    markup.row(InlineKeyboardButton("🔄 Check Subscription", callback_data="check_sub"))
    
    bot.send_message(
        message.chat.id, 
        "🤖 Welcome to Escrow Bot!\n\n"
        "This bot provides secure escrow services for your transactions.\n\n"
        "To use the bot, join our group first.",
        reply_markup=markup
    )

@bot.message_handler(commands=['admin'])
def admin_handler(message: Message):
    """Handle admin commands"""
    user_id = getattr(message.from_user, 'id', None)
    if user_id is None:
        bot.reply_to(message, "❌ Could not get your user ID.")
        return
    if user_id != ADMIN_USER_ID:
        bot.reply_to(message, "❌ Access denied. Admin only.")
        return
    bot.send_message(message.chat.id, "🔧 Admin Panel", reply_markup=admin_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    """Handle all callback queries"""
    user_id = call.from_user.id
    
    try:
        if call.data == "check_sub":
            if check_subscription(bot, user_id, GROUP_USERNAME):
                bot.send_message(
                    call.message.chat.id,
                    "<b>✅ Access Granted!</b>\n\nWelcome! You now have full access to the Escrow Bot features.",
                    reply_markup=main_menu(),
                    parse_mode="HTML"
                )
            else:
                bot.answer_callback_query(call.id, "❌ You're not subscribed!")
                
        elif call.data == "profile":
            user = get_user(user_id)
            if user:
                profile_msg = "👤 Your Profile\n\n"
                profile_msg += f"💰 Balance: {format_balance(user['balance'])} USDT\n\n"
                profile_msg += f"🤝 Deals Done: {user['deals_done']}\n"
                profile_msg += f"📅 Member since: {user['created_at'][:10]}"
                bot.send_message(call.message.chat.id, profile_msg, reply_markup=deposit_menu())
            else:
                bot.send_message(call.message.chat.id, "❌ Error loading profile.")
                
        elif call.data == "deposit":
            bot.send_message(
                call.message.chat.id,
                f"💳 Select payment currency:\n\n"
                f"Minimum deposit: {get_minimum_payment_amount()} USD",
                reply_markup=currency_menu()
            )
            
        elif call.data.startswith("currency_"):
            currency = call.data.split("_")[1]
            user_currency[user_id] = currency
            bot.send_message(
                call.message.chat.id,
                f"Please enter amount to deposit (USD):\n\n"
                f"Currency: {currency}\n"
                f"Minimum: {get_minimum_payment_amount()} USD"
            )
            bot.register_next_step_handler(call.message, handle_deposit)
            
        elif call.data == "withdraw":
            user = get_user(user_id)
            if user and user['balance'] > 0:
                bot.send_message(
                    call.message.chat.id, 
                    f"Enter amount to withdraw (USD):\n\n"
                    f"Available balance: {format_balance(user['balance'])} USDT"
                )
                bot.register_next_step_handler(call.message, handle_withdraw)
            else:
                bot.send_message(call.message.chat.id, "❌ No balance available for withdrawal.")
                
        elif call.data == "history":
            show_withdrawal_history(call.message, user_id)
            
        elif call.data == "faq":
            faq_msg = (
                "📜 Frequently Asked Questions:\n\n"
                "🤝 How to create a deal?\n"
                "Go to Escrow section and click 'New Deal'.\n\n"
                "💰 What are the fees?\n"
                f"Deposit fee: {DEPOSIT_FEE_PERCENTAGE}%\n"
                f"Escrow fee: {ESCROW_FEE_PERCENTAGE}%\n\n"
                "⏰ How long do deals take?\n"
                "Deals are typically completed within 24-72 hours.\n\n"
                "🛡️ Is it secure?\n"
                "Yes, all funds are held in escrow until deal completion.\n\n"
                "📞 Support?\n"
                "@Abul_kalam2025"
            )
            faq_markup = InlineKeyboardMarkup()
            faq_markup.add(InlineKeyboardButton("💬 Contact Support", url="https://t.me/Abul_kalam2025"))
            faq_markup.add(InlineKeyboardButton("🔙 Back to Menu", callback_data="main"))
            bot.send_message(call.message.chat.id, faq_msg, reply_markup=faq_markup)
            
        elif call.data == "main":
            bot.send_message(call.message.chat.id, "🏠 Main Menu:", reply_markup=main_menu())
            
        elif call.data == "escrow":
            bot.send_message(
                call.message.chat.id, 
                "🤝 My Deals\n\n👉 Select a deal category:", 
                reply_markup=escrow_menu(user_id)
            )
            
        elif call.data == "new_deal":
            deal_creation_state[user_id] = {}
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("❌ Cancel Deal Creation", callback_data="cancel_deal"))
            bot.send_message(
                call.message.chat.id,
                "Starting a new deal...\n\n"
                "Please enter the Telegram @username of the seller.\n"
                "Ensure they are a member of our required group.",
                reply_markup=markup
            )
            bot.register_next_step_handler(call.message, handle_seller_username)
            
        elif call.data == "cancel_deal":
            deal_creation_state.pop(user_id, None)
            bot.send_message(call.message.chat.id, "❌ Deal creation cancelled.", reply_markup=escrow_menu(user_id))
            
        elif call.data == "waiting":
            deals = get_user_deals(user_id, "waiting")
            if deals:
                text = get_deal_list_text(user_id, "waiting")
                bot.send_message(call.message.chat.id, text, reply_markup=escrow_menu(user_id))
            else:
                bot.send_message(call.message.chat.id, "👀 No waiting deals.", reply_markup=escrow_menu(user_id))
                
        elif call.data == "active":
            deals = get_user_deals(user_id, "active")
            if deals:
                text = get_deal_list_text(user_id, "active")
                bot.send_message(call.message.chat.id, text, reply_markup=escrow_menu(user_id))
            else:
                bot.send_message(call.message.chat.id, "🧑‍💼 No active deals.", reply_markup=escrow_menu(user_id))
                
        elif call.data == "disputes":
            deals = get_user_deals(user_id, "disputed")
            if deals:
                text = get_deal_list_text(user_id, "disputed")
                bot.send_message(call.message.chat.id, text, reply_markup=escrow_menu(user_id))
            else:
                bot.send_message(call.message.chat.id, "⚖️ No disputes.", reply_markup=escrow_menu(user_id))
                
        elif call.data == "escrow_history":
            deals = get_user_deals(user_id)
            if deals:
                text = get_deal_list_text(user_id)
                bot.send_message(call.message.chat.id, text, reply_markup=escrow_menu(user_id))
            else:
                bot.send_message(call.message.chat.id, "📜 No deal history yet.", reply_markup=escrow_menu(user_id))
                
        # Admin callbacks
        elif call.data.startswith("admin_"):
            if user_id != ADMIN_USER_ID:
                bot.answer_callback_query(call.id, "❌ Admin access required!")
                return
            handle_admin_callback(call)
            
        # Deal management callbacks
        elif call.data.startswith(("complete_deal_", "cancel_deal_", "dispute_deal_", "deal_details_")):
            handle_deal_callback(call)
            
    except Exception as e:
        logger.error(f"Error in callback handler: {e}")
        bot.answer_callback_query(call.id, "❌ An error occurred. Please try again.")

def handle_deposit(message):
    """Handle deposit amount input"""
    user_id = getattr(message.from_user, 'id', None)
    if user_id is None:
        bot.send_message(message.chat.id, "❌ Could not get your user ID.")
        return
    
    currency = user_currency.get(user_id, "usdttrc20")
    
    try:
        # Validate amount input
        is_valid, result = validate_amount(message.text, int(MIN_DEPOSIT_AMOUNT))
        if not is_valid:
            bot.send_message(message.chat.id, f"❌ {result}")
            bot.register_next_step_handler(message, handle_deposit)
            return
        
        amount = float(result)
        fee = calculate_fee(amount, DEPOSIT_FEE_PERCENTAGE)
        total = calculate_total_with_fee(amount, DEPOSIT_FEE_PERCENTAGE)
        
        # Show processing message
        processing_msg = bot.send_message(
            message.chat.id,
            "⏳ Creating payment invoice... Please wait."
        )
        
        try:
            # Create invoice with better error handling
            invoice_data = create_invoice(total, user_id, currency)
            
            if invoice_data and invoice_data.get('invoice_url'):
                # Delete processing message
                bot.delete_message(message.chat.id, processing_msg.message_id)
                
                # Send success message with invoice
                bot.send_message(
                    message.chat.id,
                    f"✅ Payment Invoice Created Successfully!\n\n"
                    f"💰 Amount: {format_amount(amount)} USD\n"
                    f"💸 Fee ({DEPOSIT_FEE_PERCENTAGE}%): {format_amount(fee)} USD\n"
                    f"💳 Total: {format_amount(total)} USD\n"
                    f"🪙 Currency: {currency.upper()}\n"
                    f"🆔 Payment ID: {invoice_data.get('payment_id', 'N/A')}\n\n"
                    f"🔗 Pay here:\n{invoice_data['invoice_url']}\n\n"
                    f"⚠️ Please complete payment within 30 minutes.\n"
                    f"📞 Contact support if you face any issues: @Abul_kalam2025"
                )
            else:
                # Delete processing message
                bot.delete_message(message.chat.id, processing_msg.message_id)
                raise PaymentError("Failed to create payment invoice. Please try again.")
                
        except PaymentError as e:
            # Delete processing message
            bot.delete_message(message.chat.id, processing_msg.message_id)
            
            # Use centralized error handler
            error_message = error_handler.handle_payment_error(e, user_id, {
                "amount": amount,
                "currency": currency,
                "action": "create_invoice"
            })
            bot.send_message(message.chat.id, error_message)
                
        except Exception as e:
            # Delete processing message
            bot.delete_message(message.chat.id, processing_msg.message_id)
            
            # Log error with context
            error_handler.log_error(e, {
                "user_id": user_id,
                "amount": amount,
                "currency": currency,
                "action": "handle_deposit"
            })
            
            bot.send_message(
                message.chat.id,
                "❌ An unexpected error occurred while creating payment.\n\n"
                "Please try again or contact support: @Abul_kalam2025"
            )
            
    except ValueError:
        bot.send_message(
            message.chat.id, 
            "❌ Invalid amount format. Please enter a valid number (e.g., 10.50)"
        )
        bot.register_next_step_handler(message, handle_deposit)
    except Exception as e:
        logger.error(f"Error in handle_deposit for user {user_id}: {e}")
        bot.send_message(
            message.chat.id,
            "❌ An error occurred. Please try again or contact support: @Abul_kalam2025"
        )

def handle_withdraw(message):
    """Handle withdrawal amount input"""
    user_id = getattr(message.from_user, 'id', None)
    if user_id is None:
        bot.send_message(message.chat.id, "❌ Could not get your user ID.")
        return
    try:
        is_valid, result = validate_amount(message.text, 5)  # Minimum withdrawal as int
        if not is_valid:
            bot.send_message(message.chat.id, f"❌ {result}")
            bot.register_next_step_handler(message, handle_withdraw)
            return
        amount = float(result)
        user = get_user(user_id)
        if not user or amount > user['balance']:
            bot.send_message(message.chat.id, "❌ Insufficient balance.")
            return
        # Process withdrawal
        if update_balance(user_id, -amount) and add_withdrawal_history(user_id, amount):
            bot.send_message(
                message.chat.id, 
                f"✅ Withdrawal request submitted!\n\n"
                f"💰 Amount: {format_amount(amount)} USDT\n"
                f"📅 Processing time: 24-48 hours\n\n"
                f"Your request will be reviewed by admin."
            )
        else:
            bot.send_message(message.chat.id, "❌ Failed to process withdrawal request.")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Invalid amount. Please enter a valid number.")
        bot.register_next_step_handler(message, handle_withdraw)

def show_withdrawal_history(message, user_id):
    """Show withdrawal history"""
    history = get_withdrawal_history(user_id)
    if not history:
        bot.send_message(message.chat.id, "📜 No withdrawal history found.")
    else:
        msg = "📜 Withdrawal History:\n\n"
        for row in history:
            status_emoji = {
                'pending': '⏳',
                'approved': '✅',
                'rejected': '❌'
            }
            emoji = status_emoji.get(row['status'], '❓')
            msg += f"{emoji} {format_amount(row['amount'])} USDT - {row['status'].title()}\n"
            msg += f"📅 {format_timestamp(row['timestamp'])}\n\n"
        bot.send_message(message.chat.id, msg)

def handle_seller_username(message):
    """Handle seller username input"""
    user_id = message.from_user.id
    
    if message.text.startswith("@"):
        seller_username = message.text
        deal_creation_state[user_id]["seller_username"] = seller_username
        
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("❌ Cancel Deal Creation", callback_data="cancel_deal"))
        
        bot.send_message(
            message.chat.id,
            f"✅ Seller: {seller_username}\n\n"
            f"Now, enter a brief name or description for the deal\n"
            f"(e.g., \"Logo Design Project\", \"Crypto Artwork NFT\")",
            reply_markup=markup
        )
        bot.register_next_step_handler(message, handle_deal_description)
    else:
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("❌ Cancel Deal Creation", callback_data="cancel_deal"))
        bot.send_message(
            message.chat.id, 
            "❌ Please enter a valid @username.",
            reply_markup=markup
        )
        bot.register_next_step_handler(message, handle_seller_username)

def handle_deal_description(message):
    """Handle deal description input"""
    user_id = message.from_user.id
    deal_creation_state[user_id]["description"] = message.text
    
    user = get_user(user_id)
    balance = user['balance'] if user else 0
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("❌ Cancel Deal Creation", callback_data="cancel_deal"))
    
    bot.send_message(
        message.chat.id,
        f"📝 Deal Description: {message.text}\n\n"
        f"💰 Your Balance: {format_balance(balance)} USDT\n\n"
        f"Enter the deal amount in USDT.\n"
        f"This amount will be held in escrow from your balance.\n\n"
        f"Maximum deal amount: {format_amount(MAX_DEAL_AMOUNT)} USDT",
        reply_markup=markup
    )
    bot.register_next_step_handler(message, handle_deal_amount)

def handle_deal_amount(message):
    """Handle deal amount input"""
    user_id = getattr(message.from_user, 'id', None)
    if user_id is None:
        bot.send_message(message.chat.id, "❌ Could not get your user ID.")
        return
    user = get_user(user_id)
    if not user:
        bot.send_message(message.chat.id, "❌ User not found.")
        return
    balance = user['balance']
    try:
        is_valid, result = validate_amount(message.text, 1, int(MAX_DEAL_AMOUNT))
        if not is_valid:
            bot.send_message(message.chat.id, f"❌ {result}")
            bot.register_next_step_handler(message, handle_deal_amount)
            return
        amount = float(result)
        if amount > balance:
            bot.send_message(
                message.chat.id, 
                f"❌ Insufficient balance.\n\n"
                f"Required: {format_amount(amount)} USDT\n"
                f"Available: {format_balance(balance)} USDT"
            )
            bot.register_next_step_handler(message, handle_deal_amount)
            return
        # Create the deal
        deal_data = deal_creation_state[user_id]
        deal_id = create_deal(
            user_id, 
            deal_data["seller_username"], 
            deal_data["description"], 
            amount
        )
        if deal_id:
            # Deduct balance
            update_balance(user_id, -amount)
            # Clear deal creation state
            deal_creation_state.pop(user_id, None)
            bot.send_message(
                message.chat.id,
                f"✅ Deal Created Successfully!\n\n"
                f"🆔 Deal ID: #{deal_id}\n"
                f"💰 Amount: {format_amount(amount)} USDT\n"
                f"👤 Seller: {deal_data['seller_username']}\n"
                f"📝 Description: {deal_data['description']}\n\n"
                f"Your funds are now held in escrow.",
                reply_markup=escrow_menu(user_id)
            )
        else:
            bot.send_message(message.chat.id, "❌ Failed to create deal. Please try again.")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Invalid amount. Please enter a valid number.")
        bot.register_next_step_handler(message, handle_deal_amount)

def handle_admin_callback(call):
    """Handle admin-specific callbacks"""
    if call.data == "admin_dashboard":
        # Show admin dashboard
        bot.send_message(call.message.chat.id, "📊 Admin Dashboard - Coming Soon")
    elif call.data == "admin_withdrawals":
        # Show pending withdrawals
        bot.send_message(call.message.chat.id, "💰 Pending Withdrawals - Coming Soon")
    elif call.data == "admin_disputes":
        # Show disputes
        bot.send_message(call.message.chat.id, "⚖️ Disputes - Coming Soon")
    elif call.data == "admin_users":
        # Show user statistics
        bot.send_message(call.message.chat.id, "👥 Users - Coming Soon")
    elif call.data == "admin_stats":
        # Show bot statistics
        bot.send_message(call.message.chat.id, "📈 Statistics - Coming Soon")

def handle_deal_callback(call):
    """Handle deal management callbacks"""
    user_id = call.from_user.id
    
    if call.data.startswith("complete_deal_"):
        deal_id = int(call.data.split("_")[2])
        # Handle deal completion
        bot.send_message(call.message.chat.id, f"✅ Deal #{deal_id} completed!")
        
    elif call.data.startswith("cancel_deal_"):
        deal_id = int(call.data.split("_")[2])
        # Handle deal cancellation
        bot.send_message(call.message.chat.id, f"❌ Deal #{deal_id} cancelled!")
        
    elif call.data.startswith("dispute_deal_"):
        deal_id = int(call.data.split("_")[2])
        # Handle deal dispute
        bot.send_message(call.message.chat.id, f"⚠️ Dispute opened for Deal #{deal_id}")
        
    elif call.data.startswith("deal_details_"):
        deal_id = int(call.data.split("_")[2])
        # Show deal details
        bot.send_message(call.message.chat.id, f"📝 Details for Deal #{deal_id}")

def format_timestamp(timestamp):
    """Format timestamp for display"""
    if isinstance(timestamp, str):
        return timestamp[:19]
    return str(timestamp)[:19]

@bot.message_handler(commands=['check_payment'])
def check_payment_handler(message: Message):
    """Handle payment status check command"""
    user_id = getattr(message.from_user, 'id', None)
    if user_id is None:
        bot.reply_to(message, "❌ Could not get your user ID.")
        return
    
    # Check if user is admin
    if user_id != ADMIN_USER_ID:
        bot.reply_to(message, "❌ This command is for admin only.")
        return
    
    try:
        # Extract payment ID from message
        if not message.text:
            bot.reply_to(message, "❌ Invalid message format.")
            return
            
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ Usage: /check_payment <payment_id>")
            return
        
        payment_id = args[1]
        
        # Check payment status
        from payment_monitor import check_payment_status
        if check_payment_status(payment_id):
            bot.reply_to(message, f"✅ Payment {payment_id} status checked successfully.")
        else:
            bot.reply_to(message, f"❌ Failed to check payment {payment_id} status.")
            
    except Exception as e:
        error_handler.log_error(e, {
            "user_id": user_id,
            "action": "check_payment_command"
        })
        bot.reply_to(message, "❌ Error checking payment status.")

@bot.message_handler(commands=['mypayments'])
def my_payments_handler(message: Message):
    """Handle user payment history command"""
    user_id = getattr(message.from_user, 'id', None)
    if user_id is None:
        bot.reply_to(message, "❌ Could not get your user ID.")
        return
    
    try:
        from payment_status import get_payment_status_summary
        summary = get_payment_status_summary(user_id)
        bot.reply_to(message, summary)
        
    except Exception as e:
        error_handler.log_error(e, {
            "user_id": user_id,
            "action": "my_payments_command"
        })
        bot.reply_to(message, "❌ Error loading payment history.")

if __name__ == "__main__":
    logger.info("Bot is starting...")
    
    # Start payment monitor
    try:
        from payment_monitor import start_payment_monitor
        start_payment_monitor()
        logger.info("Payment monitor started successfully")
    except Exception as e:
        logger.error(f"Failed to start payment monitor: {e}")
    
    try:
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        logger.error(f"Bot polling error: {e}")
    finally:
        # Stop payment monitor on exit
        try:
            from payment_monitor import stop_payment_monitor
            stop_payment_monitor()
            logger.info("Payment monitor stopped")
        except Exception as e:
            logger.error(f"Error stopping payment monitor: {e}")