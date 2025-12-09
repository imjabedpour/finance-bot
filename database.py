# database.py - مدیریت دیتابیس کامل و اصلاح شده
import sqlite3
import os
import jdatetime
from contextlib import contextmanager

# ========================
# مسیر و اتصال دیتابیس
# ========================

def get_db_path():
    """مسیر دیتابیس بر اساس محیط"""
    if os.path.exists('/app/data'):
        return '/app/data/financial_bot.db'
    return 'financial_bot.db'

def get_connection():
    """ایجاد اتصال به دیتابیس"""
    return sqlite3.connect(get_db_path())

@contextmanager
def get_db():
    """Context manager برای اتصال امن"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# ========================
# تاریخ شمسی
# ========================

def get_jalali_date(with_time=True):
    """تاریخ شمسی با فرمت استاندارد"""
    now = jdatetime.datetime.now()
    if with_time:
        return f"{now.year}/{now.month}/{now.day} {now.hour:02d}:{now.minute:02d}"
    return f"{now.year}/{now.month}/{now.day}"

def get_today_pattern():
    """الگوی تاریخ امروز برای LIKE"""
    now = jdatetime.datetime.now()
    return f"{now.year}/{now.month}/{now.day}%"

# ========================
# ایجاد جداول
# ========================

def init_db():
    """ایجاد جداول دیتابیس"""
    with get_db() as conn:
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
        
        # ایندکس برای جستجوی سریع‌تر
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_transactions_user 
            ON transactions (user_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_transactions_date 
            ON transactions (date)
        ''')
        
    print(f"✅ Database initialized at: {get_db_path()}")

# ========================
# مدیریت کاربران
# ========================

def add_user(user_id, username=None, first_name=None):
    """افزودن کاربر جدید"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?)',
            (user_id, username, first_name, get_jalali_date())
        )

def get_user(user_id):
    """دریافت اطلاعات کاربر"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()

# ========================
# مدیریت تراکنش‌ها
# ========================

def add_transaction(user_id, amount, trans_type, category, description=""):
    """افزودن تراکنش جدید"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO transactions (user_id, amount, type, category, description, date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, amount, trans_type, category, description, get_jalali_date()))
        return cursor.lastrowid

def get_user_transactions(user_id, limit=10):
    """دریافت تراکنش‌های کاربر"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT amount, type, category, description, date
            FROM transactions WHERE user_id = ?
            ORDER BY id DESC LIMIT ?
        ''', (user_id, limit))
        return cursor.fetchall()

def get_transactions_with_id(user_id, limit=10):
    """دریافت تراکنش‌ها با شناسه"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, amount, type, category, description, date
            FROM transactions WHERE user_id = ?
            ORDER BY id DESC LIMIT ?
        ''', (user_id, limit))
        return cursor.fetchall()

def get_transaction_by_id(transaction_id, user_id=None):
    """دریافت یک تراکنش با شناسه"""
    with get_db() as conn:
        cursor = conn.cursor()
        if user_id:
            cursor.execute(
                'SELECT * FROM transactions WHERE id = ? AND user_id = ?',
                (transaction_id, user_id)
            )
        else:
            cursor.execute(
                'SELECT * FROM transactions WHERE id = ?',
                (transaction_id,)
            )
        return cursor.fetchone()

def delete_transaction(transaction_id, user_id=None):
    """حذف تراکنش"""
    with get_db() as conn:
        cursor = conn.cursor()
        if user_id:
            cursor.execute(
                'DELETE FROM transactions WHERE id = ? AND user_id = ?',
                (transaction_id, user_id)
            )
        else:
            cursor.execute(
                'DELETE FROM transactions WHERE id = ?',
                (transaction_id,)
            )
        return cursor.rowcount > 0

def update_transaction(transaction_id, **kwargs):
    """بروزرسانی تراکنش"""
    if not kwargs:
        return False
    
    with get_db() as conn:
        cursor = conn.cursor()
        set_clause = ', '.join([f'{k} = ?' for k in kwargs.keys()])
        values = list(kwargs.values()) + [transaction_id]
        cursor.execute(
            f'UPDATE transactions SET {set_clause} WHERE id = ?',
            values
        )
        return cursor.rowcount > 0

def search_transactions(user_id, query):
    """جستجو در تراکنش‌ها"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, amount, type, category, description, date
            FROM transactions 
            WHERE user_id = ? AND (category LIKE ? OR description LIKE ?)
            ORDER BY id DESC
        ''', (user_id, f'%{query}%', f'%{query}%'))
        return cursor.fetchall()

def delete_all_transactions(user_id):
    """حذف همه تراکنش‌های کاربر"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM transactions WHERE user_id = ?',
            (user_id,)
        )
        return cursor.rowcount

# ========================
# گزارشات
# ========================

def get_user_balance(user_id):
    """موجودی کاربر"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE user_id = ? AND type = ?',
            (user_id, 'income')
        )
        income = cursor.fetchone()[0]
        
        cursor.execute(
            'SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE user_id = ? AND type = ?',
            (user_id, 'expense')
        )
        expense = cursor.fetchone()[0]
        
        return {
            'income': income,
            'expense': expense,
            'balance': income - expense
        }

def get_daily_summary(user_id, date_pattern=None):
    """خلاصه روزانه"""
    if date_pattern is None:
        date_pattern = get_today_pattern()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0)
            FROM transactions 
            WHERE user_id = ? AND type = 'income' AND date LIKE ?
        ''', (user_id, date_pattern))
        income = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0)
            FROM transactions 
            WHERE user_id = ? AND type = 'expense' AND date LIKE ?
        ''', (user_id, date_pattern))
        expense = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*)
            FROM transactions 
            WHERE user_id = ? AND date LIKE ?
        ''', (user_id, date_pattern))
        count = cursor.fetchone()[0]
        
        return {
            'income': income,
            'expense': expense,
            'balance': income - expense,
            'count': count
        }

def get_daily_transactions(user_id, date_pattern=None, limit=10):
    """تراکنش‌های روزانه"""
    if date_pattern is None:
        date_pattern = get_today_pattern()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, amount, type, category, description, date
            FROM transactions 
            WHERE user_id = ? AND date LIKE ?
            ORDER BY id DESC LIMIT ?
        ''', (user_id, date_pattern, limit))
        return cursor.fetchall()

def get_daily_expenses_by_category(user_id, date_pattern=None):
    """هزینه‌های روزانه بر اساس دسته‌بندی"""
    if date_pattern is None:
        date_pattern = get_today_pattern()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT category, SUM(amount)
            FROM transactions 
            WHERE user_id = ? AND type = 'expense' AND date LIKE ?
            GROUP BY category
            ORDER BY SUM(amount) DESC
        ''', (user_id, date_pattern))
        return cursor.fetchall()

def get