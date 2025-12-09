import sqlite3

conn = sqlite3.connect('financial_bot.db')
cursor = conn.cursor()

print("=" * 50)
print("📅 تاریخ‌های ذخیره شده در دیتابیس:")
print("=" * 50)

cursor.execute("SELECT id, date, amount, type FROM transactions ORDER BY id DESC LIMIT 10")

for row in cursor.fetchall():
    print(f"ID: {row[0]} | Date: '{row[1]}' | Amount: {row[2]} | Type: {row[3]}")

conn.close()
