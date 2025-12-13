# charts.py - نمودارهای مالی حرفه‌ای
import numpy as np
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
plt.rcParams['axes.unicode_minus'] = False

def reshape_farsi(text):
    """تبدیل متن فارسی برای نمایش صحیح"""
    try:
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    except:
        return str(text)

def format_amount(amount):
    """فرمت‌بندی مبلغ"""
    if amount >= 1000000:
        return f'{amount/1000000:.1f}M'
    elif amount >= 1000:
        return f'{amount/1000:.0f}K'
    return str(int(amount))


def create_pie_chart(transactions):
    """نمودار دایره‌ای هزینه‌ها"""
    if not transactions:
        return None

    category_totals = defaultdict(int)

    for tx in transactions:
        try:
            amount = int(tx[2])
            tx_type = str(tx[3]).strip().lower()
            category = str(tx[4]).strip()

            if tx_type == 'expense' and amount > 0:
                category_totals[category] += amount
        except:
            continue

    if not category_totals:
        return None

    sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    categories = [item[0] for item in sorted_categories]
    amounts = [item[1] for item in sorted_categories]
    total = sum(amounts)

    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
              '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']

    fig, ax = plt.subplots(figsize=(12, 8), facecolor='#FAFAFA')
    ax.set_facecolor('#FAFAFA')

    def make_autopct(values):
        def my_autopct(pct):
            val = int(round(pct * sum(values) / 100.0))
            if pct > 5:
                return f'{pct:.1f}%\n({format_amount(val)})'
            return ''
        return my_autopct

    explode = [0.05 if i == 0 else 0.02 for i in range(len(categories))]

    wedges, texts, autotexts = ax.pie(
        amounts,
        autopct=make_autopct(amounts),
        colors=colors[:len(categories)],
        explode=explode,
        startangle=90,
        wedgeprops={'edgecolor': 'white', 'linewidth': 2},
        shadow=True,
        pctdistance=0.75
    )

    for autotext in autotexts:
        autotext.set_fontsize(9)
        autotext.set_color('#333333')
        autotext.set_fontweight('bold')

    legend_labels = []
    for cat, amt in zip(categories, amounts):
        pct = (amt / total) * 100
        label = f'{reshape_farsi(cat)}: {amt:,} ({pct:.1f}%)'
        legend_labels.append(label)

    ax.legend(wedges, legend_labels,
              title=reshape_farsi('دسته‌بندی'),
              loc='center left',
              bbox_to_anchor=(1, 0.5),
              fontsize=10)

    ax.set_title(f'{reshape_farsi("هزینه‌های ماهانه")}\n{reshape_farsi(f"مجموع: {total:,} ریال")}',
                 fontsize=14, fontweight='bold', color='#2C3E50', pad=20)

    centre_circle = plt.Circle((0, 0), 0.50, fc='#FAFAFA')
    ax.add_artist(centre_circle)

    ax.text(0, 0, f'{format_amount(total)}', ha='center', va='center',
            fontsize=14, fontweight='bold', color='#2C3E50')

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='#FAFAFA')
    buf.seek(0)
    plt.close(fig)

    return buf


def create_daily_chart(transactions):
    """نمودار میله‌ای روزانه"""
    if not transactions:
        return None

    daily_income = defaultdict(int)
    daily_expense = defaultdict(int)

    for tx in transactions:
        try:
            amount = int(tx[2])
            tx_type = str(tx[3]).strip().lower()
            date = str(tx[6]).split()[0]

            if tx_type == 'income':
                daily_income[date] += amount
            elif tx_type == 'expense':
                daily_expense[date] += amount
        except:
            continue

    all_dates = sorted(set(daily_income.keys()) | set(daily_expense.keys()))

    if not all_dates:
        return None

    # فقط ۱۴ روز اخیر
    all_dates = all_dates[-14:]

    incomes = [daily_income.get(d, 0) for d in all_dates]
    expenses = [daily_expense.get(d, 0) for d in all_dates]
    labels = [d.split('/')[-1] for d in all_dates]

    fig, ax1 = plt.subplots(figsize=(14, 7), facecolor='#FAFAFA')
    ax1.set_facecolor('#FAFAFA')

    x = list(range(len(labels)))
    width = 0.35

    bars1 = ax1.bar([i - width/2 for i in x], incomes, width, 
                    label=reshape_farsi('درآمد'), color='#4A90D9', edgecolor='white')
    bars2 = ax1.bar([i + width/2 for i in x], expenses, width, 
                    label=reshape_farsi('هزینه'), color='#E74C3C', edgecolor='white')

    ax1.set_xlabel(reshape_farsi('روز'), fontsize=11)
    ax1.set_ylabel(reshape_farsi('مبلغ'), fontsize=11)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=9)

    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: format_amount(val)))

    # محور دوم - خط تراز تجمعی
    ax2 = ax1.twinx()

    cumulative_balance = []
    running = 0
    for inc, exp in zip(incomes, expenses):
        running += inc - exp
        cumulative_balance.append(running)

    ax2.plot(x, cumulative_balance, color='#27AE60', linewidth=2.5,
             marker='o', markersize=6, label=reshape_farsi('تراز تجمعی'), linestyle='-', zorder=10)

    ax2.set_ylabel(reshape_farsi('تراز'), fontsize=11, color='#27AE60')
    ax2.tick_params(axis='y', labelcolor='#27AE60')
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: format_amount(val)))

    ax1.set_title(reshape_farsi('روند ورود و خروج پول - روزانه'),
                  fontsize=14, fontweight='bold', color='#2C3E50', pad=20)

    ax1.grid(axis='y', linestyle='--', alpha=0.3)
    ax1.spines['top'].set_visible(False)
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='#FAFAFA')
    buf.seek(0)
    plt.close(fig)

    return buf


def create_weekly_chart(transactions):
    """نمودار هفتگی"""
    if not transactions:
        return None

    weekly_data = defaultdict(lambda: {'income': 0, 'expense': 0})

    for tx in transactions:
        try:
            amount = int(tx[2])
            tx_type = str(tx[3]).strip().lower()
            date_str = str(tx[6]).split()[0]
            
            parts = date_str.split('/')
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            week_num = (day - 1) // 7 + 1
            week_key = f"{year}/{month:02d}-W{week_num}"

            if tx_type == 'income':
                weekly_data[week_key]['income'] += amount
            elif tx_type == 'expense':
                weekly_data[week_key]['expense'] += amount
        except:
            continue

    if not weekly_data:
        return None

    sorted_weeks = sorted(weekly_data.keys())[-4:]

    week_labels = [f"W{w.split('-W')[1]}" for w in sorted_weeks]
    incomes = [weekly_data[w]['income'] for w in sorted_weeks]
    expenses = [weekly_data[w]['expense'] for w in sorted_weeks]
    balances = [weekly_data[w]['income'] - weekly_data[w]['expense'] for w in sorted_weeks]

    fig, ax = plt.subplots(figsize=(10, 6), facecolor='#FAFAFA')
    ax.set_facecolor('#FAFAFA')

    x = list(range(len(week_labels)))
    width = 0.25

    ax.bar([i - width for i in x], incomes, width, label=reshape_farsi('درآمد'), color='#27ae60')
    ax.bar(x, expenses, width, label=reshape_farsi('هزینه'), color='#e74c3c')
    ax.bar([i + width for i in x], balances, width, label=reshape_farsi('تراز'), color='#3498db')

    ax.set_xlabel(reshape_farsi('هفته'), fontsize=12)
    ax.set_ylabel(reshape_farsi('مبلغ (ریال)'), fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(week_labels)
    ax.legend()
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: format_amount(val)))

    ax.set_title(reshape_farsi('نمودار هفتگی (۴ هفته اخیر)'),
                 fontsize=14, fontweight='bold', color='#2C3E50', pad=15)

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='#FAFAFA')
    buf.seek(0)
    plt.close(fig)

    return buf


def create_monthly_chart(months_data):
    """نمودار ماهانه - ۳ ماه اخیر"""
    if not months_data:
        return None

    month_names_fa = ["", "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
                      "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]

    labels = []
    incomes = []
    expenses = []
    balances = []

    for m in months_data:
        name = m.get('name', '')
        if '/' in name:
            try:
                month_num = int(name.split('/')[1])
                labels.append(reshape_farsi(month_names_fa[month_num]))
            except:
                labels.append(reshape_farsi(name))
        else:
            labels.append(reshape_farsi(name))

        incomes.append(m.get('income', 0))
        expenses.append(m.get('expense', 0))
        balances.append(m.get('income', 0) - m.get('expense', 0))

    fig, ax = plt.subplots(figsize=(10, 6), facecolor='#FAFAFA')
    ax.set_facecolor('#FAFAFA')

    x = list(range(len(labels)))
    width = 0.25

    ax.bar([i - width for i in x], incomes, width, label=reshape_farsi('درآمد'), color='#27ae60')
    ax.bar(x, expenses, width, label=reshape_farsi('هزینه'), color='#e74c3c')
    ax.bar([i + width for i in x], balances, width, label=reshape_farsi('تراز'), color='#3498db')

    ax.set_xlabel(reshape_farsi('ماه'), fontsize=12)
    ax.set_ylabel(reshape_farsi('مبلغ (ریال)'), fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    ax.legend()
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: format_amount(val)))

    ax.set_title(reshape_farsi('نمودار ماهانه (۳ ماه اخیر)'),
                 fontsize=14, fontweight='bold', color='#2C3E50', pad=15)

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='#FAFAFA')
    buf.seek(0)
    plt.close(fig)

    return buf
