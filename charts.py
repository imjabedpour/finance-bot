# charts.py - نمودارهای مالی حرفه‌ای
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from bidi.algorithm import get_display
import arabic_reshaper
import io
from collections import defaultdict
import numpy as np
import jdatetime

# تنظیمات فونت
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

def reshape_persian(text):
    """تبدیل متن فارسی برای نمایش صحیح"""
    try:
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    except:
        return str(text)

def format_amount(amount):
    """فرمت‌بندی مبلغ به K و M"""
    if abs(amount) >= 1_000_000:
        return f'{amount/1_000_000:.1f}M'
    elif abs(amount) >= 1_000:
        return f'{amount/1_000:.0f}K'
    return str(int(amount))

# ================== رنگ‌های استاندارد ==================

COLORS = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
          '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
          '#F8B500', '#6C5CE7', '#A29BFE', '#FD79A8', '#00B894']

# ================== نمودار دایره‌ای ==================

def create_pie_chart(transactions):
    """نمودار دایره‌ای سهم هر دسته از هزینه‌ها"""

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

    # مرتب‌سازی بر اساس مبلغ
    sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    categories = [item[0] for item in sorted_categories]
    amounts = [item[1] for item in sorted_categories]
    total = sum(amounts)

    # ایجاد نمودار
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
        colors=COLORS[:len(categories)],
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

    # Legend
    legend_labels = []
    for cat, amt in zip(categories, amounts):
        pct = (amt / total) * 100
        label = f'{reshape_persian(cat)}: {amt:,} ({pct:.1f}%)'
        legend_labels.append(label)

    ax.legend(wedges, legend_labels,
              title=reshape_persian('دسته‌بندی'),
              loc='center left',
              bbox_to_anchor=(1, 0.5),
              fontsize=10)

    ax.set_title(f'{reshape_persian("🥧 سهم هر دسته از هزینه‌ها")}\n{reshape_persian(f"مجموع: {total:,} ریال")}',
                 fontsize=14, fontweight='bold', color='#2C3E50', pad=20)

    # دایره مرکزی (Donut)
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

# ================== نمودار روزانه ==================

def create_daily_chart(transactions):
    """نمودار میله‌ای روزانه + خط تراز تجمعی"""

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

    # مرتب‌سازی صحیح تاریخ‌ها
    all_dates = sorted(
        set(daily_income.keys()) | set(daily_expense.keys()),
        key=lambda d: [int(p) for p in d.split('/')]
    )

    if not all_dates:
        return None

    incomes = [daily_income.get(d, 0) for d in all_dates]
    expenses = [daily_expense.get(d, 0) for d in all_dates]

    # تراز تجمعی
    cumulative_balance = []
    running = 0
    for inc, exp in zip(incomes, expenses):
        running += inc - exp
        cumulative_balance.append(running)

    # فقط روز رو نشون بده
    labels = [d.split('/')[-1] for d in all_dates]

    # ایجاد نمودار
    fig, ax1 = plt.subplots(figsize=(14, 7), facecolor='#FAFAFA')
    ax1.set_facecolor('#FAFAFA')

    x = np.arange(len(labels))
    width = 0.35

    # میله‌ها
    ax1.bar(x - width/2, incomes, width, label=reshape_persian('درآمد'),
            color='#4A90D9', edgecolor='white')
    ax1.bar(x + width/2, expenses, width, label=reshape_persian('هزینه'),
            color='#E74C3C', edgecolor='white')

    ax1.set_xlabel(reshape_persian('روز'), fontsize=11)
    ax1.set_ylabel(reshape_persian('مبلغ'), fontsize=11)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=9)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: format_amount(val)))

    # محور دوم - خط تراز
    ax2 = ax1.twinx()
    ax2.plot(x, cumulative_balance,
             color='#27AE60',
             linewidth=3,
             marker='o',
             markersize=8,
             markerfacecolor='white',
             markeredgecolor='#27AE60',
             markeredgewidth=2,
             linestyle='-',
             zorder=10,
             label=reshape_persian('تراز تجمعی'))

    ax2.set_ylabel(reshape_persian('تراز تجمعی'), fontsize=11, color='#27AE60')
    ax2.tick_params(axis='y', labelcolor='#27AE60')
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: format_amount(val)))

    ax1.set_title(reshape_persian('📅 گزارش روزانه - درآمد و هزینه'),
                  fontsize=14, fontweight='bold', color='#2C3E50', pad=20)

    ax1.grid(axis='y', linestyle='--', alpha=0.3)
    ax1.spines['top'].set_visible(False)

    # Legend ترکیبی
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=10)

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='#FAFAFA')
    buf.seek(0)
    plt.close(fig)

    return buf

# ================== نمودار هفتگی ==================

def create_weekly_chart(transactions):
    """نمودار هفتگی - مقایسه هفته‌های ماه"""

    if not transactions:
        return None

    weekly_income = defaultdict(int)
    weekly_expense = defaultdict(int)

    for tx in transactions:
        try:
            amount = int(tx[2])
            tx_type = str(tx[3]).strip().lower()
            date_str = str(tx[6]).split()[0]

            parts = date_str.split('/')
            day = int(parts[2])

            # شماره هفته در ماه (۱-۵)
            week_num = (day - 1) // 7 + 1
            week_key = f"هفته {week_num}"

            if tx_type == 'income':
                weekly_income[week_key] += amount
            elif tx_type == 'expense':
                weekly_expense[week_key] += amount
        except:
            continue

    if not weekly_income and not weekly_expense:
        return None

    # مرتب‌سازی هفته‌ها
    weeks = ['هفته 1', 'هفته 2', 'هفته 3', 'هفته 4', 'هفته 5']
    weeks = [w for w in weeks if w in weekly_income or w in weekly_expense]

    if not weeks:
        return None

    incomes = [weekly_income.get(w, 0) for w in weeks]
    expenses = [weekly_expense.get(w, 0) for w in weeks]
    balances = [inc - exp for inc, exp in zip(incomes, expenses)]

    # ایجاد نمودار
    fig, ax = plt.subplots(figsize=(12, 7), facecolor='#FAFAFA')
    ax.set_facecolor('#FAFAFA')

    x = np.arange(len(weeks))
    width = 0.25

    bars1 = ax.bar(x - width, incomes, width, label=reshape_persian('درآمد'),
                   color='#4A90D9', edgecolor='white')
    bars2 = ax.bar(x, expenses, width, label=reshape_persian('هزینه'),
                   color='#E74C3C', edgecolor='white')
    
    # رنگ تراز بر اساس مثبت/منفی
    bar_colors = ['#27AE60' if b >= 0 else '#E67E22' for b in balances]
    bars3 = ax.bar(x + width, balances, width, label=reshape_persian('تراز'),
                   color=bar_colors, edgecolor='white')

    ax.set_xlabel(reshape_persian('هفته'), fontsize=11)
    ax.set_ylabel(reshape_persian('مبلغ (ریال)'), fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels([reshape_persian(w) for w in weeks], fontsize=10)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, pos: format_amount(val)))

    # مقدار روی میله‌ها
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            if height != 0:
                ax.annotate(format_amount(height),
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=8)

    ax.set_title(reshape_persian('📆 گزارش هفتگی - مقایسه هفته‌ها'),
                 fontsize=14, fontweight='bold', color='#2C3E50', pad=20)

    ax.legend(loc='upper right', fontsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='#FAFAFA')
    buf.seek(0)
    plt.close(fig)

    return buf

# ================== نمودار ماهانه ==================

def create_monthly_chart(months_data):
    """نمودار ماهانه - مقایسه ۳ ماه اخیر
    
    months_data: لیست دیکشنری با کلیدهای 'name', 'income', 'expense'
    """

    if not months_data:
        return None

    month_names = [m['name'] for m in months_data]
    incomes = [m['income'] for m in months_data]
    expenses = [m['expense'] for m in months_data]
    balances = [m['income'] - m['expense'] for m in months_data]

    # ایجاد نمودار
    fig, ax = plt.subplots(figsize=(12, 7), facecolor='#FAFAFA')
    ax.set_facecolor('#FAFAFA')

    x = np.arange(len(month_names))
    width = 0.25
 
    bars1 = ax.bar(x - width, incomes, width,
                   label=reshape_persian('درآمد'),
                   color='#4A90D9', edgecolor='white')

    bars2 = ax.bar(x, expenses, width,
                   label=reshape_persian('هزینه'),
                   color='#E74C3C', edgecolor='white')

    bar_colors = ['#27AE60' if b >= 0 else '#E67E22' for b in balances]
    bars3 = ax.bar(x + width, balances, width,
                   label=reshape_persian('تراز'),
                   color=bar_colors, edgecolor='white')

    ax.set_xlabel(reshape_persian('ماه'), fontsize=11)
    ax.set_ylabel(reshape_persian('مبلغ (ریال)'), fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels([reshape_persian(m) for m in month_names], fontsize=10)
    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda val, pos: format_amount(val))
    )

    # نمایش مقدار روی میله‌ها
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            if height != 0:
                ax.annotate(
                    format_amount(height),
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=8
                )

    ax.set_title(
        reshape_persian('🗓️ روند مالی ۳ ماه اخیر'),
        fontsize=14,
        fontweight='bold',
        color='#2C3E50',
        pad=20
    )

    ax.legend(loc='upper right', fontsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150,
                bbox_inches='tight', facecolor='#FAFAFA')
    buf.seek(0)
    plt.close(fig)

    return buf
