# charts.py - نسخه اصلاح شده
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from bidi.algorithm import get_display
import arabic_reshaper
import io
from collections import defaultdict

plt.rcParams['font.family'] = 'DejaVu Sans'


def reshape_persian(text):
    try:
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    except:
        return str(text)


def create_pie_chart(transactions):
    """نمودار دایره‌ای هزینه‌ها"""
    print(f"📊 create_pie_chart شروع - تعداد: {len(transactions)}")
    
    if not transactions:
        print("⚠️ لیست خالی")
        return None
    
    # نمونه برای دیباگ
    print(f"📊 نمونه: {transactions[0]}")
    
    category_totals = defaultdict(int)

    for tx in transactions:
        try:
            # پیدا کردن amount و type و category
            # بررسی هر فیلد برای تشخیص درست
            
            amount = None
            tx_type = None
            category = None
            
            for i, field in enumerate(tx):
                field_str = str(field)
                
                # اگه عدده، احتمالاً amount هست
                if amount is None:
                    try:
                        test_int = int(field)
                        if test_int > 100:  # مبالغ معمولاً بزرگن
                            amount = test_int
                            continue
                    except:
                        pass
                
                # اگه income یا expense هست
                if field_str in ['income', 'expense']:
                    tx_type = field_str
                    continue
                
                # بقیه فیلدهای متنی فارسی احتمالاً category هستن
                if category is None and field_str not in ['income', 'expense']:
                    if any(c in field_str for c in ['خوراک', 'حمل', 'قبوض', 'خرید', 'تفریح', 'سلامت', 'آموزش', 'سایر', 'حقوق', 'هدیه', 'سرمایه', 'پروژه']):
                        category = field_str

            # اگه پیدا نشد، از ایندکس ثابت استفاده کن
            if amount is None or tx_type is None or category is None:
                # فرمت: (type, amount, category, desc, date)
                tx_type = str(tx[0])
                # amount باید عدد باشه - پیداش کن
                for field in tx[1:]:
                    try:
                        amount = int(field)
                        break
                    except:
                        continue
                category = str(tx[2]) if len(tx) > 2 else 'سایر'

            if tx_type == 'expense' and amount:
                category_totals[category] += amount
                
        except Exception as e:
            print(f"⚠️ خطا: {e}")
            continue

    print(f"📊 دسته‌بندی‌ها: {dict(category_totals)}")

    if not category_totals:
        print("⚠️ هیچ هزینه‌ای یافت نشد")
        return None

    categories = list(category_totals.keys())
    amounts = list(category_totals.values())
    total = sum(amounts)

    colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
              '#FF9F40', '#FF6384', '#C9CBCF', '#7BC225', '#B97CD1']

    fig, ax = plt.subplots(figsize=(10, 8), facecolor='white')

    wedges, texts, autotexts = ax.pie(
        amounts,
        labels=[reshape_persian(cat) for cat in categories],
        autopct=lambda pct: f'{pct:.1f}%' if pct > 5 else '',
        colors=colors[:len(categories)],
        explode=[0.02] * len(categories),
        startangle=90
    )

    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(10)
        autotext.set_weight('bold')

    title = reshape_persian(f'هزینه‌ها - مجموع: {total:,} ریال')
    ax.set_title(title, fontsize=14, pad=20)

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close(fig)

    print("✅ نمودار دایره‌ای ساخته شد")
    return buf


def create_bar_chart(transactions):
    """نمودار میله‌ای درآمد و هزینه"""
    print(f"📊 create_bar_chart شروع - تعداد: {len(transactions)}")
    
    if not transactions:
        return None

    total_income = 0
    total_expense = 0

    for tx in transactions:
        try:
            # پیدا کردن amount و type
            amount = None
            tx_type = None
            
            for field in tx:
                field_str = str(field)
                
                # پیدا کردن type
                if field_str in ['income', 'expense']:
                    tx_type = field_str
                
                # پیدا کردن amount
                if amount is None:
                    try:
                        test_int = int(field)
                        if test_int > 100:
                            amount = test_int
                    except:
                        pass

            if tx_type and amount:
                if tx_type == 'income':
                    total_income += amount
                elif tx_type == 'expense':
                    total_expense += amount
                
        except Exception as e:
            print(f"⚠️ خطا: {e}")
            continue

    print(f"📊 درآمد: {total_income}, هزینه: {total_expense}")

    if total_income == 0 and total_expense == 0:
        print("⚠️ داده‌ای برای نمودار نیست")
        return None

    fig, ax = plt.subplots(figsize=(8, 6), facecolor='white')

    categories = [reshape_persian('درآمد'), reshape_persian('هزینه')]
    values = [total_income, total_expense]
    colors = ['#4BC0C0', '#FF6384']

    bars = ax.bar(categories, values, color=colors, width=0.5)

    for bar, val in zip(bars, values):
        ax.annotate(f'{val:,}',
                    xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', fontsize=12, weight='bold')

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.yaxis.grid(True, linestyle='--', alpha=0.3)

    balance = total_income - total_expense
    balance_color = '#4BC0C0' if balance >= 0 else '#FF6384'
    
    ax.set_title(reshape_persian('مقایسه درآمد و هزینه'), fontsize=14)
    ax.text(0.5, 0.95, reshape_persian(f'تراز: {balance:,} ریال'),
            transform=ax.transAxes, ha='center', color=balance_color, 
            fontsize=12, weight='bold')

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close(fig)

    print("✅ نمودار میله‌ای ساخته شد")
    return buf


# Alias برای سازگاری
create_expense_pie_chart = create_pie_chart
create_income_expense_chart = create_bar_chart
