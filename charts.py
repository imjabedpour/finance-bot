# charts.py - ساخت نمودارهای مالی با استایل جدید
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from bidi.algorithm import get_display
import arabic_reshaper
import io
from collections import defaultdict
import jdatetime

# تنظیمات فونت
plt.rcParams['font.family'] = 'DejaVu Sans'

def reshape_persian(text):
    """تبدیل متن فارسی برای نمایش صحیح"""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def create_monthly_chart(transactions):
    """
    نمودار ترکیبی ماهانه - میله‌ای درآمد/هزینه + خطی تراز
    """
    
    # جمع‌آوری داده‌ها بر اساس ماه
    monthly_income = defaultdict(int)
    monthly_expense = defaultdict(int)
    
    for tx in transactions:
        amount = tx[2]
        tx_type = tx[3]
        date_str = tx[6]  # تاریخ
        
        try:
            # استخراج سال و ماه از تاریخ
            parts = date_str.split('/')
            year = int(parts[0])
            month = int(parts[1])
            key = f"{month:02d}"  # فقط ماه
            
            if tx_type == 'income':
                monthly_income[key] += amount
            else:
                monthly_expense[key] += amount
        except:
            continue
    
    if not monthly_income and not monthly_expense:
        return None
    
    # نام ماه‌های فارسی
    month_names = {
        '01': 'فرو', '02': 'ارد', '03': 'خرد',
        '04': 'تیر', '05': 'مرد', '06': 'شهر',
        '07': 'مهر', '08': 'آبا', '09': 'آذر',
        '10': 'دی', '11': 'بهم', '12': 'اسف'
    }
    
    # مرتب‌سازی ماه‌ها
    all_months = sorted(set(monthly_income.keys()) | set(monthly_expense.keys()))
    
    if not all_months:
        return None
    
    months = [reshape_persian(month_names.get(m, m)) for m in all_months]
    incomes = [monthly_income[m] / 1000000 for m in all_months]  # به میلیون
    expenses = [monthly_expense[m] / 1000000 for m in all_months]
    
    # محاسبه درصد سود (تراز / درآمد)
    profit_margins = []
    for inc, exp in zip(incomes, expenses):
        if inc > 0:
            margin = ((inc - exp) / inc) * 100
        else:
            margin = 0
        profit_margins.append(margin)
    
    # ساخت نمودار
    fig, ax1 = plt.subplots(figsize=(12, 6), facecolor='white')
    ax1.set_facecolor('white')
    
    x = range(len(months))
    width = 0.35
    
    # نمودار میله‌ای - درآمد (آبی)
    bars1 = ax1.bar([i - width/2 for i in x], incomes, width, 
                     label=reshape_persian('درآمد'), color='#4A90D9', edgecolor='white')
    
    # نمودار میله‌ای - هزینه (آبی روشن‌تر)
    bars2 = ax1.bar([i + width/2 for i in x], expenses, width,
                     label=reshape_persian('هزینه'), color='#7CB9E8', edgecolor='white')
    
    # تنظیمات محور اول (میله‌ای)
    ax1.set_xlabel('')
    ax1.set_ylabel(reshape_persian('مبلغ (میلیون ریال)'), color='#4A90D9', fontsize=11)
    ax1.tick_params(axis='y', labelcolor='#4A90D9')
    ax1.set_xticks(x)
    ax1.set_xticklabels(months, fontsize=10)
    
    # حذف خطوط اضافی
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['left'].set_color('#E0E0E0')
    ax1.spines['bottom'].set_color('#E0E0E0')
    
    # خطوط راهنمای افقی
    ax1.yaxis.grid(True, linestyle='-', alpha=0.3, color='#E0E0E0')
    ax1.set_axisbelow(True)
    
    # محور دوم برای نمودار خطی (درصد سود)
    ax2 = ax1.twinx()
    line = ax2.plot(x, profit_margins, color='#F4B942', marker='o', 
                    linewidth=2, markersize=8, label=reshape_persian('درصد سود'))
    
    ax2.set_ylabel(reshape_persian('درصد سود'), color='#F4B942', fontsize=11)
    ax2.tick_params(axis='y', labelcolor='#F4B942')
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_color('#F4B942')
    ax2.spines['left'].set_visible(False)
    
    # فرمت درصد
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1f}%'))
    
    # لجند
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', 
               framealpha=0.9, facecolor='white', edgecolor='#E0E0E0')
    
    plt.tight_layout()
    
    # ذخیره
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close(fig)
    
    return buf


def create_expense_pie_chart(transactions):
    """
    نمودار دایره‌ای هزینه‌ها - استایل مدرن
    """
    category_totals = defaultdict(int)

    for tx in transactions:
        amount = tx[2]
        tx_type = tx[3]
        category = tx[4]

        if tx_type == 'expense':
            category_totals[category] += amount

    if not category_totals:
        return None

    categories = list(category_totals.keys())
    amounts = list(category_totals.values())
    total = sum(amounts)
    percentages = [(a / total) * 100 for a in amounts]

    # رنگ‌های مدرن
    colors = ['#4A90D9', '#7CB9E8', '#F4B942', '#5CB85C', '#D9534F', 
              '#9B59B6', '#1ABC9C', '#E67E22', '#34495E', '#95A5A6']

    fig, ax = plt.subplots(figsize=(10, 8), facecolor='white')
    ax.set_facecolor('white')

    wedges, texts, autotexts = ax.pie(
        amounts,
        labels=[reshape_persian(cat) for cat in categories],
        autopct=lambda pct: f'{pct:.1f}%' if pct > 5 else '',
        colors=colors[:len(categories)],
        explode=[0.02] * len(categories),
        shadow=False,
        startangle=90
    )

    for text in texts:
        text.set_color('#333333')
        text.set_fontsize(11)

    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(10)
        autotext.set_weight('bold')

    title = reshape_persian(f'هزینه‌ها بر اساس دسته - مجموع: {total:,} ریال')
    ax.set_title(title, color='#333333', fontsize=14, pad=20)

    legend_labels = [
        f'{reshape_persian(cat)}: {amt:,} ({pct:.1f}%)'
        for cat, amt, pct in zip(categories, amounts, percentages)
    ]

    legend = ax.legend(
        wedges, legend_labels,
        title=reshape_persian('دسته‌بندی'),
        loc='center left',
        bbox_to_anchor=(1, 0, 0.5, 1),
        facecolor='white',
        edgecolor='#E0E0E0'
    )
    legend.get_title().set_color('#333333')

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close(fig)

    return buf


def create_income_expense_chart(transactions):
    """نمودار مقایسه درآمد و هزینه - استایل مدرن"""

    total_income = 0
    total_expense = 0

    for tx in transactions:
        amount = tx[2]
        tx_type = tx[3]

        if tx_type == 'income':
            total_income += amount
        else:
            total_expense += amount

    if total_income == 0 and total_expense == 0:
        return None

    fig, ax = plt.subplots(figsize=(8, 6), facecolor='white')
    ax.set_facecolor('white')

    categories = [reshape_persian('درآمد'), reshape_persian('هزینه')]
    values = [total_income / 1000000, total_expense / 1000000]  # به میلیون
    colors = ['#4A90D9', '#7CB9E8']

    bars = ax.bar(categories, values, color=colors, width=0.5, edgecolor='white')

    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax.annotate(f'{val:,.1f}M',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    color='#333333', fontsize=12, weight='bold')

    ax.set_ylabel(reshape_persian('مبلغ (میلیون ریال)'), color='#333333')
    ax.tick_params(colors='#333333')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#E0E0E0')
    ax.spines['bottom'].set_color('#E0E0E0')
    ax.yaxis.grid(True, linestyle='-', alpha=0.3, color='#E0E0E0')

    balance = (total_income - total_expense) / 1000000
    balance_text = reshape_persian(f'تراز: {balance:,.1f} میلیون ریال')
    balance_color = '#5CB85C' if balance >= 0 else '#D9534F'

    title = reshape_persian('مقایسه درآمد و هزینه')
    ax.set_title(f'{title}', color='#333333', fontsize=14)
    
    # نمایش تراز
    ax.text(0.5, 0.95, balance_text, transform=ax.transAxes, 
            ha='center', color=balance_color, fontsize=12, weight='bold')

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close(fig)

    return buf


def create_daily_trend_chart(transactions, days=30):
    """نمودار روند روزانه - خطی"""
    
    daily_data = defaultdict(lambda: {'income': 0, 'expense': 0})
    
    for tx in transactions:
        amount = tx[2]
        tx_type = tx[3]
        date_str = tx[6].split(' ')[0]  # فقط تاریخ بدون ساعت
        
        if tx_type == 'income':
            daily_data[date_str]['income'] += amount
        else:
            daily_data[date_str]['expense'] += amount
    
    if not daily_data:
        return None
    
    # مرتب‌سازی بر اساس تاریخ
    sorted_dates = sorted(daily_data.keys())[-days:]
    
    dates = [d.split('/')[2] for d in sorted_dates]  # فقط روز
    incomes = [daily_data[d]['income'] / 1000000 for d in sorted_dates]
    expenses = [daily_data[d]['expense'] / 1000000 for d in sorted_dates]
    
    fig, ax = plt.subplots(figsize=(12, 5), facecolor='white')
    ax.set_facecolor('white')
    
    x = range(len(dates))
    
    ax.plot(x, incomes, color='#4A90D9', marker='o', linewidth=2, 
            markersize=6, label=reshape_persian('درآمد'))
    ax.plot(x, expenses, color='#F4B942', marker='s', linewidth=2, 
            markersize=6, label=reshape_persian('هزینه'))
    
    ax.fill_between(x, incomes, alpha=0.2, color='#4A90D9')
    ax.fill_between(x, expenses, alpha=0.2, color='#F4B942')
    
    ax.set_xticks(x)
    ax.set_xticklabels(dates, fontsize=9)
    ax.set_ylabel(reshape_persian('میلیون ریال'), color='#333333')
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#E0E0E0')
    ax.spines['bottom'].set_color('#E0E0E0')
    ax.yaxis.grid(True, linestyle='-', alpha=0