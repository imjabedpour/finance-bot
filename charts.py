# charts.py - ساخت نمودارهای مالی
import matplotlib
matplotlib.use('Agg')  # برای سرور بدون GUI
import matplotlib.pyplot as plt
from bidi.algorithm import get_display
import arabic_reshaper
import io
from collections import defaultdict

# تنظیم فونت فارسی
plt.rcParams['font.family'] = 'DejaVu Sans'


def reshape_persian(text):
    """تبدیل متن فارسی برای نمایش صحیح"""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def create_pie_chart(transactions):
    """
    ساخت نمودار دایره‌ای هزینه‌ها بر اساس دسته‌بندی
    
    transactions: لیست تراکنش‌ها از دیتابیس
    هر تراکنش: (type, amount, category, description, date)
    """
    
    # جمع‌آوری هزینه‌ها بر اساس دسته‌بندی
    category_totals = defaultdict(int)
    
    for tx in transactions:
        tx_type = tx[0]          # نوع
        amount = int(tx[1])      # مبلغ - تبدیل به عدد
        category = tx[2]         # دسته‌بندی
        
        if tx_type == 'expense':
            category_totals[category] += amount
    
    # اگر هزینه‌ای نبود
    if not category_totals:
        return None
    
    # آماده‌سازی داده‌ها
    categories = list(category_totals.keys())
    amounts = list(category_totals.values())
    total = sum(amounts)
    
    # درصدها
    percentages = [(a / total) * 100 for a in amounts]
    
    # رنگ‌های زیبا
    colors = [
        '#FF6B6B',  # قرمز
        '#4ECDC4',  # فیروزه‌ای
        '#45B7D1',  # آبی
        '#96CEB4',  # سبز
        '#FFEAA7',  # زرد
        '#DDA0DD',  # بنفش
        '#98D8C8',  # سبز روشن
        '#F7DC6F',  # طلایی
        '#BB8FCE',  # یاسی
        '#85C1E9',  # آبی روشن
    ]
    
    # ساخت نمودار
    fig, ax = plt.subplots(figsize=(10, 8), facecolor='#1a1a2e')
    ax.set_facecolor('#1a1a2e')
    
    # رسم نمودار دایره‌ای
    wedges, texts, autotexts = ax.pie(
        amounts,
        labels=[reshape_persian(cat) for cat in categories],
        autopct=lambda pct: f'{pct:.1f}%' if pct > 5 else '',
        colors=colors[:len(categories)],
        explode=[0.02] * len(categories),
        shadow=True,
        startangle=90
    )
    
    # تنظیم استایل متن‌ها
    for text in texts:
        text.set_color('white')
        text.set_fontsize(12)
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(10)
        autotext.set_weight('bold')
    
    # عنوان
    title = reshape_persian(f'نمودار هزینه‌ها - مجموع: {total:,} تومان')
    ax.set_title(title, color='white', fontsize=14, pad=20)
    
    # لجند با جزئیات
    legend_labels = [
        f'{reshape_persian(cat)}: {amt:,} ({pct:.1f}%)'
        for cat, amt, pct in zip(categories, amounts, percentages)
    ]
    
    legend = ax.legend(
        wedges,
        legend_labels,
        title=reshape_persian('دسته‌بندی‌ها'),
        loc='center left',
        bbox_to_anchor=(1, 0, 0.5, 1),
        facecolor='#16213e',
        edgecolor='white'
    )
    
    legend.get_title().set_color('white')
    for text in legend.get_texts():
        text.set_color('white')
    
    plt.tight_layout()
    
    # ذخیره به فایل موقت
    filename = 'temp_pie_chart.png'
    plt.savefig(filename, format='png', dpi=150, bbox_inches='tight',
                facecolor='#1a1a2e', edgecolor='none')
    plt.close(fig)
    
    return filename


def create_bar_chart(transactions):
    """
    نمودار مقایسه درآمد و هزینه
    
    transactions: لیست تراکنش‌ها از دیتابیس
    هر تراکنش: (type, amount, category, description, date)
    """
    
    total_income = 0
    total_expense = 0
    
    for tx in transactions:
        tx_type = tx[0]          # نوع
        amount = int(tx[1])      # مبلغ - تبدیل به عدد
        
        if tx_type == 'income':
            total_income += amount
        else:
            total_expense += amount
    
    if total_income == 0 and total_expense == 0:
        return None
    
    # ساخت نمودار میله‌ای
    fig, ax = plt.subplots(figsize=(8, 6), facecolor='#1a1a2e')
    ax.set_facecolor('#1a1a2e')
    
    categories = [reshape_persian('درآمد'), reshape_persian('هزینه')]
    values = [total_income, total_expense]
    colors = ['#2ECC71', '#E74C3C']
    
    bars = ax.bar(categories, values, color=colors, width=0.5, edgecolor='white')
    
    # نمایش مقادیر روی میله‌ها
    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax.annotate(f'{val:,}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    color='white', fontsize=12, weight='bold')
    
    # تنظیمات
    ax.set_ylabel(reshape_persian('مبلغ (تومان)'), color='white')
    ax.tick_params(colors='white')
    ax.spines['bottom'].set_color('white')
    ax.spines['left'].set_color('white')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # تراز مالی
    balance = total_income - total_expense
    balance_text = reshape_persian(f'تراز: {balance:,} تومان')
    balance_color = '#2ECC71' if balance >= 0 else '#E74C3C'
    
    title = reshape_persian('مقایسه درآمد و هزینه')
    ax.set_title(f'{title}\n{balance_text}', color='white', fontsize=14)
    
    plt.tight_layout()
    
    # ذخیره به فایل موقت
    filename = 'temp_bar_chart.png'
    plt.savefig(filename, format='png', dpi=150, bbox_inches='tight',
                facecolor='#1a1a2e', edgecolor='none')
    plt.close(fig)
    
    return filename


# تست
if __name__ == "__main__":
    # داده‌های تستی - با فرمت جدید (type, amount, category, description, date)
    test_transactions = [
        ('expense', 500000, 'خوراک', 'ناهار', '1403/09/15'),
        ('expense', 200000, 'حمل‌ونقل', 'تاکسی', '1403/09/15'),
        ('expense', 1500000, 'خرید', 'لباس', '1403/09/15'),
        ('expense', 300000, 'خوراک', 'شام', '1403/09/15'),
        ('income', 5000000, 'حقوق', 'حقوق ماهانه', '1403/09/15'),
        ('expense', 800000, 'قبوض', 'برق', '1403/09/15'),
    ]
    
    # تست نمودار دایره‌ای
    pie_file = create_pie_chart(test_transactions)
    if pie_file:
        print(f"✅ نمودار دایره‌ای ذخیره شد: {pie_file}")
    
    # تست نمودار مقایسه
    bar_file = create_bar_chart(test_transactions)
    if bar_file:
        print(f"✅ نمودار میله‌ای ذخیره شد: {bar_file}")
