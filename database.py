# database.py - مدیریت دیتابیس با پشتیبانی Volume
import sqlite3
import os
import jdatetime

def get_db_path():
    """مسیر دیتابیس"""
    # اگر پوشه data وجود داره (Railway Volume)
    if os.path.exists('/app/data'):
        return '/app/data/financial_bot.db'
    # مسیر محلی
    return 'financial_bot.db'

def get_connection():
    """ایجاد اتصال به دیتابیس"""
    db_path = get_db_path()
    return sqlite3.connect(db_path)

def init_db():
    """ایجاد جداول دیتابیس"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            created_at TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            type TEXT,
            category TEXT,
            description TEXT,
            date TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized at: {get_db_path()}")

def add_user(user_id, username, first_name):
    """اضافه کردن کاربر جدید"""
    conn = get_connection()
    cursor = conn.cursor()
    now = jdatetime.datetime.now().strftime('%Y/%m/%d %H:%M')
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, created_at)
        VALUES (?, ?, ?, ?)
    ''', (user_id, username, first_name, now))
    conn.commit()
    conn.close()

def add_transaction(user_id, amount, trans_type, category, description=""):
    """اضافه کردن تراکنش جدید"""
    conn = get_connection()
    cursor = conn.cursor()
    now = jdatetime.datetime.now().strftime('%Y/%m/%d %H:%M')
    cursor.execute('''
        INSERT INTO transactions (user_id, amount, type, category, description, date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, amount, trans_type, category, description, now))
    conn.commit()
    conn.close()

def get_user_transactions(user_id, limit=10):
    """دریافت تراکنش‌های کاربر"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT amount, type, category, description, date
        FROM transactions
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
    ''', (user_id, limit))
    results = cursor.fetchall()
    conn.close()
    return results

def get_user_balance(user_id):
    """محاسبه موجودی کاربر"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE user_id = ? AND type = ?', (user_id, 'income'))
    total_income = cursor.fetchone()[0]
    
    cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE user_id = ? AND type = ?', (user_id, 'expense'))
    total_expense = cursor.fetchone()[0]
    
    conn.close()
    return {'income': total_income, 'expense': total_expense, 'balance': total_income - total_expense}

# اجرای اولیه
init_db()
