# bot.py - ربات مدیریت مالی با پنل مدیریت کامل
import os
import sqlite3
import datetime
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, 
    ContextTypes, CallbackQueryHandler, ConversationHandler
)
from dotenv import load_dotenv
import jdatetime
from database import (
    create_tables, add_user, add_transaction, get_balance, 
    get_user_transactions, get_transactions_with_id, get_transaction_by_id,
    delete_transaction, update_transaction, search_transactions,
    get_monthly_report, get_user_stats, delete_all_transactions
)
from sms_parser import parse_bank_sms
from charts import create_pie_chart, create_bar_chart

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# مراحل مکالمه
AMOUNT, CATEGORY, DESCRIPTION = range(3)

# دسته‌بندی‌ها
EXPENSE_CATEGORIES = [
    ("🍔 خوراک", "خوراک"),
    ("🚗 حمل‌ونقل", "حمل‌ونقل"),
    ("🏠 قبوض", "قبوض"),
    ("🛒 خرید", "خرید"),
    ("🎬 تفریح", "تفریح"),
    ("💊 سلامت", "سلامت"),
    ("📚 آموزش", "آموزش"),
    ("📦 سایر", "سایر"),
]

INCOME_CATEGORIES = [
    ("💰 حقوق", "حقوق"),
    ("🎁 هدیه", "هدیه"),
    ("📈 سرمایه‌گذاری", "سرمایه‌گذاری"),
    ("💼 پروژه", "پروژه"),
    ("📦 سایر", "سایر"),
]
# ================== دستورات اصلی ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username, user.first_name)

    welcome = f"""
سلام **{user.first_name}**! 👋

به **ربات مدیریت مالی** خوش اومدی! 💰

✨ **امکانات:**
├ 📱 ثبت خودکار از SMS بانک
├ ➕ ثبت دستی درآمد/هزینه
├ 💵 مشاهده موجودی
├ 📊 نمودار
└ ⚙️ مدیریت کامل تراکنش‌ها

📲 **برای ثبت خودکار:**
پیام بانک رو مستقیم فوروارد کن!
"""

    keyboard = [
        [
            InlineKeyboardButton("➕ ثبت هزینه", callback_data="new_expense"),
            InlineKeyboardButton("➕ ثبت درآمد", callback_data="new_income"),
        ],
        [
            InlineKeyboardButton("💵 موجودی", callback_data="balance"),
            InlineKeyboardButton("📋 تراکنش‌ها", callback_data="transactions"),
        ],
        [
            InlineKeyboardButton("📊 نمودار", callback_data="chart"),
            InlineKeyboardButton("📅 امروز", callback_data="daily_report"),
        ],
        [
            InlineKeyboardButton("⚙️ مدیریت", callback_data="manage"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome, parse_mode='Markdown', reply_markup=reply_markup)



async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📚 **راهنمای ربات:**

**🔹 ثبت خودکار:**
پیام SMS بانک رو فوروارد کن، خودم تشخیص میدم!

**🔹 دستورات:**
/start - منوی اصلی
/balance - موجودی
/transactions - لیست تراکنش‌ها
/expense - ثبت هزینه دستی
/income - ثبت درآمد دستی
/chart - نمودار
/manage - پنل مدیریت

**🔹 بانک‌های پشتیبانی:**
ملت، ملی، صادرات، سامان، پاسارگاد، تجارت، سپه و...
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بازگشت به منوی اصلی"""
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    welcome = f"""
سلام **{user.first_name}**! 👋

به **ربات مدیریت مالی** خوش اومدی! 💰

✨ **امکانات:**
├ 📱 ثبت خودکار از پیامک بانک
├ ➕ ثبت دستی درآمد/هزینه
├ 💵 مشاهده موجودی
├ 📋 لیست تراکنش‌ها
├ 📊 نمودار هزینه‌ها
└ ⚙️ پنل مدیریت

📲 **برای ثبت خودکار:**
پیام بانک رو مستقیم فوروارد کن!
"""

    keyboard = [
        [
            InlineKeyboardButton("➕ ثبت هزینه", callback_data="new_expense"),
            InlineKeyboardButton("➕ ثبت درآمد", callback_data="new_income"),
        ],
        [
            InlineKeyboardButton("💵 موجودی", callback_data="balance"),
            InlineKeyboardButton("📋 تراکنش‌ها", callback_data="transactions"),
        ],
        [
            InlineKeyboardButton("📊 نمودار", callback_data="chart"),
            InlineKeyboardButton("📅 امروز", callback_data="daily_report"),
        ],
        [
            InlineKeyboardButton("⚙️ مدیریت", callback_data="manage"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(welcome, parse_mode='Markdown', reply_markup=reply_markup)

# ================== موجودی ==================

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = get_balance(user_id)

    text = f"""
💵 **وضعیت مالی شما:**

├ 📈 کل درآمد: **{data['income']:,}** ریال
├ 📉 کل هزینه: **{data['expense']:,}** ریال
└ 💰 موجودی: **{data['balance']:,}** ریال
"""
    await update.message.reply_text(text, parse_mode='Markdown')


async def balance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    data = get_balance(user_id)

    text = f"""
💵 **وضعیت مالی شما:**

├ 📈 کل درآمد: **{data['income']:,}** ریال
├ 📉 کل هزینه: **{data['expense']:,}** ریال
└ 💰 موجودی: **{data['balance']:,}** ریال
"""
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)


# ================== لیست تراکنش‌ها ==================

async def transactions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    transactions = get_user_transactions(user_id, 5)  # تغییر از 10 به 5

    if not transactions:
        await update.message.reply_text("📭 هنوز تراکنشی ثبت نکردی!")
        return

    text = "📋 **5 تراکنش آخر:**\n\n"
    for t in transactions:
        amount, t_type, category, desc, date = t
        emoji = "🟢" if t_type == "income" else "🔴"
        sign = "+" if t_type == "income" else "-"
        text += f"{emoji} {sign}{amount:,} | {category} | {date}\n"

    await update.message.reply_text(text, parse_mode='Markdown')



async def transactions_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    transactions = get_user_transactions(user_id, 5)  # تغییر از 10 به 5

    if not transactions:
        await query.edit_message_text("📭 هنوز تراکنشی ثبت نکردی!")
        return

    text = "📋 **5 تراکنش آخر:**\n\n"
    for t in transactions:
        amount, t_type, category, desc, date = t
        emoji = "🟢" if t_type == "income" else "🔴"
        sign = "+" if t_type == "income" else "-"
        text += f"{emoji} {sign}{amount:,} | {category} | {date}\n"

    keyboard = [
        [InlineKeyboardButton("📄 همه تراکنش‌ها", callback_data="all_transactions_0")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)



# ========== اینجا اضافه کن ==========

async def all_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش همه تراکنش‌ها با صفحه‌بندی"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    
    # گرفتن شماره صفحه از callback_data
    page = int(query.data.replace("all_transactions_", ""))
    per_page = 10  # تعداد در هر صفحه

    conn = sqlite3.connect('financial_bot.db')
    cursor = conn.cursor()

    # گرفتن تعداد کل تراکنش‌ها
    cursor.execute('SELECT COUNT(*) FROM transactions WHERE user_id = ?', (user_id,))
    total_count = cursor.fetchone()[0]

    # محاسبه تعداد صفحات
    total_pages = (total_count + per_page - 1) // per_page
    if total_pages == 0:
        total_pages = 1

    # گرفتن تراکنش‌های این صفحه
    offset = page * per_page
    cursor.execute('''
        SELECT amount, type, category, description, date
        FROM transactions
        WHERE user_id = ?
        ORDER BY date DESC
        LIMIT ? OFFSET ?
    ''', (user_id, per_page, offset))
    transactions = cursor.fetchall()
    conn.close()

    if not transactions:
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="transactions")]]
        await query.edit_message_text(
            "📭 تراکنشی وجود نداره!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    text = f"📋 **همه تراکنش‌ها** (صفحه {page + 1} از {total_pages})\n\n"

    for t in transactions:
        amount, t_type, category, desc, date = t
        emoji = "🟢" if t_type == "income" else "🔴"
        sign = "+" if t_type == "income" else "-"
        text += f"{emoji} {sign}{amount:,} | {category} | {date}\n"

    text += f"\n📊 مجموع: {total_count} تراکنش"

    # دکمه‌های صفحه‌بندی
    keyboard = []
    nav_row = []

    if page > 0:
        nav_row.append(InlineKeyboardButton("◀️ قبلی", callback_data=f"all_transactions_{page - 1}"))

    nav_row.append(InlineKeyboardButton(f"📄 {page + 1}/{total_pages}", callback_data="ignore"))

    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("بعدی ▶️", callback_data=f"all_transactions_{page + 1}"))

    keyboard.append(nav_row)
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="transactions")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)


# ================== نمودار ==================

async def chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش نمودار هزینه‌ها"""
    user_id = update.effective_user.id

    if update.callback_query:
        await update.callback_query.answer()
        msg = await update.callback_query.edit_message_text("📊 در حال ساخت نمودار...")
    else:
        msg = await update.message.reply_text("📊 در حال ساخت نمودار...")

    conn = sqlite3.connect('financial_bot.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, user_id, amount, type, category, description, date
        FROM transactions
        WHERE user_id = ?
        ORDER BY date DESC
    ''', (user_id,))

    transactions_list = cursor.fetchall()
    conn.close()

    if not transactions_list:
        await msg.edit_text("❌ هنوز تراکنشی ثبت نشده!")
        return

    # ساخت نمودار دایره‌ای
    pie_chart = create_pie_chart(transactions_list)
    if pie_chart:
        await update.effective_chat.send_photo(
            photo=pie_chart,
            caption="📊 نمودار هزینه‌ها بر اساس دسته‌بندی"
        )

    # ساخت نمودار میله‌ای
    bar_chart = create_bar_chart(transactions_list)
    if bar_chart:
        await update.effective_chat.send_photo(
            photo=bar_chart,
            caption="📈 مقایسه درآمد و هزینه"
        )

    if not pie_chart and not bar_chart:
        await msg.edit_text("❌ داده‌ای برای نمایش نمودار وجود ندارد.")
    else:
        await msg.delete()


async def chart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """کالبک نمودار از دکمه"""
    await chart(update, context)


# ================== پردازش SMS بانکی ==================

async def process_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش همه پیام‌های متنی"""
    
    # چک کردن اگه ادمین منتظر آیدی کاربر هست
    if context.user_data.get('admin_waiting_user_id'):
        handled = await admin_show_user_transactions(update, context)
        if handled:
            return
    text = update.message.text
    user_id = update.effective_user.id

    # تحلیل پیام بانکی
    result = parse_bank_sms(text)

    if result['amount'] and result['type']:
        # ذخیره موقت
        context.user_data['sms_data'] = result

        type_emoji = "🔴 هزینه" if result['type'] == 'expense' else "🟢 درآمد"
        bank_text = f"🏦 بانک: {result['bank']}" if result['bank'] else ""
        desc_text = f"📝 توضیح: {result['description']}" if result['description'] else ""
        balance_text = f"💰 مانده: {result['balance']:,} ریال" if result['balance'] else ""

        msg = f"""
📱 **پیام بانکی شناسایی شد!**

{type_emoji}
💵 مبلغ: **{result['amount']:,}** ریال
{bank_text}
{desc_text}
{balance_text}

✅ ثبت بشه؟
"""

        keyboard = [
            [
                InlineKeyboardButton("✅ بله، ثبت کن", callback_data="confirm_sms"),
                InlineKeyboardButton("❌ انصراف", callback_data="cancel_sms"),
            ],
            [
                InlineKeyboardButton("✏️ ویرایش دسته‌بندی", callback_data="edit_category_sms"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        await update.message.reply_text(
            "🤔 متوجه نشدم!\n\n"
            "اگه پیام بانک بود، مطمئن شو کامل فوروارد کردی.\n"
            "یا از /start برای منوی اصلی استفاده کن."
        )


async def confirm_sms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تأیید و ثبت SMS"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    data = context.user_data.get('sms_data')

    if not data:
        await query.edit_message_text("❌ خطا! لطفاً دوباره پیام رو بفرست.")
        return

    if data['type'] == 'expense':
        category = data.get('category', 'خرید')
    else:
        category = data.get('category', 'سایر')

    description = data.get('description', '')
    if data['bank']:
        description = f"{data['bank']} - {description}" if description else data['bank']

    add_transaction(user_id, data['amount'], data['type'], category, description)

    type_text = "هزینه" if data['type'] == 'expense' else "درآمد"
    emoji = "💸" if data['type'] == 'expense' else "💰"

    await query.edit_message_text(
        f"{emoji} **{type_text} ثبت شد!**\n\n"
        f"💵 مبلغ: **{data['amount']:,}** ریال\n"
        f"📁 دسته: {category}",
        parse_mode='Markdown'
    )

    context.user_data.pop('sms_data', None)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو عملیات"""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ عملیات لغو شد.\n\nبرای شروع مجدد: /start"
    )
    return ConversationHandler.END

# ↓↓↓ دقیقاً اینجا اضافه کن ↓↓↓

async def cancel_transaction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """انصراف از ثبت تراکنش با دکمه"""
    query = update.callback_query
    await query.answer()
    
    context.user_data.clear()
    
    await query.edit_message_text(
        "❌ عملیات لغو شد.\n\nبرای شروع مجدد: /start"
    )
    
    return ConversationHandler.END

async def cancel_sms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """انصراف از ثبت SMS"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ ثبت لغو شد.")
    context.user_data.pop('sms_data', None)


async def confirm_sms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تأیید و ثبت SMS"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    data = context.user_data.get('sms_data')

    if not data:
        await query.edit_message_text("❌ خطا! لطفاً دوباره پیام رو بفرست.")
        return

    if data['type'] == 'expense':
        category = data.get('category', 'خرید')
    else:
        category = data.get('category', 'سایر')

    description = data.get('description', '')
    if data['bank']:
        description = f"{data['bank']} - {description}" if description else data['bank']

    add_transaction(user_id, data['amount'], data['type'], category, description)

    type_text = "هزینه" if data['type'] == 'expense' else "درآمد"
    emoji = "💸" if data['type'] == 'expense' else "💰"

    await query.edit_message_text(
        f"{emoji} **{type_text} ثبت شد!**\n\n"
        f"💵 مبلغ: **{data['amount']:,}** ریال\n"
        f"📁 دسته: {category}",
        parse_mode='Markdown'
    )

    context.user_data.pop('sms_data', None)


async def edit_category_sms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ویرایش دسته‌بندی SMS"""
    query = update.callback_query
    await query.answer()

    data = context.user_data.get('sms_data')
    if not data:
        await query.edit_message_text("❌ خطا!")
        return

    if data['type'] == 'expense':
        categories = EXPENSE_CATEGORIES
    else:
        categories = INCOME_CATEGORIES

    keyboard = []
    row = []
    for emoji_name, value in categories:
        row.append(InlineKeyboardButton(emoji_name, callback_data=f"smscat_{value}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("📁 دسته‌بندی رو انتخاب کن:", reply_markup=reply_markup)


async def sms_category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """انتخاب دسته‌بندی برای SMS"""
    query = update.callback_query
    await query.answer()

    category = query.data.replace("smscat_", "")
    data = context.user_data.get('sms_data')

    if not data:
        await query.edit_message_text("❌ خطا!")
        return

    data['category'] = category
    user_id = update.effective_user.id

    description = data.get('description', '')
    if data['bank']:
        description = f"{data['bank']} - {description}" if description else data['bank']

    add_transaction(user_id, data['amount'], data['type'], category, description)

    type_text = "هزینه" if data['type'] == 'expense' else "درآمد"
    emoji = "💸" if data['type'] == 'expense' else "💰"

    await query.edit_message_text(
        f"{emoji} **{type_text} ثبت شد!**\n\n"
        f"💵 مبلغ: **{data['amount']:,}** ریال\n"
        f"📁 دسته: {category}",
        parse_mode='Markdown'
    )

    context.user_data.pop('sms_data', None)


async def edit_category_sms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ویرایش دسته‌بندی SMS"""
    query = update.callback_query
    await query.answer()

    data = context.user_data.get('sms_data')
    if not data:
        await query.edit_message_text("❌ خطا!")
        return

    if data['type'] == 'expense':
        categories = EXPENSE_CATEGORIES
    else:
        categories = INCOME_CATEGORIES

    keyboard = []
    row = []
    for emoji_name, value in categories:
        row.append(InlineKeyboardButton(emoji_name, callback_data=f"smscat_{value}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("📁 دسته‌بندی رو انتخاب کن:", reply_markup=reply_markup)


async def sms_category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """انتخاب دسته‌بندی برای SMS"""
    query = update.callback_query
    await query.answer()

    category = query.data.replace("smscat_", "")
    data = context.user_data.get('sms_data')

    if not data:
        await query.edit_message_text("❌ خطا!")
        return

    data['category'] = category
    user_id = update.effective_user.id

    description = data.get('description', '')
    if data['bank']:
        description = f"{data['bank']} - {description}" if description else data['bank']

    add_transaction(user_id, data['amount'], data['type'], category, description)

    type_text = "هزینه" if data['type'] == 'expense' else "درآمد"
    emoji = "💸" if data['type'] == 'expense' else "💰"

    await query.edit_message_text(
        f"{emoji} **{type_text} ثبت شد!**\n\n"
        f"💵 مبلغ: **{data['amount']:,}** ریال\n"
        f"📁 دسته: {category}",
        parse_mode='Markdown'
    )

    context.user_data.pop('sms_data', None)
# ================== ثبت دستی هزینه/درآمد ==================

async def expense_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع ثبت هزینه"""
    context.user_data['type'] = 'expense'

    keyboard = [[InlineKeyboardButton("❌ انصراف", callback_data="cancel_transaction")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "💸 **ثبت هزینه جدید**\n\n💵 مبلغ رو به ریال وارد کن:\n\n(مثال: 500000)",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "💸 **ثبت هزینه جدید**\n\n💵 مبلغ رو به ریال وارد کن:\n\n(مثال: 500000)",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    return AMOUNT


async def income_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع ثبت درآمد"""
    context.user_data['type'] = 'income'

    keyboard = [[InlineKeyboardButton("❌ انصراف", callback_data="cancel_transaction")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "💰 **ثبت درآمد جدید**\n\n💵 مبلغ رو به ریال وارد کن:\n\n(مثال: 5000000)",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "💰 **ثبت درآمد جدید**\n\n💵 مبلغ رو به ریال وارد کن:\n\n(مثال: 5000000)",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    return AMOUNT



async def amount_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت مبلغ"""
    text = update.message.text

    # تبدیل اعداد فارسی به انگلیسی
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    english_digits = '0123456789'
    translation_table = str.maketrans(persian_digits, english_digits)
    text = text.translate(translation_table)

    # حذف کاراکترهای اضافی
    text = text.replace(',', '').replace('،', '').replace(' ', '')

    try:
        amount = int(text)
        if amount <= 0:
            raise ValueError

        context.user_data['amount'] = amount

        # نمایش دسته‌بندی‌ها
        if context.user_data['type'] == 'expense':
            categories = EXPENSE_CATEGORIES
            title = "📁 دسته‌بندی هزینه رو انتخاب کن:"
        else:
            categories = INCOME_CATEGORIES
            title = "📁 دسته‌بندی درآمد رو انتخاب کن:"

        keyboard = []
        row = []
        for emoji_name, value in categories:
            row.append(InlineKeyboardButton(emoji_name, callback_data=f"cat_{value}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(title, reply_markup=reply_markup)

        return CATEGORY

    except ValueError:
        await update.message.reply_text(
            "❌ مبلغ نامعتبر!\n\nلطفاً فقط عدد وارد کن (مثال: 500000)"
        )
        return AMOUNT


async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """انتخاب دسته‌بندی"""
    query = update.callback_query
    await query.answer()

    category = query.data.replace("cat_", "")
    context.user_data['category'] = category

    await query.edit_message_text(
        f"📁 دسته: **{category}**\n\n"
        "📝 توضیحات رو بنویس:\n\n(یا /skip برای رد کردن)",
        parse_mode='Markdown'
    )

    return DESCRIPTION


async def description_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت توضیحات و ثبت نهایی"""
    description = update.message.text
    user_id = update.effective_user.id

    amount = context.user_data['amount']
    t_type = context.user_data['type']
    category = context.user_data['category']

    # ثبت در دیتابیس
    add_transaction(user_id, amount, t_type, category, description)

    emoji = "💸" if t_type == 'expense' else "💰"
    type_text = "هزینه" if t_type == 'expense' else "درآمد"

    await update.message.reply_text(
        f"{emoji} **{type_text} ثبت شد!**\n\n"
        f"💵 مبلغ: **{amount:,}** ریال\n"
        f"📁 دسته: {category}\n"
        f"📝 توضیح: {description}",
        parse_mode='Markdown'
    )

    context.user_data.clear()
    return ConversationHandler.END


async def skip_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رد کردن توضیحات"""
    user_id = update.effective_user.id

    amount = context.user_data['amount']
    t_type = context.user_data['type']
    category = context.user_data['category']

    # ثبت در دیتابیس بدون توضیحات
    add_transaction(user_id, amount, t_type, category, "")

    emoji = "💸" if t_type == 'expense' else "💰"
    type_text = "هزینه" if t_type == 'expense' else "درآمد"

    await update.message.reply_text(
        f"{emoji} **{type_text} ثبت شد!**\n\n"
        f"💵 مبلغ: **{amount:,}** ریال\n"
        f"📁 دسته: {category}",
        parse_mode='Markdown'
    )

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو عملیات"""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ عملیات لغو شد.\n\nبرای شروع مجدد: /start"
    )
    return ConversationHandler.END
# ================== پنل مدیریت ==================

# مراحل ویرایش
EDIT_AMOUNT, EDIT_CATEGORY, EDIT_DESCRIPTION = range(10, 13)
DELETE_CONFIRM = 20
SEARCH_TEXT = 30

async def manage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منوی اصلی مدیریت"""
    keyboard = [
        [
            InlineKeyboardButton("📋 لیست تراکنش‌ها", callback_data="manage_list"),
        ],
        [
            InlineKeyboardButton("🔍 جستجو", callback_data="manage_search"),
            InlineKeyboardButton("📊 گزارش ماهانه", callback_data="manage_report"),
        ],
        [
            InlineKeyboardButton("📈 آمار کلی", callback_data="manage_stats"),
            InlineKeyboardButton("🗑️ حذف همه", callback_data="manage_delete_all"),
        ],
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_start"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = """
⚙️ **پنل مدیریت**

از اینجا می‌تونی تراکنش‌هات رو مدیریت کنی:

• 📋 مشاهده و ویرایش تراکنش‌ها
• 🔍 جستجو در تراکنش‌ها
• 📊 گزارش ماهانه
• 📈 آمار کلی
• 🗑️ حذف همه داده‌ها
"""

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text, parse_mode='Markdown', reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text, parse_mode='Markdown', reply_markup=reply_markup
        )


async def manage_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لیست تراکنش‌ها برای مدیریت"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    # گرفتن تراکنش‌ها با id
    conn = sqlite3.connect('financial_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, amount, type, category, description, date
        FROM transactions
        WHERE user_id = ?
        ORDER BY date DESC
        LIMIT 10
    ''', (user_id,))
    transactions = cursor.fetchall()
    conn.close()

    if not transactions:
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="manage")]]
        await query.edit_message_text(
            "📭 هنوز تراکنشی ثبت نکردی!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    text = "📋 **تراکنش‌ها (برای ویرایش/حذف کلیک کن):**\n\n"

    keyboard = []
    for t in transactions:
        t_id, amount, t_type, category, desc, date = t
        emoji = "🟢" if t_type == "income" else "🔴"
        sign = "+" if t_type == "income" else "-"

        text += f"{emoji} {sign}{amount:,} | {category} | {date}\n"

        # دکمه ویرایش و حذف برای هر تراکنش
        keyboard.append([
            InlineKeyboardButton(f"✏️ {amount:,}", callback_data=f"edit_{t_id}"),
            InlineKeyboardButton(f"🗑️", callback_data=f"delete_{t_id}"),
        ])

    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="manage")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)


async def edit_transaction_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع ویرایش تراکنش"""
    query = update.callback_query
    await query.answer()

    t_id = int(query.data.replace("edit_", ""))
    context.user_data['edit_id'] = t_id

    # گرفتن اطلاعات تراکنش
    conn = sqlite3.connect('financial_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT amount, type, category, description, date
        FROM transactions
        WHERE id = ?
    ''', (t_id,))
    t = cursor.fetchone()
    conn.close()

    if not t:
        await query.edit_message_text("❌ تراکنش پیدا نشد!")
        return

    amount, t_type, category, desc, date = t
    emoji = "🟢 درآمد" if t_type == "income" else "🔴 هزینه"

    text = f"""
✏️ **ویرایش تراکنش**

{emoji}
💵 مبلغ: **{amount:,}** ریال
📁 دسته: {category}
📝 توضیح: {desc or '-'}
📅 تاریخ: {date}

**چی رو می‌خوای ویرایش کنی؟**
"""

    keyboard = [
        [
            InlineKeyboardButton("💵 مبلغ", callback_data="edit_field_amount"),
            InlineKeyboardButton("📁 دسته‌بندی", callback_data="edit_field_category"),
        ],
        [
            InlineKeyboardButton("📝 توضیحات", callback_data="edit_field_desc"),
        ],
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data="manage_list"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
# ================== ویرایش فیلدهای تراکنش ==================

async def edit_field_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع ویرایش مبلغ"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "💵 **ویرایش مبلغ**\n\n"
        "مبلغ جدید رو به ریال وارد کن:\n\n"
        "(یا /cancel برای انصراف)",
        parse_mode='Markdown'
    )

    return EDIT_AMOUNT


async def edit_field_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع ویرایش دسته‌بندی"""
    query = update.callback_query
    await query.answer()

    t_id = context.user_data.get('edit_id')

    # گرفتن نوع تراکنش
    conn = sqlite3.connect('financial_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT type FROM transactions WHERE id = ?', (t_id,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        await query.edit_message_text("❌ خطا!")
        return ConversationHandler.END

    t_type = result[0]

    if t_type == 'expense':
        categories = EXPENSE_CATEGORIES
    else:
        categories = INCOME_CATEGORIES

    keyboard = []
    row = []
    for emoji_name, value in categories:
        row.append(InlineKeyboardButton(emoji_name, callback_data=f"editcat_{value}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("🔙 انصراف", callback_data="manage_list")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "📁 **دسته‌بندی جدید رو انتخاب کن:**",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

    return EDIT_CATEGORY


async def edit_field_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع ویرایش توضیحات"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📝 **ویرایش توضیحات**\n\n"
        "توضیحات جدید رو بنویس:\n\n"
        "(یا /skip برای خالی گذاشتن)",
        parse_mode='Markdown'
    )

    return EDIT_DESCRIPTION


async def edit_amount_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت مبلغ جدید"""
    text = update.message.text

    # تبدیل اعداد فارسی به انگلیسی
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    english_digits = '0123456789'
    translation_table = str.maketrans(persian_digits, english_digits)
    text = text.translate(translation_table)

    # حذف کاراکترهای اضافی
    text = text.replace(',', '').replace('،', '').replace(' ', '')

    try:
        amount = int(text)
        if amount <= 0:
            raise ValueError

        t_id = context.user_data.get('edit_id')

        # آپدیت در دیتابیس
        conn = sqlite3.connect('financial_bot.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE transactions SET amount = ? WHERE id = ?', (amount, t_id))
        conn.commit()
        conn.close()

        await update.message.reply_text(
            f"✅ **مبلغ ویرایش شد!**\n\n"
            f"💵 مبلغ جدید: **{amount:,}** ریال",
            parse_mode='Markdown'
        )

        context.user_data.pop('edit_id', None)
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text(
            "❌ مبلغ نامعتبر!\n\nلطفاً فقط عدد وارد کن."
        )
        return EDIT_AMOUNT


async def edit_category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """انتخاب دسته‌بندی جدید"""
    query = update.callback_query
    await query.answer()

    category = query.data.replace("editcat_", "")
    t_id = context.user_data.get('edit_id')

    # آپدیت در دیتابیس
    conn = sqlite3.connect('financial_bot.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE transactions SET category = ? WHERE id = ?', (category, t_id))
    conn.commit()
    conn.close()

    await query.edit_message_text(
        f"✅ **دسته‌بندی ویرایش شد!**\n\n"
        f"📁 دسته جدید: **{category}**",
        parse_mode='Markdown'
    )

    context.user_data.pop('edit_id', None)
    return ConversationHandler.END


async def edit_desc_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت توضیحات جدید"""
    description = update.message.text
    t_id = context.user_data.get('edit_id')

    # آپدیت در دیتابیس
    conn = sqlite3.connect('financial_bot.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE transactions SET description = ? WHERE id = ?', (description, t_id))
    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"✅ **توضیحات ویرایش شد!**\n\n"
        f"📝 توضیح جدید: {description}",
        parse_mode='Markdown'
    )

    context.user_data.pop('edit_id', None)
    return ConversationHandler.END
async def edit_skip_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رد کردن ویرایش توضیحات - خالی کردن"""
    t_id = context.user_data.get('edit_id')

    if not t_id:
        await update.message.reply_text("❌ خطا!")
        return ConversationHandler.END

    # آپدیت با توضیحات خالی
    conn = sqlite3.connect('financial_bot.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE transactions SET description = ? WHERE id = ?', ('', t_id))
    conn.commit()
    conn.close()

    await update.message.reply_text(
        "✅ **توضیحات پاک شد!**",
        parse_mode='Markdown'
    )

    context.user_data.pop('edit_id', None)
    return ConversationHandler.END


async def edit_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو ویرایش"""
    context.user_data.pop('edit_id', None)
    await update.message.reply_text(
        "❌ ویرایش لغو شد.\n\n"
        "برای مدیریت: /manage"
    )
    return ConversationHandler.END


async def edit_skip_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """خالی کردن توضیحات"""
    t_id = context.user_data.get('edit_id')

    # آپدیت در دیتابیس
    conn = sqlite3.connect('financial_bot.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE transactions SET description = ? WHERE id = ?', ('', t_id))
    conn.commit()
    conn.close()

    await update.message.reply_text(
        "✅ **توضیحات پاک شد!**",
        parse_mode='Markdown'
    )

    context.user_data.pop('edit_id', None)
    return ConversationHandler.END


async def cancel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو ویرایش"""
    context.user_data.pop('edit_id', None)
    await update.message.reply_text("❌ ویرایش لغو شد.")
    return ConversationHandler.END
# ================== حذف تراکنش ==================

async def delete_transaction_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع حذف تراکنش"""
    query = update.callback_query
    await query.answer()

    t_id = int(query.data.replace("delete_", ""))
    context.user_data['delete_id'] = t_id

    # گرفتن اطلاعات تراکنش
    conn = sqlite3.connect('financial_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT amount, type, category, date
        FROM transactions
        WHERE id = ?
    ''', (t_id,))
    t = cursor.fetchone()
    conn.close()

    if not t:
        await query.edit_message_text("❌ تراکنش پیدا نشد!")
        return

    amount, t_type, category, date = t
    emoji = "🟢 درآمد" if t_type == "income" else "🔴 هزینه"

    text = f"""
🗑️ **حذف تراکنش**

{emoji}
💵 مبلغ: **{amount:,}** ریال
📁 دسته: {category}
📅 تاریخ: {date}

⚠️ **مطمئنی می‌خوای حذف کنی؟**
"""

    keyboard = [
        [
            InlineKeyboardButton("✅ بله، حذف کن", callback_data="confirm_delete"),
            InlineKeyboardButton("❌ انصراف", callback_data="manage_list"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)


async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تأیید حذف تراکنش"""
    query = update.callback_query
    await query.answer()

    t_id = context.user_data.get('delete_id')

    if not t_id:
        await query.edit_message_text("❌ خطا!")
        return

    # حذف از دیتابیس
    conn = sqlite3.connect('financial_bot.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transactions WHERE id = ?', (t_id,))
    conn.commit()
    conn.close()

    await query.edit_message_text(
        "✅ **تراکنش با موفقیت حذف شد!**",
        parse_mode='Markdown'
    )

    context.user_data.pop('delete_id', None)


# ================== حذف همه داده‌ها ==================

async def manage_delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """درخواست حذف همه داده‌ها"""
    query = update.callback_query
    await query.answer()

    text = """
⚠️ **هشدار!**

با این کار **تمام تراکنش‌ها** حذف میشن!

این عملیات قابل بازگشت نیست!

مطمئنی؟
"""

    keyboard = [
        [
            InlineKeyboardButton("🗑️ بله، همه رو حذف کن", callback_data="confirm_delete_all"),
        ],
        [
            InlineKeyboardButton("❌ انصراف", callback_data="manage"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)


async def confirm_delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تأیید حذف همه"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    # حذف همه تراکنش‌های کاربر
    conn = sqlite3.connect('financial_bot.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transactions WHERE user_id = ?', (user_id,))
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()

    await query.edit_message_text(
        f"✅ **{deleted_count} تراکنش حذف شد!**\n\n"
        "حالا می‌تونی از اول شروع کنی: /start",
        parse_mode='Markdown'
    )


# ================== گزارش ماهانه ==================

async def manage_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """گزارش ماهانه"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    # گرفتن تراکنش‌های ماه جاری
    now = jdatetime.datetime.now()
    month_start = f"{now.year}/{now.month:02d}/01"

    conn = sqlite3.connect('financial_bot.db')
    cursor = conn.cursor()

    # کل درآمد ماه
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE user_id = ? AND type = 'income' AND date >= ?
    ''', (user_id, month_start))
    month_income = cursor.fetchone()[0]

    # کل هزینه ماه
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE user_id = ? AND type = 'expense' AND date >= ?
    ''', (user_id, month_start))
    month_expense = cursor.fetchone()[0]

    # هزینه بر اساس دسته‌بندی
    cursor.execute('''
        SELECT category, SUM(amount)
        FROM transactions
        WHERE user_id = ? AND type = 'expense' AND date >= ?
        GROUP BY category
        ORDER BY SUM(amount) DESC
    ''', (user_id, month_start))
    expense_by_category = cursor.fetchall()

    conn.close()

    # نام ماه فارسی
    month_names = [
        "", "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
    ]
    month_name = month_names[now.month]

    text = f"""
📊 **گزارش {month_name} {now.year}**

💰 **درآمد:** {month_income:,} ریال
💸 **هزینه:** {month_expense:,} ریال
📈 **تراز:** {month_income - month_expense:,} ریال

"""

    if expense_by_category:
        text += "📁 **هزینه بر اساس دسته:**\n"
        for cat, amount in expense_by_category:
            percent = (amount / month_expense * 100) if month_expense > 0 else 0
            text += f"├ {cat}: {amount:,} ({percent:.1f}%)\n"

    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="manage")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)


# ================== آمار کلی ==================

async def manage_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """آمار کلی"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    conn = sqlite3.connect('financial_bot.db')
    cursor = conn.cursor()

    # تعداد کل تراکنش‌ها
    cursor.execute('SELECT COUNT(*) FROM transactions WHERE user_id = ?', (user_id,))
    total_count = cursor.fetchone()[0]

    # کل درآمد
    cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE user_id = ? AND type = ?', (user_id, 'income'))
    total_income = cursor.fetchone()[0]

    # کل هزینه
    cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE user_id = ? AND type = ?', (user_id, 'expense'))
    total_expense = cursor.fetchone()[0]

    # میانگین هزینه
    cursor.execute('SELECT AVG(amount) FROM transactions WHERE user_id = ? AND type = ?', (user_id, 'expense'))
    avg_expense = cursor.fetchone()[0] or 0

    # بیشترین هزینه
    cursor.execute('SELECT MAX(amount) FROM transactions WHERE user_id = ? AND type = ?', (user_id, 'expense'))
    max_expense = cursor.fetchone()[0] or 0

    # اولین تراکنش
    cursor.execute('SELECT MIN(date) FROM transactions WHERE user_id = ?', (user_id,))
    first_date = cursor.fetchone()[0] or '-'

    conn.close()

    text = f"""
📈 **آمار کلی**

📊 **تعداد تراکنش:** {total_count}
💰 **کل درآمد:** {total_income:,} ریال
💸 **کل هزینه:** {total_expense:,} ریال
💵 **موجودی:** {total_income - total_expense:,} ریال

📉 **میانگین هزینه:** {avg_expense:,.0f} ریال
🔺 **بیشترین هزینه:** {max_expense:,} ریال
📅 **اولین ثبت:** {first_date}
"""

    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="manage")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
# ================== جستجو ==================

async def manage_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع جستجو"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🔍 **جستجو در تراکنش‌ها**\n\n"
        "متن مورد نظر رو بنویس:\n"
        "(در دسته‌بندی و توضیحات جستجو میشه)\n\n"
        "یا /cancel برای انصراف",
        parse_mode='Markdown'
    )

    return SEARCH_TEXT


async def search_text_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت متن جستجو"""
    search_text = update.message.text
    user_id = update.effective_user.id

    conn = sqlite3.connect('financial_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, amount, type, category, description, date
        FROM transactions
        WHERE user_id = ? AND (category LIKE ? OR description LIKE ?)
        ORDER BY date DESC
        LIMIT 20
    ''', (user_id, f'%{search_text}%', f'%{search_text}%'))
    results = cursor.fetchall()
    conn.close()

    if not results:
        await update.message.reply_text(
            f"❌ نتیجه‌ای برای «{search_text}» پیدا نشد!\n\n"
            "برای جستجوی جدید: /manage",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

    text = f"🔍 **نتایج جستجو برای «{search_text}»:**\n\n"

    for t in results:
        t_id, amount, t_type, category, desc, date = t
        emoji = "🟢" if t_type == "income" else "🔴"
        sign = "+" if t_type == "income" else "-"
        text += f"{emoji} {sign}{amount:,} | {category} | {date}\n"

    text += f"\n📊 تعداد: {len(results)} تراکنش"

    await update.message.reply_text(text, parse_mode='Markdown')

    return ConversationHandler.END


async def cancel_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو جستجو"""
    await update.message.reply_text("❌ جستجو لغو شد.\n\nبرای منوی مدیریت: /manage")
    return ConversationHandler.END


# ================== بازگشت به منوی اصلی ==================

async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بازگشت به منوی اصلی"""
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    welcome = f"""
سلام **{user.first_name}**! 👋

به **ربات مدیریت مالی** خوش اومدی! 💰

✨ **امکانات:**
├ 📱 ثبت خودکار از پیامک بانک
├ ➕ ثبت دستی درآمد/هزینه
├ 💵 مشاهده موجودی
├ 📋 لیست تراکنش‌ها
├ 📊 نمودار هزینه‌ها
└ ⚙️ پنل مدیریت

📲 **برای ثبت خودکار:**
پیام بانک رو مستقیم فوروارد کن!
"""

    keyboard = [
        [
            InlineKeyboardButton("➕ ثبت هزینه", callback_data="new_expense"),
            InlineKeyboardButton("➕ ثبت درآمد", callback_data="new_income"),
        ],
        [
            InlineKeyboardButton("💵 موجودی", callback_data="balance"),
            InlineKeyboardButton("📋 تراکنش‌ها", callback_data="transactions"),
        ],
        [
            InlineKeyboardButton("📊 نمودار", callback_data="chart"),
            InlineKeyboardButton("📅 امروز", callback_data="daily_report"),  # ← اضافه شد
        ],
        [
            InlineKeyboardButton("⚙️ مدیریت", callback_data="manage"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(welcome, parse_mode='Markdown', reply_markup=reply_markup)


# ================== کالبک نمودار ==================

async def chart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش نمودار از کالبک"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    await query.edit_message_text("📊 در حال ساخت نمودار...")

    conn = sqlite3.connect('financial_bot.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT type, amount, category, description, date
        FROM transactions
        WHERE user_id = ?
        ORDER BY date DESC
    ''', (user_id,))

    transactions_list = cursor.fetchall()
    conn.close()

    if not transactions_list:
        await query.message.reply_text("❌ هنوز تراکنشی ثبت نشده!")
        return

    # ساخت نمودار دایره‌ای
    pie_chart = create_pie_chart(transactions_list)

    if pie_chart:
        await query.message.reply_photo(
            photo=open(pie_chart, 'rb'),
            caption="📊 نمودار هزینه‌ها بر اساس دسته‌بندی"
        )
        os.remove(pie_chart)

    # ساخت نمودار میله‌ای
    bar_chart = create_bar_chart(transactions_list)

    if bar_chart:
        await query.message.reply_photo(
            photo=open(bar_chart, 'rb'),
            caption="📈 مقایسه درآمد و هزینه"
        )
        os.remove(bar_chart)

    if not pie_chart and not bar_chart:
        await query.message.reply_text("❌ داده‌ای برای نمایش نمودار وجود ندارد.")


# ================== کالبک مدیریت ==================

async def manage_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش منوی مدیریت از کالبک"""
    await manage(update, context)
# ================== مراحل اضافی برای ConversationHandler ==================

SEARCH_TEXT = 30
# ================== پنل ادمین ==================

ADMIN_ID = 5669469598  # آیدی ادمین (تو!)

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پنل ادمین"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ شما اجازه دسترسی ندارید!")
        return
    
    conn = sqlite3.connect('financial_bot.db')
    cursor = conn.cursor()
    
    # تعداد کاربران
    cursor.execute('SELECT COUNT(DISTINCT user_id) FROM users')
    total_users = cursor.fetchone()[0]
    
    # تعداد کل تراکنش‌ها
    cursor.execute('SELECT COUNT(*) FROM transactions')
    total_transactions = cursor.fetchone()[0]
    
    # کل درآمد ثبت شده
    cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = ?', ('income',))
    total_income = cursor.fetchone()[0]
    
    # کل هزینه ثبت شده
    cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = ?', ('expense',))
    total_expense = cursor.fetchone()[0]
    
    conn.close()
    
    text = f"""
🔐 **پنل ادمین**

📊 **آمار کلی ربات:**

👥 تعداد کاربران: **{total_users}**
📝 تعداد تراکنش‌ها: **{total_transactions}**
💰 کل درآمد ثبت شده: **{total_income:,}** ریال
💸 کل هزینه ثبت شده: **{total_expense:,}** ریال
"""
    
    keyboard = [
        [InlineKeyboardButton("👥 لیست کاربران", callback_data="admin_users")],
        [InlineKeyboardButton("📊 تراکنش‌های کاربر", callback_data="admin_user_transactions")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_start")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لیست همه کاربران"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await query.edit_message_text("⛔ دسترسی ندارید!")
        return
    
    conn = sqlite3.connect('financial_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.user_id, u.username, u.first_name, u.joined_date,
               COUNT(t.id) as tx_count,
               COALESCE(SUM(CASE WHEN t.type='income' THEN t.amount ELSE 0 END), 0) as income,
               COALESCE(SUM(CASE WHEN t.type='expense' THEN t.amount ELSE 0 END), 0) as expense
        FROM users u
        LEFT JOIN transactions t ON u.user_id = t.user_id
        GROUP BY u.user_id
        ORDER BY tx_count DESC
        LIMIT 20
    ''')
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        await query.edit_message_text("👥 هنوز کاربری ثبت نشده!")
        return
    
    text = "👥 **لیست کاربران:**\n\n"
    
    for u in users:
        uid, username, first_name, joined, tx_count, income, expense = u
        name = first_name or username or "بدون نام"
        username_text = f"@{username}" if username else "-"
        balance = income - expense
        
        text += f"👤 **{name}**\n"
        text += f"├ 🆔 `{uid}`\n"
        text += f"├ 📱 {username_text}\n"
        text += f"├ 📝 تراکنش‌ها: {tx_count}\n"
        text += f"└ 💰 موجودی: {balance:,} ریال\n\n"
    
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_back")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)

async def admin_user_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """درخواست آیدی کاربر برای نمایش تراکنش‌ها"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await query.edit_message_text("⛔ دسترسی ندارید!")
        return
    
    await query.edit_message_text(
        "🔍 **مشاهده تراکنش‌های کاربر**\n\n"
        "آیدی عددی کاربر رو بفرست:\n\n"
        "(مثال: `5669469598`)\n\n"
        "یا /cancel برای انصراف",
        parse_mode='Markdown'
    )
    
    context.user_data['admin_waiting_user_id'] = True

async def admin_show_user_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش تراکنش‌های یک کاربر خاص"""
    if not context.user_data.get('admin_waiting_user_id'):
        return False
    
    if update.effective_user.id != ADMIN_ID:
        return False
    
    try:
        target_user_id = int(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ آیدی باید عدد باشه!")
        return True
    
    conn = sqlite3.connect('financial_bot.db')
    cursor = conn.cursor()
    
    # اطلاعات کاربر
    cursor.execute('SELECT username, first_name FROM users WHERE user_id = ?', (target_user_id,))
    user_info = cursor.fetchone()
    
    if not user_info:
        await update.message.reply_text("❌ کاربر پیدا نشد!")
        context.user_data.pop('admin_waiting_user_id', None)
        conn.close()
        return True
    
    username, first_name = user_info
    name = first_name or username or "بدون نام"
    
    # تراکنش‌های کاربر
    cursor.execute('''
        SELECT amount, type, category, description, date
        FROM transactions
        WHERE user_id = ?
        ORDER BY date DESC
        LIMIT 20
    ''', (target_user_id,))
    transactions = cursor.fetchall()
    
    # آمار کاربر
    cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE user_id = ? AND type = ?', (target_user_id, 'income'))
    total_income = cursor.fetchone()[0]
    
    cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE user_id = ? AND type = ?', (target_user_id, 'expense'))
    total_expense = cursor.fetchone()[0]
    
    conn.close()
    
    text = f"📊 **تراکنش‌های {name}**\n"
    text += f"🆔 `{target_user_id}`\n\n"
    text += f"💰 درآمد: {total_income:,} ریال\n"
    text += f"💸 هزینه: {total_expense:,} ریال\n"
    text += f"📈 موجودی: {total_income - total_expense:,} ریال\n\n"
    
    if transactions:
        text += "📋 **آخرین تراکنش‌ها:**\n\n"
        for t in transactions:
            amount, t_type, category, desc, date = t
            emoji = "🟢" if t_type == "income" else "🔴"
            sign = "+" if t_type == "income" else "-"
            text += f"{emoji} {sign}{amount:,} | {category} | {date}\n"
    else:
        text += "📭 تراکنشی ثبت نشده!"
    
    await update.message.reply_text(text, parse_mode='Markdown')
    
    context.user_data.pop('admin_waiting_user_id', None)
    return True

async def admin_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بازگشت به پنل ادمین"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await query.edit_message_text("⛔ دسترسی ندارید!")
        return
    
    conn = sqlite3.connect('financial_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(DISTINCT user_id) FROM users')
    total_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM transactions')
    total_transactions = cursor.fetchone()[0]
    
    cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = ?', ('income',))
    total_income = cursor.fetchone()[0]
    
    cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = ?', ('expense',))
    total_expense = cursor.fetchone()[0]
    
    conn.close()
    
    text = f"""
🔐 **پنل ادمین**

📊 **آمار کلی ربات:**

👥 تعداد کاربران: **{total_users}**
📝 تعداد تراکنش‌ها: **{total_transactions}**
💰 کل درآمد ثبت شده: **{total_income:,}** ریال
💸 کل هزینه ثبت شده: **{total_expense:,}** ریال
"""
    
    keyboard = [
        [InlineKeyboardButton("👥 لیست کاربران", callback_data="admin_users")],
        [InlineKeyboardButton("📊 تراکنش‌های کاربر", callback_data="admin_user_transactions")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_start")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)

# ================== گزارش روزانه ==================

async def daily_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """گزارش روزانه"""
    user_id = update.effective_user.id

    # تاریخ امروز - هر دو فرمت برای سازگاری
    now = jdatetime.datetime.now()
    
    # الگوهای مختلف تاریخ (با صفر و بدون صفر)
    pattern1 = f"{now.year}/{now.month}/{now.day}%"      # 1404/9/18%
    pattern2 = f"{now.year}/{now.month:02d}/{now.day:02d}%"  # 1404/09/18%
    today_display = f"{now.year}/{now.month:02d}/{now.day:02d}"

    conn = sqlite3.connect('/app/data/financial_bot.db') if os.path.exists('/app/data') else sqlite3.connect('financial_bot.db')
    cursor = conn.cursor()

    # درآمد امروز (هر دو الگو)
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE user_id = ? AND type = 'income' AND (date LIKE ? OR date LIKE ?)
    ''', (user_id, pattern1, pattern2))
    today_income = cursor.fetchone()[0]

    # هزینه امروز
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE user_id = ? AND type = 'expense' AND (date LIKE ? OR date LIKE ?)
    ''', (user_id, pattern1, pattern2))
    today_expense = cursor.fetchone()[0]

    # تعداد تراکنش‌های امروز
    cursor.execute('''
        SELECT COUNT(*)
        FROM transactions
        WHERE user_id = ? AND (date LIKE ? OR date LIKE ?)
    ''', (user_id, pattern1, pattern2))
    today_count = cursor.fetchone()[0]

    # هزینه‌ها بر اساس دسته
    cursor.execute('''
        SELECT category, SUM(amount)
        FROM transactions
        WHERE user_id = ? AND type = 'expense' AND (date LIKE ? OR date LIKE ?)
        GROUP BY category
        ORDER BY SUM(amount) DESC
    ''', (user_id, pattern1, pattern2))
    expense_by_category = cursor.fetchall()

    # تراکنش‌های امروز
    cursor.execute('''
        SELECT amount, type, category, description
        FROM transactions
        WHERE user_id = ? AND (date LIKE ? OR date LIKE ?)
        ORDER BY id DESC
        LIMIT 10
    ''', (user_id, pattern1, pattern2))
    today_transactions = cursor.fetchall()

    conn.close()

    # ساخت متن
    text = f"📅 **گزارش امروز** ({today_display})\n\n"

    if today_count == 0:
        text += "📭 امروز هنوز تراکنشی ثبت نشده!"
    else:
        text += f"📊 **خلاصه:**\n"
        text += f"├ 💰 درآمد: **{today_income:,}** ریال\n"
        text += f"├ 💸 هزینه: **{today_expense:,}** ریال\n"
        text += f"├ 📈 تراز: **{today_income - today_expense:,}** ریال\n"
        text += f"└ 📝 تعداد: {today_count} تراکنش\n\n"

        if expense_by_category:
            text += "📁 **هزینه‌ها بر اساس دسته:**\n"
            for cat, amount in expense_by_category:
                percent = (amount / today_expense * 100) if today_expense > 0 else 0
                text += f"├ {cat}: {amount:,} ({percent:.0f}%)\n"
            text += "\n"

        if today_transactions:
            text += "📋 **تراکنش‌های امروز:**\n"
            for t in today_transactions:
                amount, t_type, category, desc = t
                emoji = "🟢" if t_type == "income" else "🔴"
                sign = "+" if t_type == "income" else "-"
                desc_text = f" - {desc}" if desc else ""
                text += f"{emoji} {sign}{amount:,} | {category}{desc_text}\n"

    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)



async def daily_report_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """کالبک گزارش روزانه"""
    await daily_report(update, context)

# ================== اعلان شبانه ==================

# ================== اعلان شبانه ==================

async def send_nightly_report_to_admin(context: ContextTypes.DEFAULT_TYPE):
    """ارسال گزارش شبانه به ادمین"""
    
    ADMIN_ID = 5669469598
    
    # اتصال به دیتابیس
    db_path = '/app/data/financial_bot.db' if os.path.exists('/app/data') else 'financial_bot.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    now = jdatetime.datetime.now()
    pattern1 = f"{now.year}/{now.month}/{now.day}%"
    pattern2 = f"{now.year}/{now.month:02d}/{now.day:02d}%"
    today_display = f"{now.year}/{now.month:02d}/{now.day:02d}"

    # درآمد امروز
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE user_id = ? AND type = 'income' AND (date LIKE ? OR date LIKE ?)
    ''', (ADMIN_ID, pattern1, pattern2))
    today_income = cursor.fetchone()[0]

    # هزینه امروز
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE user_id = ? AND type = 'expense' AND (date LIKE ? OR date LIKE ?)
    ''', (ADMIN_ID, pattern1, pattern2))
    today_expense = cursor.fetchone()[0]

    # تعداد تراکنش‌ها
    cursor.execute('''
        SELECT COUNT(*)
        FROM transactions
        WHERE user_id = ? AND (date LIKE ? OR date LIKE ?)
    ''', (ADMIN_ID, pattern1, pattern2))
    today_count = cursor.fetchone()[0]

    # تراکنش‌ها
    cursor.execute('''
        SELECT amount, type, category, description
        FROM transactions
        WHERE user_id = ? AND (date LIKE ? OR date LIKE ?)
        ORDER BY id DESC
        LIMIT 5
    ''', (ADMIN_ID, pattern1, pattern2))
    today_transactions = cursor.fetchall()

    conn.close()

    # ساخت پیام
    text = f"🌙 **گزارش شبانه** ({today_display})\n\n"

    if today_count == 0:
        text += "📭 امروز تراکنشی ثبت نشده!"
    else:
        text += f"📊 **خلاصه امروز:**\n"
        text += f"├ 💰 درآمد: **{today_income:,}** ریال\n"
        text += f"├ 💸 هزینه: **{today_expense:,}** ریال\n"
        text += f"├ 📈 تراز: **{today_income - today_expense:,}** ریال\n"
        text += f"└ 📝 تعداد: {today_count} تراکنش\n\n"

        if today_transactions:
            text += "📋 **آخرین تراکنش‌ها:**\n"
            for t in today_transactions:
                amount, t_type, category, desc = t
                emoji = "🟢" if t_type == "income" else "🔴"
                sign = "+" if t_type == "income" else "-"
                text += f"{emoji} {sign}{amount:,} | {category}\n"

    text += "\n💤 شب بخیر!"

    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=text,
            parse_mode='Markdown'
        )
        print(f"✅ گزارش شبانه ارسال شد - {today_display}")
    except Exception as e:
        print(f"❌ خطا در ارسال گزارش: {e}")
    
    conn.close()


async def send_nightly_report_to_admin(context: ContextTypes.DEFAULT_TYPE):
    """ارسال گزارش فقط به ادمین (برای تست)"""
    
    ADMIN_ID = 5669469598  # آیدی تو
    
    conn = sqlite3.connect('financial_bot.db')
    cursor = conn.cursor()
    
    now = jdatetime.datetime.now()
    today_pattern = now.strftime('%Y/%m/%d') + "%"
    today_display = now.strftime('%Y/%m/%d')
    
    # درآمد امروز
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE user_id = ? AND type = 'income' AND date LIKE ?
    ''', (ADMIN_ID, today_pattern))
    today_income = cursor.fetchone()[0]
    
    # هزینه امروز
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE user_id = ? AND type = 'expense' AND date LIKE ?
    ''', (ADMIN_ID, today_pattern))
    today_expense = cursor.fetchone()[0]
    
    # تعداد تراکنش‌ها
    cursor.execute('''
        SELECT COUNT(*)
        FROM transactions
        WHERE user_id = ? AND date LIKE ?
    ''', (ADMIN_ID, today_pattern))
    today_count = cursor.fetchone()[0]
    
    # تراکنش‌ها
    cursor.execute('''
        SELECT amount, type, category, description
        FROM transactions
        WHERE user_id = ? AND date LIKE ?
        ORDER BY id DESC
        LIMIT 5
    ''', (ADMIN_ID, today_pattern))
    today_transactions = cursor.fetchall()
    
    conn.close()
    
    # ساخت پیام
    text = f"🌙 **گزارش شبانه** ({today_display})\n\n"
    
    if today_count == 0:
        text += "📭 امروز تراکنشی ثبت نشده!"
    else:
        text += f"📊 **خلاصه امروز:**\n"
        text += f"├ 💰 درآمد: **{today_income:,}** ریال\n"
        text += f"├ 💸 هزینه: **{today_expense:,}** ریال\n"
        text += f"├ 📈 تراز: **{today_income - today_expense:,}** ریال\n"
        text += f"└ 📝 تعداد: {today_count} تراکنش\n\n"
        
        if today_transactions:
            text += "📋 **آخرین تراکنش‌ها:**\n"
            for t in today_transactions:
                amount, t_type, category, desc = t
                emoji = "🟢" if t_type == "income" else "🔴"
                sign = "+" if t_type == "income" else "-"
                text += f"{emoji} {sign}{amount:,} | {category}\n"
    
    text += "\n💤 شب بخیر!"
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=text,
            parse_mode='Markdown'
        )
        print(f"✅ گزارش شبانه ارسال شد")
    except Exception as e:
        print(f"❌ خطا: {e}")

# ================== تست گزارش شبانه ==================

async def test_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تست دستی گزارش شبانه"""
    if update.effective_user.id != 5669469598:
        await update.message.reply_text("⛔ فقط ادمین!")
        return
    
    await update.message.reply_text("⏳ در حال ارسال گزارش تست...")
    await send_nightly_report_to_admin(context)
    await update.message.reply_text("✅ گزارش ارسال شد!")

# ================== تابع اصلی ==================

def main():
    print("🤖 ربات در حال راه‌اندازی...")

    # ساخت جداول دیتابیس
    create_tables()

    # ساخت اپلیکیشن
    application = Application.builder().token(BOT_TOKEN).build()

    # ⏰ زمان‌بندی گزارش شبانه - ساعت 23:00 تهران
    tehran_tz = pytz.timezone('Asia/Tehran')
    target_time = datetime.time(hour=23, minute=0, second=0, tzinfo=tehran_tz)
    
    application.job_queue.run_daily(
        send_nightly_report_to_admin,
        time=target_time,
        name="nightly_report"
    )
    print(f"⏰ گزارش شبانه تنظیم شد: هر شب ساعت 23:00 تهران")

    # -------------------- هندلر ثبت دستی --------------------
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("expense", expense_start),
            CommandHandler("income", income_start),
            CallbackQueryHandler(expense_start, pattern="^new_expense$"),
            CallbackQueryHandler(income_start, pattern="^new_income$"),
        ],
        states={
            AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, amount_received),
                CallbackQueryHandler(cancel_transaction_callback, pattern="^cancel_transaction$"),
            ],
            CATEGORY: [
                CallbackQueryHandler(category_selected, pattern="^cat_"),
                CallbackQueryHandler(cancel_transaction_callback, pattern="^cancel_transaction$"),
            ],
            DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, description_received),
                CommandHandler("skip", skip_description),
                CallbackQueryHandler(cancel_transaction_callback, pattern="^cancel_transaction$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(cancel_transaction_callback, pattern="^cancel_transaction$"),
        ],
    )
    
    # ... بقیه کدها همون که هست ادامه بده ...


    # -------------------- هندلر ویرایش تراکنش --------------------
    edit_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(edit_field_amount, pattern="^edit_field_amount$"),
            CallbackQueryHandler(edit_field_desc, pattern="^edit_field_desc$"),
        ],
        states={
            EDIT_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_amount_received),
            ],
            EDIT_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_desc_received),
                CommandHandler("skip", edit_skip_desc),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", edit_cancel),
        ],
    )

    # -------------------- هندلر جستجو --------------------
    search_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(manage_search, pattern="^manage_search$"),
        ],
        states={
            SEARCH_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, search_text_received),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_search),
        ],
    )


    # -------------------- دستورات اصلی --------------------
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("transactions", transactions_command))
    application.add_handler(CommandHandler("chart", chart))
    application.add_handler(CommandHandler("manage", manage))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CommandHandler("testreport", test_report))
    application.add_handler(CommandHandler("testreport", test_report))
    # -------------------- هندلرهای مکالمه --------------------
    application.add_handler(conv_handler)
    application.add_handler(edit_conv_handler)
    application.add_handler(search_conv_handler)

    # -------------------- کالبک‌های منوی اصلی --------------------
    application.add_handler(CallbackQueryHandler(balance_callback, pattern="^balance$"))
    application.add_handler(CallbackQueryHandler(transactions_callback, pattern="^transactions$"))
    application.add_handler(CallbackQueryHandler(chart_callback, pattern="^chart$"))
    application.add_handler(CallbackQueryHandler(back_to_start, pattern="^back_to_start$"))
    application.add_handler(CallbackQueryHandler(all_transactions, pattern=r"^all_transactions_\d+$"))
    application.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.answer(), pattern="^ignore$"))

    # -------------------- کالبک‌های پیامک بانکی --------------------
    application.add_handler(CallbackQueryHandler(confirm_sms, pattern="^confirm_sms$"))
    application.add_handler(CallbackQueryHandler(cancel_sms, pattern="^cancel_sms$"))
    application.add_handler(CallbackQueryHandler(edit_category_sms, pattern="^edit_category_sms$"))
    application.add_handler(CallbackQueryHandler(sms_category_selected, pattern="^smscat_"))

    # -------------------- کالبک‌های پنل مدیریت --------------------
    application.add_handler(CallbackQueryHandler(manage_callback, pattern="^manage$"))
    application.add_handler(CallbackQueryHandler(manage_list, pattern="^manage_list$"))
    application.add_handler(CallbackQueryHandler(manage_report, pattern="^manage_report$"))
    application.add_handler(CallbackQueryHandler(manage_stats, pattern="^manage_stats$"))
    application.add_handler(CallbackQueryHandler(manage_delete_all, pattern="^manage_delete_all$"))
    application.add_handler(CallbackQueryHandler(confirm_delete_all, pattern="^confirm_delete_all$"))

        # -------------------- کالبک‌های ادمین --------------------
    application.add_handler(CallbackQueryHandler(admin_users, pattern="^admin_users$"))
    application.add_handler(CallbackQueryHandler(admin_user_transactions, pattern="^admin_user_transactions$"))
    application.add_handler(CallbackQueryHandler(admin_back, pattern="^admin_back$"))

    # -------------------- کالبک‌های ویرایش/حذف تراکنش --------------------
    application.add_handler(CallbackQueryHandler(edit_field_category, pattern="^edit_field_category$"))
    application.add_handler(CallbackQueryHandler(edit_transaction_start, pattern=r"^edit_\d+$"))
    application.add_handler(CallbackQueryHandler(edit_category_selected, pattern="^editcat_"))
    application.add_handler(CallbackQueryHandler(delete_transaction_start, pattern=r"^delete_\d+$"))
    application.add_handler(CallbackQueryHandler(confirm_delete, pattern="^confirm_delete$"))

    # کالبک گزارش روزانه
    application.add_handler(CallbackQueryHandler(daily_report_callback, pattern="^daily_report$"))
    
    # دستور گزارش روزانه
    application.add_handler(CommandHandler("today", daily_report))
    
    # -------------------- هندلر یام‌های متنی (آخر!) --------------------
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_text_message))

    print("✅ ربات آماده است!")
    print("📱 در حال تصال به تلگرام...")

    # اجرا
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()


