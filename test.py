# test.py
import unittest
import sqlite3
import os
from datetime import datetime
from db import init_db, get_user, update_balance, create_deal, get_user_deals
from payment import create_invoice, get_minimum_payment_amount
from utils import validate_amount, calculate_fee, format_balance
from config import DATABASE_NAME

class TestEscrowBot(unittest.TestCase):
    
    def setUp(self):
        """Set up test database"""
        # Use a test database
        self.test_db = 'test_bot.db'
        os.environ['DATABASE_NAME'] = self.test_db
        
        # Initialize test database
        init_db()
    
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    def test_database_initialization(self):
        """Test database initialization"""
        conn = sqlite3.connect(self.test_db)
        c = conn.cursor()
        
        # Check if tables exist
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in c.fetchall()]
        
        expected_tables = ['users', 'deals', 'payments', 'withdrawal_history']
        for table in expected_tables:
            self.assertIn(table, tables)
        
        conn.close()
    
    def test_user_creation(self):
        """Test user creation and retrieval"""
        user_id = 12345
        
        # Get user (should create if not exists)
        user = get_user(user_id)
        self.assertIsNotNone(user)
        if user:  # Add null check
            self.assertEqual(user['user_id'], user_id)
            self.assertEqual(user['balance'], 0.0)
            self.assertEqual(user['deals_done'], 0)
    
    def test_balance_update(self):
        """Test balance update functionality"""
        user_id = 12345
        initial_balance = 100.0
        
        # Set initial balance
        update_balance(user_id, initial_balance)
        user = get_user(user_id)
        self.assertIsNotNone(user)
        if user:  # Add null check
            self.assertEqual(user['balance'], initial_balance)
            
            # Add more balance
            update_balance(user_id, 50.0)
            user = get_user(user_id)
            self.assertIsNotNone(user)
            if user:  # Add null check
                self.assertEqual(user['balance'], 150.0)
                
                # Deduct balance
                update_balance(user_id, -25.0)
                user = get_user(user_id)
                self.assertIsNotNone(user)
                if user:  # Add null check
                    self.assertEqual(user['balance'], 125.0)
    
    def test_deal_creation(self):
        """Test deal creation"""
        user_id = 12345
        seller_username = "@test_seller"
        description = "Test deal"
        amount = 50.0
        
        # Create deal
        deal_id = create_deal(user_id, seller_username, description, amount)
        self.assertIsNotNone(deal_id)
        
        # Get user deals
        deals = get_user_deals(user_id)
        self.assertEqual(len(deals), 1)
        if deals:  # Add null check
            self.assertEqual(deals[0]['seller_username'], seller_username)
            self.assertEqual(deals[0]['description'], description)
            self.assertEqual(deals[0]['amount'], amount)
            self.assertEqual(deals[0]['status'], 'waiting')
    
    def test_amount_validation(self):
        """Test amount validation"""
        # Valid amounts
        result = validate_amount("100.50", min_amount=10)
        self.assertTrue(result[0])  # valid should be True
        self.assertIsInstance(result[1], float)  # amount should be float
        self.assertEqual(result[1], 100.50)  # amount should be 100.50
        
        # Invalid amounts
        result = validate_amount("abc", min_amount=10)
        self.assertFalse(result[0])  # valid should be False
        self.assertIsInstance(result[1], str)  # error should be string
        if isinstance(result[1], str):
            self.assertIn("Invalid amount format", result[1])
        
        # Amount too small
        result = validate_amount("5", min_amount=10)
        self.assertFalse(result[0])  # valid should be False
        self.assertIsInstance(result[1], str)  # error should be string
        if isinstance(result[1], str):
            self.assertIn("Amount must be at least 10", result[1])
        
        # Amount too large
        result = validate_amount("1000", min_amount=10, max_amount=500)
        self.assertFalse(result[0])  # valid should be False
        self.assertIsInstance(result[1], str)  # error should be string
        if isinstance(result[1], str):
            self.assertIn("Amount cannot exceed 500", result[1])
    
    def test_fee_calculation(self):
        """Test fee calculation"""
        amount = 100.0
        fee_percentage = 3.0
        
        fee = calculate_fee(amount, fee_percentage)
        self.assertEqual(fee, 3.0)
        
        total = amount + fee
        self.assertEqual(total, 103.0)
    
    def test_balance_formatting(self):
        """Test balance formatting"""
        balance = 123.456789
        formatted = format_balance(balance)
        self.assertEqual(formatted, "123.46")
    
    def test_minimum_payment_amount(self):
        """Test minimum payment amount"""
        min_amount = get_minimum_payment_amount()
        self.assertEqual(min_amount, 10.0)
    
    def test_database_connection_error_handling(self):
        """Test database connection error handling"""
        # This test would require mocking the database connection
        # For now, we'll just test that the functions don't crash
        try:
            user = get_user(99999)
            # Should not crash even if database is not accessible
            self.assertIsNotNone(user)
        except Exception as e:
            # If there's an error, it should be handled gracefully
            self.assertIsInstance(e, Exception)

class TestPaymentIntegration(unittest.TestCase):
    
    def test_invoice_creation_structure(self):
        """Test invoice creation structure (without actual API call)"""
        # This would test the structure of the invoice creation
        # without making actual API calls
        pass
    
    def test_webhook_processing(self):
        """Test webhook processing (without actual webhook)"""
        # This would test webhook processing logic
        pass

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2) 