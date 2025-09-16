# utils.py
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import get_deal_counts, get_user_deals
from config import MIN_DEPOSIT_AMOUNT, DEPOSIT_FEE_PERCENTAGE, ESCROW_FEE_PERCENTAGE

def check_subscription(bot, user_id, group_username):
    """Check if user is subscribed to the required group"""
    try:
        # Remove @ if present for get_chat_member
        group = group_username[1:] if group_username.startswith('@') else group_username
        member = bot.get_chat_member(f"@{group}", user_id)
        return member.status in ['member', 'creator', 'administrator']
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False

def main_menu():
    """Main menu markup"""
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("👤 Profile", callback_data="profile"),
               InlineKeyboardButton("🤝 Escrow", callback_data="escrow"))
    markup.row(InlineKeyboardButton("📕 FAQ and Rules", callback_data="faq"))
    return markup

def deposit_menu():
    """Deposit menu markup"""
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("💳 Deposit", callback_data="deposit"),
               InlineKeyboardButton("🏧 Withdraw", callback_data="withdraw"))
    markup.row(InlineKeyboardButton("📜 Withdrawal History", callback_data="history"))
    markup.row(InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main"))
    return markup

def escrow_menu(user_id=None):
    """Escrow menu markup with dynamic counts"""
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("➕ New Deal", callback_data="new_deal"))
    
    if user_id:
        # Get actual deal counts
        counts = get_deal_counts(user_id)
        markup.row(
            InlineKeyboardButton(f"👀 Waiting ({counts['waiting']})", callback_data="waiting"),
            InlineKeyboardButton(f"🧑‍💼 Active ({counts['active']})", callback_data="active"),
            InlineKeyboardButton(f"⚖️ Disputes ({counts['disputes']})", callback_data="disputes")
        )
    else:
        markup.row(
            InlineKeyboardButton("👀 Waiting (0)", callback_data="waiting"),
            InlineKeyboardButton("🧑‍💼 Active (0)", callback_data="active"),
            InlineKeyboardButton("⚖️ Disputes (0)", callback_data="disputes")
        )
    
    markup.row(InlineKeyboardButton("📜 History", callback_data="escrow_history"),
               InlineKeyboardButton("🔙 Back", callback_data="main"))
    return markup

def currency_menu():
    """Create currency selection menu"""
    markup = InlineKeyboardMarkup()
    # Only show USDT (TRC20) as requested
    markup.row(InlineKeyboardButton("🪙 USDT (TRC20)", callback_data="currency_usdttrc20"))
    markup.row(InlineKeyboardButton("🔙 Back", callback_data="main"))
    return markup

def deal_status_menu(deal_id):
    """Deal status management menu"""
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("✅ Complete", callback_data=f"complete_deal_{deal_id}"),
        InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_deal_{deal_id}")
    )
    markup.row(
        InlineKeyboardButton("⚠️ Dispute", callback_data=f"dispute_deal_{deal_id}"),
        InlineKeyboardButton("📝 Details", callback_data=f"deal_details_{deal_id}")
    )
    markup.row(InlineKeyboardButton("🔙 Back", callback_data="escrow"))
    return markup

def admin_menu():
    """Admin menu markup"""
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📊 Dashboard", callback_data="admin_dashboard"))
    markup.row(
        InlineKeyboardButton("💰 Pending Withdrawals", callback_data="admin_withdrawals"),
        InlineKeyboardButton("⚖️ Disputes", callback_data="admin_disputes")
    )
    markup.row(
        InlineKeyboardButton("👥 Users", callback_data="admin_users"),
        InlineKeyboardButton("📈 Statistics", callback_data="admin_stats")
    )
    markup.row(InlineKeyboardButton("🔙 Back", callback_data="main"))
    return markup

def format_balance(balance):
    """Format balance with proper decimal places"""
    return f"{balance:.2f}"

def format_amount(amount):
    """Format amount with proper decimal places"""
    return f"{amount:.2f}"

def calculate_fee(amount, fee_percentage):
    """Calculate fee amount"""
    return round(amount * (fee_percentage / 100), 2)

def calculate_total_with_fee(amount, fee_percentage):
    """Calculate total amount including fee"""
    fee = calculate_fee(amount, fee_percentage)
    return round(amount + fee, 2)

def validate_amount(amount, min_amount=0, max_amount=None):
    """Validate amount input"""
    try:
        amount = float(amount)
        if amount < min_amount:
            return False, f"Amount must be at least {min_amount}"
        if max_amount and amount > max_amount:
            return False, f"Amount cannot exceed {max_amount}"
        return True, amount
    except ValueError:
        return False, "Invalid amount format"

def format_deal_info(deal):
    """Format deal information for display"""
    status_emoji = {
        'waiting': '⏳',
        'active': '🔄',
        'completed': '✅',
        'cancelled': '❌',
        'disputed': '⚠️'
    }
    
    emoji = status_emoji.get(deal['status'], '❓')
    return f"{emoji} Deal #{deal['id']}\n" \
           f"Amount: {format_amount(deal['amount'])} USDT\n" \
           f"Seller: {deal['seller_username']}\n" \
           f"Status: {deal['status'].title()}\n" \
           f"Created: {deal['created_at'][:10]}"

def get_deal_list_text(user_id, status=None):
    """Get formatted text for deal list"""
    deals = get_user_deals(user_id, status)
    
    if not deals:
        status_text = f" {status}" if status else ""
        return f"📜 No{status_text} deals found."
    
    text = f"📜 Your {status if status else ''} Deals:\n\n"
    for deal in deals:
        text += format_deal_info(deal) + "\n\n"
    
    return text

def escape_markdown(text):
    """Escape special characters for MarkdownV2"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def truncate_text(text, max_length=100):
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def format_timestamp(timestamp):
    """Format timestamp for display"""
    if isinstance(timestamp, str):
        return timestamp[:19]  # Remove microseconds if present
    return str(timestamp)[:19]