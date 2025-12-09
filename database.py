# database.py - مدیریت دیتابیس کامل
import sqlite3
import os
import jdatetime

def get_db_path():
    """مسیر دیتابیس"""
    if os.path.exists('/app/data'):
        return '/app/data/financial_bot.db'
    return 'financial_bot.db'

def get_connection():
    """اتصال به دیتابیس"""
    return sqlite3.connect(get_db_path())

def init_db():
    """ایجاد جداول"""
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
            date TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized at: {get_db_path()}")

def add_user(user_id, username=None, first_name=None):
    """افزودن کاربر"""
    conn = get_connection()
    cursor = conn.cursor()
    now = jdatetime.datetime.now().strftime('%Y/%m/%d %H:%M')
    cursor.execute('INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?)',
                   (user_id, username, first_name, now))
    conn.commit()
    conn.close()

def add_transaction(user_id, amount, trans_type, category, description=""):
    """افزودن تراکنش"""
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
    """دریافت تراکنش‌ها"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT amount, type, category, description, date
        FROM transactions WHERE user_id = ?
        ORDER BY id DESC LIMIT ?
    ''', (user_id, limit))
    results = cursor.fetchall()
    conn.close()
    return results

def get_transactions_with_id(user_id, limit=10):
    """دریافت تراکنش‌ها با ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, amount, type, category, description, date
        FROM transactions WHERE user_id = ?
        ORDER BY id DESC LIMIT ?
    ''', (user_id, limit))
    results = cursor.fetchall()
    conn.close()
    return results

def get_transaction_by_id(transaction_id):
    """دریافت یک تراکنش"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM transactions WHERE id = ?', (transaction_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_user_balance(user_id):
    """موجودی کاربر"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE user_id = ? AND type = ?', 
                   (user_id, 'income'))
    income = cursor.fetchone()[0]
    cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE user_id = ? AND type = ?', 
                   (user_id, 'expense'))
    expense = cursor.fetchone()[0]
    conn.close()
    return {'income': income, 'expense': expense, 'balance': income - expense}

def delete_transaction(transaction_id, user_id=None):
    """حذف تراکنش"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
    conn.commit()
    conn.close()

def update_transaction(transaction_id, **kwargs):
    """بروزرسانی تراکنش"""
    conn = get_connection()
    cursor = conn.cursor()
    for key, value in kwargs.items():
        cursor.execute(f'UPDATE transactions SET {key} = ? WHERE id = ?', (value, transaction_id))
    conn.commit()
    conn.close()

def search_transactions(user_id, query):
    """جستجو"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, amount, type, category, description, date
        FROM transactions WHERE user_id = ? AND (category LIKE ? OR description LIKE ?)
        ORDER BY id DESC
    ''', (user_id, f'%{query}%', f'%{query}%'))
    results = cursor.fetchall()
    conn.close()
    return results

def get_monthly_report(user_id, year, month):
    """گزارش ماهانه"""
    conn = get_connection()
    cursor = conn.cursor()
    pattern = f'{year}/{month}%'
    cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE user_id = ? AND type = ? AND date LIKE ?',
                   (user_id, 'income', pattern))
    income = cursor.fetchone()[0]
    cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE user_id = ? AND type = ? AND date LIKE ?',
                   (user_id, 'expense', pattern))
    expense = cursor.fetchone()[0]
    conn.close()
    return {'income': income, 'expense': expense}

def get_user_stats(user_id):
    """آمار کاربر"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM transactions WHERE user_id = ?', (user_id,))
    count = cursor.fetchone()[0]
    data = get_user_balance(user_id)
    conn.close()
    return {'count': count, **data}

def delete_all_transactions(user_id):
    """حذف همه"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transactions WHERE user_id = ?', (user_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted

# ⭐ Alias برای سازگاری با bot.py
create_tables = init_db
get_balance = get_user_balance

# اجرای اولیه
init_db()
