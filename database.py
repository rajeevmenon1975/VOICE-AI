import sqlite3
import os
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trader.db")

def get_connection():
    return sqlite3.connect(DATABASE_PATH)

def init_db():
    """Initializes the SQLite database with compliant schemas and seeding mock data."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Clients Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        client_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        preferred_lang TEXT NOT NULL, -- 'English', 'Hindi', 'Gujarati'
        ledger_balance REAL NOT NULL,
        activated_segments TEXT NOT NULL -- Comma-separated list: 'EQUITY,F&O'
    )
    """)

    # 2. Stocks Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stocks (
        symbol TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        current_price REAL NOT NULL,
        is_banned INTEGER NOT NULL DEFAULT 0, -- 1 = Banned from trading, 0 = Active
        is_penny INTEGER NOT NULL DEFAULT 0  -- 1 = Penny/high-risk stock, 0 = Standard
    )
    """)

    # 3. Order Logs Table (Audit log for compliance and complaints handling)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_logs (
        order_id TEXT PRIMARY KEY,
        client_id TEXT NOT NULL,
        symbol TEXT NOT NULL,
        action TEXT NOT NULL, -- 'BUY' or 'SELL'
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        order_type TEXT NOT NULL, -- 'MARKET' or 'LIMIT'
        product_type TEXT NOT NULL, -- 'CNC' (Delivery) or 'MIS' (Intraday)
        status TEXT NOT NULL, -- 'PENDING', 'COMPLETED', 'REJECTED'
        rejection_reason TEXT,
        otp_used TEXT,
        recording_url TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (client_id) REFERENCES clients(client_id)
    )
    """)

    # 4. Call Logs Table (SEBI compliance telemetric logs)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS call_logs (
        call_id TEXT PRIMARY KEY,
        client_id TEXT NOT NULL,
        phone TEXT NOT NULL,
        call_type TEXT NOT NULL, -- 'OUTBOUND_PITCH' or 'CALLBACK_CONFIRM'
        recording_url TEXT NOT NULL,
        transcript TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (client_id) REFERENCES clients(client_id)
    )
    """)

    # Seed Mock Data if tables are empty
    cursor.execute("SELECT COUNT(*) FROM clients")
    if cursor.fetchone()[0] == 0:
        clients_data = [
            ("CLIENT_123", "Rajeev Menon", "+919876543210", "English", 150000.00, "EQUITY,F&O"),
            ("CLIENT_456", "Amit Patel", "+919988776655", "Gujarati", 40000.00, "EQUITY"),
            ("CLIENT_789", "Priya Sharma", "+919123456789", "Hindi", 12000.00, "EQUITY")
        ]
        cursor.executemany("INSERT INTO clients VALUES (?, ?, ?, ?, ?, ?)", clients_data)

    cursor.execute("SELECT COUNT(*) FROM stocks")
    if cursor.fetchone()[0] == 0:
        stocks_data = [
            ("RELIANCE", "Reliance Industries Ltd", 2800.00, 0, 0),
            ("TCS", "Tata Consultancy Services Ltd", 3850.00, 0, 0),
            ("ITC", "ITC Limited", 430.00, 0, 0),
            ("IDEA", "Vodafone Idea Ltd", 12.40, 0, 1), # Penny stock
            ("GTLINFRA", "GTL Infrastructure Ltd", 1.85, 1, 1) # Banned and Penny stock
        ]
        cursor.executemany("INSERT INTO stocks VALUES (?, ?, ?, ?, ?)", stocks_data)

    conn.commit()
    conn.close()

# Data Access APIs

def get_client(client_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clients WHERE client_id = ?", (client_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_stock(symbol):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stocks WHERE symbol = ?", (symbol.upper(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_client_balance(client_id, new_balance):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE clients SET ledger_balance = ? WHERE client_id = ?", (new_balance, client_id))
    conn.commit()
    conn.close()

def log_order(order_id, client_id, symbol, action, quantity, price, order_type, product_type, status, rejection_reason=None, otp_used=None, recording_url=None):
    conn = get_connection()
    cursor = conn.cursor()
    created_at = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO order_logs (order_id, client_id, symbol, action, quantity, price, order_type, product_type, status, rejection_reason, otp_used, recording_url, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (order_id, client_id, symbol.upper(), action.upper(), quantity, price, order_type.upper(), product_type.upper(), status.upper(), rejection_reason, otp_used, recording_url, created_at))
    conn.commit()
    conn.close()

def log_call(call_id, client_id, phone, call_type, recording_url, transcript):
    conn = get_connection()
    cursor = conn.cursor()
    created_at = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO call_logs (call_id, client_id, phone, call_type, recording_url, transcript, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (call_id, client_id, phone, call_type, recording_url, transcript, created_at))
    conn.commit()
    conn.close()

def get_order_logs(client_id=None):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if client_id:
        cursor.execute("SELECT * FROM order_logs WHERE client_id = ? ORDER BY created_at DESC", (client_id,))
    else:
        cursor.execute("SELECT * FROM order_logs ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Auto-initialize database on import
init_db()
