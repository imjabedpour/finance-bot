# database.py - مدیریت دیتابیس مالی
import sqlite3
import jdatetime


def get_connection():
    """ایجاد اتصال به دیتابیس"""
    return sqlite3.connect('financial_bot.db')


def create_tables():
    """ساخت جداول دیتابیس"""
    conn = get_connection()
    cursor = conn.cursor()

    # جدول کاربران
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # جدول تراکنش‌ها
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL,
            category TEXT DEFAULT 'سایر',
            description TEXT DEFAULT '',
            date TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ جداول دیتابیس ایجاد شد.")


def add_user(user_id, username=None, first_name=None):
    """افزودن کاربر جدید"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
        ''', (user_id, username, first_name))
        conn.commit()
    except Exception as e:
        print(f"خطا در افزودن کاربر: {e}")
    finally:
        conn.close()


def add_transaction(user_id, amount, trans_type, category="سایر", description=""):
    """افزودن تراکنش جدید"""
    conn = get_connection()
    cursor = conn.cursor()

    # تاریخ شمسی
    now = jdatetime.datetime.now()
    date_str = now.strftime("%Y/%m/%d %H:%M")

    try:
        cursor.execute('''
            INSERT INTO transactions (user_id, amount, type, category, description, date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, amount, trans_type, category, description, date_str))
        conn.commit()
        return True
    except Exception as e:
        print(f"خطا در افزودن تراکنش: {e}")
        return False
    finally:
        conn.close()


def get_balance(user_id):
    """محاسبه موجودی کاربر"""
    conn = get_connection()
    cursor = conn.cursor()

    # کل درآمد
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) FROM transactions
        WHERE user_id = ? AND type = 'income'
    ''', (user_id,))
    total_income = cursor.fetchone()[0]

    # کل هزینه
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) FROM transactions
        WHERE user_id = ? AND type = 'expense'
    ''', (user_id,))
    total_expense = cursor.fetchone()[0]

    conn.close()

    return {
        'income': int(total_income),
        'expense': int(total_expense),
        'balance': int(total_income - total_expense)
    }


def get_user_transactions(user_id, limit=10):
    """دریافت آخرین تراکنش‌های کاربر"""
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


# ================== توابع پنل مدیریت ==================

def get_transactions_with_id(user_id, limit=10):
    """دریافت تراکنش‌ها همراه با ID"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, amount, type, category, description, date
        FROM transactions
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
    ''', (user_id, limit))

    results = cursor.fetchall()
    conn.close()
    return results


def get_transaction_by_id(transaction_id, user_id):
    """دریافت یک تراکنش خاص"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, amount, type, category, description, date
        FROM transactions
        WHERE id = ? AND user_id = ?
    ''', (transaction_id, user_id))

    result = cursor.fetchone()
    conn.close()
    return result


def delete_transaction(transaction_id, user_id):
    """حذف یک تراکنش"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id FROM transactions
        WHERE id = ? AND user_id = ?
    ''', (transaction_id, user_id))

    if not cursor.fetchone():
        conn.close()
        return False

    cursor.execute('''
        DELETE FROM transactions
        WHERE id = ? AND user_id = ?
    ''', (transaction_id, user_id))

    conn.commit()
    conn.close()
    return True


def delete_all_transactions(user_id):
    """حذف همه تراکنش‌های کاربر"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        DELETE FROM transactions
        WHERE user_id = ?
    ''', (user_id,))

    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted


def update_transaction(transaction_id, user_id, field, value):
    """ویرایش یک فیلد از تراکنش"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id FROM transactions
        WHERE id = ? AND user_id = ?
    ''', (transaction_id, user_id))

    if not cursor.fetchone():
        conn.close()
        return False

    allowed_fields = ['amount', 'category', 'description']
    if field not in allowed_fields:
        conn.close()
        return False

    cursor.execute(f'''
        UPDATE transactions
        SET {field} = ?
        WHERE id = ? AND user_id = ?
    ''', (value, transaction_id, user_id))

    conn.commit()
    conn.close()
    return True


def search_transactions(user_id, keyword):
    """جستجو در تراکنش‌ها"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, amount, type, category, description, date
        FROM transactions
        WHERE user_id = ? AND (
            category LIKE ? OR
            description LIKE ?
        )
        ORDER BY id DESC
        LIMIT 20
    ''', (user_id, f'%{keyword}%', f'%{keyword}%'))

    results = cursor.fetchall()
    conn.close()
    return results


def get_monthly_report(user_id, year, month):
    """گزارش ماهانه"""
    conn = get_connection()
    cursor = conn.cursor()

    date_pattern = f"{year}/{month:02d}%"

    # درآمد ماه
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) FROM transactions
        WHERE user_id = ? AND type = 'income' AND date LIKE ?
    ''', (user_id, date_pattern))
    income = cursor.fetchone()[0]

    # هزینه ماه
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) FROM transactions
        WHERE user_id = ? AND type = 'expense' AND date LIKE ?
    ''', (user_id, date_pattern))
    expense = cursor.fetchone()[0]

    # هزینه به تفکیک دسته
    cursor.execute('''
        SELECT category, SUM(amount) FROM transactions
        WHERE user_id = ? AND type = 'expense' AND date LIKE ?
        GROUP BY category
        ORDER BY SUM(amount) DESC
    ''', (user_id, date_pattern))
    categories = cursor.fetchall()

    # تعداد تراکنش‌ها
    cursor.execute('''
        SELECT COUNT(*) FROM transactions
        WHERE user_id = ? AND date LIKE ?
    ''', (user_id, date_pattern))
    count = cursor.fetchone()[0]

    conn.close()

    return {
        'income': int(income),
        'expense': int(expense),
        'balance': int(income - expense),
        'categories': categories,
        'count': count
    }


def get_user_stats(user_id):
    """آمار کلی کاربر"""
    conn = get_connection()
    cursor = conn.cursor()

    # تعداد کل تراکنش‌ها
    cursor.execute('''
        SELECT COUNT(*) FROM transactions WHERE user_id = ?
    ''', (user_id,))
    total_count = cursor.fetchone()[0]

    # اولین تراکنش
    cursor.execute('''
        SELECT date FROM transactions
        WHERE user_id = ?
        ORDER BY id ASC LIMIT 1
    ''', (user_id,))
    first = cursor.fetchone()
    first_date = first[0] if first else "—"

    # پرهزینه‌ترین دسته
    cursor.execute('''
        SELECT category, SUM(amount) as total FROM transactions
        WHERE user_id = ? AND type = 'expense'
        GROUP BY category
        ORDER BY total DESC LIMIT 1
    ''', (user_id,))
    top_category = cursor.fetchone()

    conn.close()

    return {
        'total_count': total_count,
        'first_date': first_date,
        'top_category': top_category[0] if top_category else "—",
        'top_amount': int(top_category[1]) if top_category else 0
    }


# تست
if __name__ == "__main__":
    create_tables()
    print("✅ دیتابیس آماده است.")
