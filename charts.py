# charts.py - نسخه نهایی
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
    print(f"📊 create_pie_chart - تعداد تراکنش: {len(transactions)}")
    
    if not transactions:
        return None
    
    # دیباگ
    print(f"📊 نمونه داده: {transactions[0]}")
    print(f"📊 تعداد فیلد: {len(transactions[0])}")
    
    category_totals = defaultdict(int)

    for tx in transactions:
        try:
            # فرمت: (id, user_id, amount, type, category, description, date)
            # یا: (type, amount, category, description, date)
            # یا: (amount, type, category, description, date)
            
            amount = None
            tx_type = None
            category = None
            
            # اول پیدا کن کدوم فیلد چیه
            for i, field in enumerate(tx):
                field_str = str(field).strip()
                
                # تشخیص type
                if field_str in ['income', 'expense']:
                    tx_type = field_str
                    continue
                
                # تشخیص amount (عدد بزرگ)
                if amount is None:
                    try:
                        num = int(str(field).replace(',', ''))
                        if num > 1000:  # مبالغ معمولاً بیشتر از 1000 هستن
                            amount = num
                            continue
                    except:
                        pass
                
                # تشخیص category (کلمات فارسی خاص)
                if category is None and tx_type is not None:
                    persian_cats = ['خوراک', 'حمل', 'قبوض', 'خرید', 'تفریح', 
                                   'سلامت', 'آموزش', 'سایر', 'حقوق', 'هدیه', 
                                   'سرمایه', 'پروژه', 'نقل']
                    if any(cat in field_str for cat in persian_cats):
                        category = field_str
            
            # اگه هنوز پیدا نشده، از ایندکس استفاده کن
            if len(tx) >= 7:
                # فرمت: (id, user_id, amount, type, category, desc, date)
                if amount is None:
                    try:
                        amount = int(str(tx[2]).replace(',', ''))
                    except:
                        pass
                if tx_type is None:
                    tx_type = str(tx[3])
                if category is None:
                    category = str(tx[4])
            elif len(tx) >= 5:
                # فرمت: (type, amount, category, desc, date) یا مشابه
                if amount is None:
                    for field in tx:
                        try:
                            num = int(str(field).replace(',', ''))
                            if num > 1000:
                                amount = num
                                break
                        except:
                            pass
                if tx_type is None:
                    for field in tx:
                        if str(field) in ['income', 'expense']:
                            tx_type = str(field)
                            break
                if category is None:
                    category = 'سایر'
            
            # ثبت هزینه
            if tx_type == 'expense' and amount and amount > 0:
                cat_name = category if category else 'سایر'
                category_totals[cat_name] += amount
                print(f"  ✓ هزینه: {amount:,} - {cat_name}")
                
        except Exception as e:
            print(f"  ✗ خطا در پردازش: {e}")
            continue

    print(f"📊 جمع دسته‌ها: {dict(category_totals)}")

    if not category_totals:
        print("⚠️ هیچ هزینه‌ای پیدا نشد!")
        return None

    # ساخت نمودار
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

    print("✅ نمودار دایره‌ای آماده!")
    return buf


def create_bar_chart(transactions):
    """نمودار میله‌ای درآمد و هزینه"""
    print(f"📊 create_bar_chart - تعداد: {len(transactions)}")
    
    if not transactions:
        return None

    total_income = 0
    total_expense = 0

    for tx in transactions:
        try:
            amount = None
            tx_type = None
            
            # پیدا کردن فیلدها
            for field in tx:
                field_str = str(field).strip()
                
                if field_str in ['income', 'expense']:
                    tx_type = field_str
                
                if amount is None:
                    try:
                        num = int(str(field).replace(',', ''))
                        if num > 1000:
                            amount = num
                    except:
                        pass

            # اگه پیدا نشد از ایندکس
            if len(tx) >= 7 and (amount is None or tx_type is None):
                try:
                    amount = int(str(tx[2]).replace(',', ''))
                except:
                    pass
                tx_type = str(tx[3])

            if tx_type and amount and amount > 0:
                if tx_type == 'income':
                    total_income += amount
                elif tx_type == 'expense':
                    total_expense += amount
                
        except Exception as e:
            print(f"  ✗ خطا: {e}")
            continue

    print(f"📊 درآمد: {total_income:,}, هزینه: {total_expense:,}")

    if total_income == 0 and total_expense == 0:
        print("⚠️ داده‌ای نیست!")
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

    print("✅ نمودار میله‌ای آماده!")
    return buf
