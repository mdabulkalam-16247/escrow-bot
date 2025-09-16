# db.py
import sqlite3
import logging
from datetime import datetime
from config import DATABASE_NAME
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection with proper error handling and retry logic"""
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(DATABASE_NAME, timeout=20.0)
            conn.row_factory = sqlite3.Row  # This enables column access by name
            
            # Test the connection
            conn.execute("SELECT 1")
            logger.debug(f"Database connection established successfully (attempt {attempt + 1})")
            return conn
            
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower():
                if attempt < max_retries - 1:
                    logger.warning(f"Database locked, retrying in {retry_delay} seconds... (attempt {attempt + 1})")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    logger.error(f"Database locked after {max_retries} attempts: {e}")
                    return None
            else:
                logger.error(f"Database operational error: {e}")
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected database connection error: {e}")
            return None
    
    logger.error(f"Failed to connect to database after {max_retries} attempts")
    return None

def init_db():
    """Initialize database with all required tables"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        c = conn.cursor()

        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance REAL DEFAULT 0,
            deals_done INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

        # Withdrawal history table
        c.execute('''CREATE TABLE IF NOT EXISTS withdrawal_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            status TEXT DEFAULT 'pending',
            admin_notes TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )''')

        # Deals table for escrow functionality
        c.execute('''CREATE TABLE IF NOT EXISTS deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_id INTEGER,
            seller_username TEXT,
            description TEXT,
            amount REAL,
            status TEXT DEFAULT 'waiting',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME,
            dispute_reason TEXT,
            admin_notes TEXT,
            FOREIGN KEY (buyer_id) REFERENCES users (user_id)
        )''')

        # Payment transactions table
        c.execute('''CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            payment_id TEXT UNIQUE,
            amount REAL,
            currency TEXT,
            status TEXT DEFAULT 'pending',
            invoice_url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )''')

        conn.commit()
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        return False
    finally:
        conn.close()

def get_user(user_id):
    """Get user by ID, create if not exists"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        
        if not result:
            c.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
            conn.commit()
            c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            result = c.fetchone()
        
        return dict(result) if result else None
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        return None
    finally:
        conn.close()

def update_user_info(user_id, username=None, first_name=None):
    """Update user information"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        c = conn.cursor()
        updates = []
        params = []
        
        if username:
            updates.append("username = ?")
            params.append(username)
        if first_name:
            updates.append("first_name = ?")
            params.append(first_name)
        
        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.now())
            params.append(user_id)
            
            query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
            c.execute(query, params)
            conn.commit()
            return True
        return False
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        return False
    finally:
        conn.close()

def update_balance(user_id, amount):
    """Update user balance with transaction safety and proper error handling"""
    conn = get_db_connection()
    if not conn:
        logger.error(f"Failed to get database connection for balance update for user {user_id}")
        return False
    
    try:
        c = conn.cursor()
        
        # Start transaction
        c.execute("BEGIN TRANSACTION")
        
        # Get current balance first
        c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        
        if not result:
            # User doesn't exist, create them
            c.execute("INSERT INTO users (user_id, balance) VALUES (?, ?)", (user_id, amount))
            logger.info(f"Created new user {user_id} with balance {amount}")
        else:
            current_balance = result[0]
            new_balance = current_balance + amount
            
            # Check for negative balance (except for admin operations)
            if new_balance < 0:
                logger.warning(f"Attempted to set negative balance for user {user_id}: {new_balance}")
                c.execute("ROLLBACK")
                return False
            
            c.execute("UPDATE users SET balance = ?, updated_at = ? WHERE user_id = ?", 
                     (new_balance, datetime.now(), user_id))
            logger.info(f"Balance updated for user {user_id}: {current_balance} -> {new_balance} (change: {amount})")
        
        # Commit transaction
        c.execute("COMMIT")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Database error updating balance for user {user_id}: {e}")
        try:
            c.execute("ROLLBACK")
        except:
            pass
        return False
    except Exception as e:
        logger.error(f"Unexpected error updating balance for user {user_id}: {e}")
        try:
            c.execute("ROLLBACK")
        except:
            pass
        return False
    finally:
        conn.close()

def add_withdrawal_history(user_id, amount):
    """Add withdrawal request to history"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        c = conn.cursor()
        c.execute("INSERT INTO withdrawal_history (user_id, amount) VALUES (?, ?)", (user_id, amount))
        conn.commit()
        logger.info(f"Withdrawal request added for user {user_id}: {amount}")
        return True
    except Exception as e:
        logger.error(f"Error adding withdrawal history for user {user_id}: {e}")
        return False
    finally:
        conn.close()

def get_withdrawal_history(user_id):
    """Get withdrawal history for user"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM withdrawal_history WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
        return [dict(row) for row in c.fetchall()]
    except Exception as e:
        logger.error(f"Error getting withdrawal history for user {user_id}: {e}")
        return []
    finally:
        conn.close()

def create_deal(buyer_id, seller_username, description, amount):
    """Create a new escrow deal"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO deals (buyer_id, seller_username, description, amount) 
            VALUES (?, ?, ?, ?)
        """, (buyer_id, seller_username, description, amount))
        
        deal_id = c.lastrowid
        conn.commit()
        logger.info(f"Deal created: {deal_id} for buyer {buyer_id}")
        return deal_id
    except Exception as e:
        logger.error(f"Error creating deal for buyer {buyer_id}: {e}")
        return None
    finally:
        conn.close()

def get_user_deals(user_id, status=None):
    """Get deals for a user"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        c = conn.cursor()
        if status:
            c.execute("SELECT * FROM deals WHERE buyer_id = ? AND status = ? ORDER BY created_at DESC", 
                     (user_id, status))
        else:
            c.execute("SELECT * FROM deals WHERE buyer_id = ? ORDER BY created_at DESC", (user_id,))
        return [dict(row) for row in c.fetchall()]
    except Exception as e:
        logger.error(f"Error getting deals for user {user_id}: {e}")
        return []
    finally:
        conn.close()

def update_deal_status(deal_id, status, admin_notes=None):
    """Update deal status"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        c = conn.cursor()
        if admin_notes:
            c.execute("""
                UPDATE deals SET status = ?, admin_notes = ?, updated_at = ? 
                WHERE id = ?
            """, (status, admin_notes, datetime.now(), deal_id))
        else:
            c.execute("""
                UPDATE deals SET status = ?, updated_at = ? 
                WHERE id = ?
            """, (status, datetime.now(), deal_id))
        
        conn.commit()
        logger.info(f"Deal {deal_id} status updated to {status}")
        return True
    except Exception as e:
        logger.error(f"Error updating deal {deal_id}: {e}")
        return False
    finally:
        conn.close()

def add_payment(user_id, payment_id, amount, currency, invoice_url):
    """Add payment record with validation and error handling"""
    conn = get_db_connection()
    if not conn:
        logger.error(f"Failed to get database connection for adding payment {payment_id}")
        return False
    
    try:
        c = conn.cursor()
        
        # Validate input parameters
        if not payment_id or not isinstance(payment_id, str):
            logger.error(f"Invalid payment_id: {payment_id}")
            return False
        
        if not user_id or not isinstance(user_id, int):
            logger.error(f"Invalid user_id: {user_id}")
            return False
        
        if not amount or amount <= 0:
            logger.error(f"Invalid amount: {amount}")
            return False
        
        if not currency or not isinstance(currency, str):
            logger.error(f"Invalid currency: {currency}")
            return False
        
        # Check if payment already exists
        c.execute("SELECT id FROM payments WHERE payment_id = ?", (payment_id,))
        if c.fetchone():
            logger.warning(f"Payment {payment_id} already exists in database")
            return True  # Consider this a success since payment exists
        
        # Start transaction
        c.execute("BEGIN TRANSACTION")
        
        # Insert payment record
        c.execute("""
            INSERT INTO payments (user_id, payment_id, amount, currency, invoice_url, status) 
            VALUES (?, ?, ?, ?, ?, 'pending')
        """, (user_id, payment_id, amount, currency, invoice_url))
        
        # Commit transaction
        c.execute("COMMIT")
        
        logger.info(f"Payment record added successfully for user {user_id}: {payment_id}")
        return True
        
    except sqlite3.IntegrityError as e:
        logger.error(f"Integrity error adding payment {payment_id}: {e}")
        try:
            c.execute("ROLLBACK")
        except:
            pass
        return False
    except sqlite3.Error as e:
        logger.error(f"Database error adding payment {payment_id}: {e}")
        try:
            c.execute("ROLLBACK")
        except:
            pass
        return False
    except Exception as e:
        logger.error(f"Unexpected error adding payment {payment_id}: {e}")
        try:
            c.execute("ROLLBACK")
        except:
            pass
        return False
    finally:
        conn.close()

def update_payment_status(payment_id, status):
    """Update payment status with validation and transaction safety"""
    conn = get_db_connection()
    if not conn:
        logger.error(f"Failed to get database connection for updating payment {payment_id}")
        return False
    
    try:
        c = conn.cursor()
        
        # Validate input parameters
        if not payment_id or not isinstance(payment_id, str):
            logger.error(f"Invalid payment_id: {payment_id}")
            return False
        
        if not status or not isinstance(status, str):
            logger.error(f"Invalid status: {status}")
            return False
        
        # Valid payment statuses
        valid_statuses = ['pending', 'confirming', 'confirmed', 'failed', 'cancelled', 'expired']
        if status not in valid_statuses:
            logger.error(f"Invalid payment status: {status}")
            return False
        
        # Start transaction
        c.execute("BEGIN TRANSACTION")
        
        # Check if payment exists
        c.execute("SELECT id, status FROM payments WHERE payment_id = ?", (payment_id,))
        result = c.fetchone()
        
        if not result:
            logger.error(f"Payment {payment_id} not found in database")
            c.execute("ROLLBACK")
            return False
        
        current_status = result[1]
        
        # Check if status is already the same
        if current_status == status:
            logger.info(f"Payment {payment_id} status already {status}, no update needed")
            c.execute("ROLLBACK")
            return True
        
        # Update payment status
        c.execute("""
            UPDATE payments SET status = ?, updated_at = ? 
            WHERE payment_id = ?
        """, (status, datetime.now(), payment_id))
        
        # Verify update was successful
        if c.rowcount == 0:
            logger.error(f"No rows updated for payment {payment_id}")
            c.execute("ROLLBACK")
            return False
        
        # Commit transaction
        c.execute("COMMIT")
        
        logger.info(f"Payment {payment_id} status updated: {current_status} -> {status}")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Database error updating payment {payment_id}: {e}")
        try:
            c.execute("ROLLBACK")
        except:
            pass
        return False
    except Exception as e:
        logger.error(f"Unexpected error updating payment {payment_id}: {e}")
        try:
            c.execute("ROLLBACK")
        except:
            pass
        return False
    finally:
        conn.close()

def get_pending_payments():
    """Get all pending payments"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM payments WHERE status = 'pending' ORDER BY created_at DESC")
        return [dict(row) for row in c.fetchall()]
    except Exception as e:
        logger.error(f"Error getting pending payments: {e}")
        return []
    finally:
        conn.close()

def get_deal_counts(user_id):
    """Get deal counts by status for a user"""
    conn = get_db_connection()
    if not conn:
        return {'waiting': 0, 'active': 0, 'disputes': 0}
    
    try:
        c = conn.cursor()
        c.execute("""
            SELECT status, COUNT(*) as count 
            FROM deals 
            WHERE buyer_id = ? 
            GROUP BY status
        """, (user_id,))
        
        counts = {'waiting': 0, 'active': 0, 'disputes': 0}
        for row in c.fetchall():
            status = row['status']
            if status in counts:
                counts[status] = row['count']
        
        return counts
    except Exception as e:
        logger.error(f"Error getting deal counts for user {user_id}: {e}")
        return {'waiting': 0, 'active': 0, 'disputes': 0}
    finally:
        conn.close()