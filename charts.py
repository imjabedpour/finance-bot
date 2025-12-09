# charts.py - نمودارهای مالی حرفه‌ای
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from bidi.algorithm import get_display
import arabic_reshaper
import io
from collections import defaultdict
import numpy as np

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
    """فرمت‌بندی مبلغ"""
    if amount >= 1000000:
        return f'{amount/1000000:.1f}M'
    elif amount >= 1000:
        return f'{amount/1000:.0f}K'
    return str(int(amount))


def create_pie_chart(transactions):
    """نمودار دایره‌ای هزینه‌ها با نمایش مبلغ"""
    
    if not transactions:
        return None
    
    print(f"🔍 create_pie_chart - تعداد: {len(transactions)}")
    
    category_totals = defaultdict(int)
    
    for tx in transactions:
        try:
            amount = int(tx[2])
            tx_type = str(tx[3]).strip().lower()
            category = str(tx[4]).strip()
            
            if tx_type == 'expense' and amount > 0:
                category_totals[category] += amount
                
        except Exception as e:
            continue
    
    if not category_totals:
        return None
    
    # مرتب‌سازی
    sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    categories = [item[0] for item in sorted_categories]
    amounts = [item[1] for item in sorted_categories]
    total = sum(amounts)
    
    # رنگ‌ها
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', 
              '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']
    
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
    
    # عنوان
    ax.set_title(f'{reshape_persian("هزینه‌های ماهانه")}\n{reshape_persian(f"مجموع: {total:,} ریال")}',
                 fontsize=14, fontweight='bold', color='#2C3E50', pad=20)
    
    # دایره مرکزی
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


def create_bar_chart(transactions):
    """نمودار میله‌ای درآمد و هزینه روزانه"""
    
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
    
    incomes = [daily_income.get(d, 0) for d in all_dates]
    expenses = [daily_expense.get(d, 0) for d in all_dates]
    labels = [d.split('/')[-1] for d in all_dates]
    
    # ایجاد نمودار
    fig, ax1 = plt.subplots(figsize=(14, 7), facecolor='#FAFAFA')
    ax1.set_facecolor('#FAFAFA')
    
    x = np.arange(len(labels))
    width = 0.35
    
    # میله‌ها
    bars1 = ax1.bar(x - width/2, incomes, width, label=reshape_persian('درآمد'),
                    color='#4A90D9', edgecolor='white')
    bars2 = ax1.bar(x + width/2, expenses, width, label=reshape_persian('هزینه'),
                    color='#E74C3C', edgecolor='white')
    
    ax1.set_xlabel(reshape_persian('روز'), fontsize=11)
    ax1.set_ylabel(reshape_persian('مبلغ'), fontsize=11)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=9)
    
    # فرمت محور Y - اینجا اصلاح شد
    ax1.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda val, pos: format_amount(val))
    )
    
    # محور دوم - خط روند
    ax2 = ax1.twinx()
    
    cumulative_balance = []
    running = 0
    for inc, exp in zip(incomes, expenses):
        running += inc - exp
        cumulative_balance.append(running)
    
    ax2.plot(x, cumulative_balance, color='#27AE60', linewidth=2.5,
             marker='o', markersize=6, label=reshape_persian('تراز'))
    
    ax2.set_ylabel(reshape_persian('تراز'), fontsize=11, color='#27AE60')
    ax2.tick_params(axis='y', labelcolor='#27AE60')
    
    # فرمت محور Y دوم - اینجا هم اصلاح شد
    ax2.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda val, pos: format_amount(val))
    )
    
    # عنوان
    ax1.set_title(reshape_persian('روند ورود و خروج پول'),
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
