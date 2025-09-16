# admin.py
import logging
from datetime import datetime, timedelta
from db import (
    get_db_connection, get_user, update_balance, 
    get_withdrawal_history, get_user_deals, get_pending_payments,
    update_deal_status, get_deal_counts
)
from config import ADMIN_USER_ID

logger = logging.getLogger(__name__)

def is_admin(user_id):
    """Check if user is admin"""
    return user_id == ADMIN_USER_ID

def get_bot_statistics():
    """Get comprehensive bot statistics"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        c = conn.cursor()
        stats = {}
        
        # Total users
        c.execute("SELECT COUNT(*) FROM users")
        stats['total_users'] = c.fetchone()[0]
        
        # Total balance
        c.execute("SELECT SUM(balance) FROM users")
        total_balance = c.fetchone()[0] or 0
        stats['total_balance'] = total_balance
        
        # Total deals
        c.execute("SELECT COUNT(*) FROM deals")
        stats['total_deals'] = c.fetchone()[0]
        
        # Deals by status
        c.execute("SELECT status, COUNT(*) FROM deals GROUP BY status")
        deals_by_status = dict(c.fetchall())
        stats['deals_by_status'] = deals_by_status
        
        # Total payments
        c.execute("SELECT COUNT(*) FROM payments")
        stats['total_payments'] = c.fetchone()[0]
        
        # Payments by status
        c.execute("SELECT status, COUNT(*) FROM payments GROUP BY status")
        payments_by_status = dict(c.fetchall())
        stats['payments_by_status'] = payments_by_status
        
        # Total withdrawal requests
        c.execute("SELECT COUNT(*) FROM withdrawal_history")
        stats['total_withdrawals'] = c.fetchone()[0]
        
        # Withdrawals by status
        c.execute("SELECT status, COUNT(*) FROM withdrawal_history GROUP BY status")
        withdrawals_by_status = dict(c.fetchall())
        stats['withdrawals_by_status'] = withdrawals_by_status
        
        # Recent activity (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        c.execute("SELECT COUNT(*) FROM users WHERE created_at > ?", (week_ago,))
        stats['new_users_week'] = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM deals WHERE created_at > ?", (week_ago,))
        stats['new_deals_week'] = c.fetchone()[0]
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return None
    finally:
        conn.close()

def get_pending_withdrawals():
    """Get all pending withdrawal requests"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        c = conn.cursor()
        c.execute("""
            SELECT wh.*, u.username, u.first_name 
            FROM withdrawal_history wh 
            JOIN users u ON wh.user_id = u.user_id 
            WHERE wh.status = 'pending' 
            ORDER BY wh.timestamp DESC
        """)
        return [dict(row) for row in c.fetchall()]
    except Exception as e:
        logger.error(f"Error getting pending withdrawals: {e}")
        return []
    finally:
        conn.close()

def approve_withdrawal(withdrawal_id, admin_notes=None):
    """Approve a withdrawal request"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        c = conn.cursor()
        
        # Get withdrawal details
        c.execute("SELECT * FROM withdrawal_history WHERE id = ?", (withdrawal_id,))
        withdrawal = c.fetchone()
        
        if not withdrawal:
            logger.error(f"Withdrawal {withdrawal_id} not found")
            return False
        
        if withdrawal['status'] != 'pending':
            logger.error(f"Withdrawal {withdrawal_id} is not pending")
            return False
        
        # Update withdrawal status
        c.execute("""
            UPDATE withdrawal_history 
            SET status = 'approved', admin_notes = ?, timestamp = ? 
            WHERE id = ?
        """, (admin_notes, datetime.now(), withdrawal_id))
        
        conn.commit()
        logger.info(f"Withdrawal {withdrawal_id} approved")
        return True
        
    except Exception as e:
        logger.error(f"Error approving withdrawal {withdrawal_id}: {e}")
        return False
    finally:
        conn.close()

def reject_withdrawal(withdrawal_id, admin_notes=None):
    """Reject a withdrawal request and refund balance"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        c = conn.cursor()
        
        # Get withdrawal details
        c.execute("SELECT * FROM withdrawal_history WHERE id = ?", (withdrawal_id,))
        withdrawal = c.fetchone()
        
        if not withdrawal:
            logger.error(f"Withdrawal {withdrawal_id} not found")
            return False
        
        if withdrawal['status'] != 'pending':
            logger.error(f"Withdrawal {withdrawal_id} is not pending")
            return False
        
        # Refund the balance
        update_balance(withdrawal['user_id'], withdrawal['amount'])
        
        # Update withdrawal status
        c.execute("""
            UPDATE withdrawal_history 
            SET status = 'rejected', admin_notes = ?, timestamp = ? 
            WHERE id = ?
        """, (admin_notes, datetime.now(), withdrawal_id))
        
        conn.commit()
        logger.info(f"Withdrawal {withdrawal_id} rejected and balance refunded")
        return True
        
    except Exception as e:
        logger.error(f"Error rejecting withdrawal {withdrawal_id}: {e}")
        return False
    finally:
        conn.close()

def get_disputed_deals():
    """Get all disputed deals"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        c = conn.cursor()
        c.execute("""
            SELECT d.*, u.username, u.first_name 
            FROM deals d 
            JOIN users u ON d.buyer_id = u.user_id 
            WHERE d.status = 'disputed' 
            ORDER BY d.updated_at DESC
        """)
        return [dict(row) for row in c.fetchall()]
    except Exception as e:
        logger.error(f"Error getting disputed deals: {e}")
        return []
    finally:
        conn.close()

def resolve_dispute(deal_id, resolution, admin_notes=None):
    """Resolve a disputed deal"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        c = conn.cursor()
        
        # Get deal details
        c.execute("SELECT * FROM deals WHERE id = ?", (deal_id,))
        deal = c.fetchone()
        
        if not deal:
            logger.error(f"Deal {deal_id} not found")
            return False
        
        if deal['status'] != 'disputed':
            logger.error(f"Deal {deal_id} is not disputed")
            return False
        
        # Update deal status based on resolution
        if resolution == 'refund_buyer':
            # Refund buyer
            update_balance(deal['buyer_id'], deal['amount'])
            new_status = 'cancelled'
        elif resolution == 'pay_seller':
            # Pay seller (deduct from buyer's balance)
            update_balance(deal['buyer_id'], -deal['amount'])
            new_status = 'completed'
        else:
            logger.error(f"Invalid resolution: {resolution}")
            return False
        
        # Update deal
        c.execute("""
            UPDATE deals 
            SET status = ?, admin_notes = ?, updated_at = ?, completed_at = ? 
            WHERE id = ?
        """, (new_status, admin_notes, datetime.now(), 
              datetime.now() if new_status == 'completed' else None, deal_id))
        
        conn.commit()
        logger.info(f"Deal {deal_id} resolved: {resolution}")
        return True
        
    except Exception as e:
        logger.error(f"Error resolving dispute for deal {deal_id}: {e}")
        return False
    finally:
        conn.close()

def get_user_details(user_id):
    """Get detailed user information"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        c = conn.cursor()
        
        # Get user info
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = c.fetchone()
        
        if not user:
            return None
        
        # Get user's deals
        c.execute("SELECT * FROM deals WHERE buyer_id = ? ORDER BY created_at DESC", (user_id,))
        deals = [dict(row) for row in c.fetchall()]
        
        # Get user's payments
        c.execute("SELECT * FROM payments WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        payments = [dict(row) for row in c.fetchall()]
        
        # Get user's withdrawals
        c.execute("SELECT * FROM withdrawal_history WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
        withdrawals = [dict(row) for row in c.fetchall()]
        
        return {
            'user': dict(user),
            'deals': deals,
            'payments': payments,
            'withdrawals': withdrawals
        }
        
    except Exception as e:
        logger.error(f"Error getting user details for {user_id}: {e}")
        return None
    finally:
        conn.close()

def update_user_balance(user_id, amount, reason):
    """Manually update user balance (admin only)"""
    if not is_admin(user_id):
        logger.error(f"Non-admin user {user_id} attempted to update balance")
        return False
    
    try:
        success = update_balance(user_id, amount)
        if success:
            logger.info(f"Admin updated balance for user {user_id}: {amount} ({reason})")
        return success
    except Exception as e:
        logger.error(f"Error updating balance for user {user_id}: {e}")
        return False

def get_system_health():
    """Get system health information"""
    conn = get_db_connection()
    if not conn:
        return {'status': 'error', 'message': 'Database connection failed'}
    
    try:
        c = conn.cursor()
        health = {'status': 'healthy', 'checks': {}}
        
        # Check database tables
        tables = ['users', 'deals', 'payments', 'withdrawal_history']
        for table in tables:
            try:
                c.execute(f"SELECT COUNT(*) FROM {table}")
                count = c.fetchone()[0]
                health['checks'][f'{table}_count'] = count
            except Exception as e:
                health['checks'][f'{table}_error'] = str(e)
                health['status'] = 'warning'
        
        # Check for stuck deals (older than 72 hours)
        three_days_ago = datetime.now() - timedelta(hours=72)
        c.execute("SELECT COUNT(*) FROM deals WHERE status = 'waiting' AND created_at < ?", (three_days_ago,))
        stuck_deals = c.fetchone()[0]
        health['checks']['stuck_deals'] = stuck_deals
        
        # Check for pending payments (older than 24 hours)
        one_day_ago = datetime.now() - timedelta(hours=24)
        c.execute("SELECT COUNT(*) FROM payments WHERE status = 'pending' AND created_at < ?", (one_day_ago,))
        old_payments = c.fetchone()[0]
        health['checks']['old_payments'] = old_payments
        
        return health
        
    except Exception as e:
        logger.error(f"Error checking system health: {e}")
        return {'status': 'error', 'message': str(e)}
    finally:
        conn.close()

def cleanup_old_data():
    """Clean up old data (admin maintenance function)"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        c = conn.cursor()
        
        # Archive old completed deals (older than 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        c.execute("""
            UPDATE deals 
            SET status = 'archived' 
            WHERE status = 'completed' AND completed_at < ?
        """, (thirty_days_ago,))
        
        # Archive old payments (older than 30 days)
        c.execute("""
            UPDATE payments 
            SET status = 'archived' 
            WHERE status IN ('confirmed', 'failed') AND updated_at < ?
        """, (thirty_days_ago,))
        
        conn.commit()
        logger.info("Old data cleanup completed")
        return True
        
    except Exception as e:
        logger.error(f"Error during data cleanup: {e}")
        return False
    finally:
        conn.close() 