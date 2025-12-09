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
    """فرمت‌بندی مبلغ به تومان"""
    if amount >= 10000000:  # بیشتر از 10 میلیون
        return f'{amount/1000000:.1f}M'
    elif amount >= 1000000:  # بیشتر از 1 میلیون
        return f'{amount/1000000:.1f}M'
    elif amount >= 1000:
        return f'{amount/1000:.0f}K'
    return str(amount)


def create_pie_chart(transactions):
    """
    نمودار دایره‌ای هزینه‌ها با نمایش مبلغ
    فرمت: (id, user_id, amount, type, category, description, date)
    """
    
    if not transactions:
        print("❌ تراکنشی نیست")
        return None
    
    print(f"🔍 create_pie_chart - تعداد: {len(transactions)}")
    
    category_totals = defaultdict(int)
    
    for tx in transactions:
        try:
            # ایندکس‌های ثابت
            amount = int(tx[2])
            tx_type = str(tx[3]).strip().lower()
            category = str(tx[4]).strip().replace('\u200c', '')
            
            if tx_type == 'expense' and amount > 0:
                category_totals[category] += amount
                
        except Exception as e:
            print(f"⚠️ خطا: {e}")
            continue
    
    print(f"📊 دسته‌ها: {dict(category_totals)}")
    
    if not category_totals:
        print("❌ هزینه‌ای نیست")
        return None
    
    # مرتب‌سازی بر اساس مبلغ
    sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    categories = [item[0] for item in sorted_categories]
    amounts = [item[1] for item in sorted_categories]
    total = sum(amounts)
    
    # رنگ‌های حرفه‌ای
    colors = [
        '#FF6B6B',  # قرمز ملایم
        '#4ECDC4',  # فیروزه‌ای
        '#45B7D1',  # آبی روشن
        '#96CEB4',  # سبز ملایم
        '#FFEAA7',  # زرد ملایم
        '#DDA0DD',  # بنفش ملایم
        '#98D8C8',  # سبز نعنایی
        '#F7DC6F',  # طلایی
        '#BB8FCE',  # ارغوانی
        '#85C1E9',  # آبی آسمانی
    ]
    
    # ایجاد نمودار
    fig, ax = plt.subplots(figsize=(12, 8), facecolor='#FAFAFA')
    ax.set_facecolor('#FAFAFA')
    
    # تابع نمایش درصد و مبلغ روی نمودار
    def make_autopct(values):
        def my_autopct(pct):
            total_val = sum(values)
            val = int(round(pct * total_val / 100.0))
            # نمایش درصد و مبلغ
            if pct > 5:
                return f'{pct:.1f}%\n({format_amount(val)})'
            return ''
        return my_autopct
    
    # اضافه کردن explode برای جدا کردن بزرگترین قطعه
    explode = [0.05 if i == 0 else 0.02 for i in range(len(categories))]
    
    wedges, texts, autotexts = ax.pie(
        amounts,
        labels=None,  # لیبل‌ها رو جداگانه میذاریم
        autopct=make_autopct(amounts),
        colors=colors[:len(categories)],
        explode=explode,
        startangle=90,
        wedgeprops={
            'edgecolor': 'white',
            'linewidth': 2,
            'antialiased': True
        },
        shadow=True,
        pctdistance=0.75
    )
    
    # استایل متن‌های درصد
    for autotext in autotexts:
        autotext.set_fontsize(9)
        autotext.set_color('#333333')
        autotext.set_fontweight('bold')
    
    # ایجاد Legend با جزئیات کامل
    legend_labels = []
    for cat, amt in zip(categories, amounts):
        pct = (amt / total) * 100
        label = f'{reshape_persian(cat)}: {amt:,} ({pct:.1f}%)'
        legend_labels.append(label)
    
    legend = ax.legend(
        wedges,
        legend_labels,
        title=reshape_persian('📁 دسته‌بندی هزینه‌ها'),
        loc='center left',
        bbox_to_anchor=(1, 0.5),
        fontsize=10,
        facecolor='white',
        edgecolor='#E0E0E0',
        framealpha=0.95
    )
    legend.get_title().set_fontsize(12)
    legend.get_title().set_fontweight('bold')
    
    # عنوان
    title = reshape_persian(f'📊 هزینه‌های ماهانه')
    subtitle = reshape_persian(f'مجموع: {total:,} ریال')
    
    ax.set_title(f'{title}\n{subtitle}', 
                 fontsize=14, 
                 fontweight='bold', 
                 color='#2C3E50',
                 pad=20)
    
    # اضافه کردن دایره مرکزی (Donut style)
    centre_circle = plt.Circle((0, 0), 0.50, fc='#FAFAFA', ec='white', linewidth=2)
    ax.add_artist(centre_circle)
    
    # متن مرکز
    ax.text(0, 0.05, reshape_persian('مجموع'), 
            ha='center', va='center', fontsize=10, color='#7F8C8D')
    ax.text(0, -0.1, f'{format_amount(total)}', 
            ha='center', va='center', fontsize=14, fontweight='bold', color='#2C3E50')
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                facecolor='#FAFAFA', edgecolor='none')
    buf.seek(0)
    plt.close(fig)
    
    print("✅ نمودار دایره‌ای آماده")
    return buf


def create_bar_chart(transactions):
    """
    نمودار میله‌ای ترکیبی - درآمد و هزینه روزانه با خط روند
    شبیه نمودار نمونه که کاربر داد
    """
    
    if not transactions:
        return None
    
    print(f"🔍 create_bar_chart - تعداد: {len(transactions)}")
    
    # گروه‌بندی بر اساس روز
    daily_income = defaultdict(int)
    daily_expense = defaultdict(int)
    
    for tx in transactions:
        try:
            amount = int(tx[2])
            tx_type = str(tx[3]).strip().lower()
            date = str(tx[6]).split()[0]  # فقط تاریخ بدون ساعت
            
            if tx_type == 'income':
                daily_income[date] += amount
            elif tx_type == 'expense':
                daily_expense[date] += amount
                
        except Exception as e:
            print(f"⚠️ خطا: {e}")
            continue
    
    # همه تاریخ‌ها
    all_dates = sorted(set(daily_income.keys()) | set(daily_expense.keys()))
    
    if not all_dates:
        # اگه روزانه نبود، کل ماه رو نشون بده
        total_income = sum(daily_income.values())
        total_expense = sum(daily_expense.values())
        
        if total_income == 0 and total_expense == 0:
            return None
        
        # نمودار ساده
        fig, ax = plt.subplots(figsize=(10, 6), facecolor='#FAFAFA')
        ax.set_facecolor('#FAFAFA')
        
        categories = [reshape_persian('درآمد'), reshape_persian('هزینه')]
        values = [total_income, total_expense]
        colors = ['#27AE60', '#E74C3C']
        
        bars = ax.bar(categories, values, color=colors, width=0.5, 
                      edgecolor='white', linewidth=2)
        
        for bar, val in zip(bars, values):
            ax.annotate(f'{val:,}',
                        xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                        xytext=(0, 5), textcoords="offset points",
                        ha='center', fontsize=12, fontweight='bold', color='#2C3E50')
        
        ax.set_title(reshape_persian('📈 مقایسه درآمد و هزینه'), 
                     fontsize=14, fontweight='bold', color='#2C3E50')
        
        balance = total_income - total_expense
        balance_color = '#27AE60' if balance >= 0 else '#E74C3C'
        ax.text(0.5, 0.95, reshape_persian(f'تراز: {balance:,} ریال'),
                transform=ax.transAxes, ha='center', color=balance_color,
                fontsize=12, fontweight='bold')
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='#FAFAFA')
        buf.seek(0)
        plt.close(fig)
        return buf
    
    # داده‌ها برای نمودار
    incomes = [daily_income.get(d, 0) for d in all_dates]
    expenses = [daily_expense.get(d, 0) for d in all_dates]
    
    # فقط روز رو نشون بده (بدون سال/ماه)
    labels = [d.split('/')[-1] for d in all_dates]  # فقط روز
    
    # ایجاد نمودار با دو محور
    fig, ax1 = plt.subplots(figsize=(14, 7), facecolor='#FAFAFA')
    ax1.set_facecolor('#FAFAFA')
    
    x = np.arange(len(labels))
    width = 0.35
    
    # میله‌های درآمد (آبی)
    bars1 = ax1.bar(x - width/2, incomes, width, 
                    label=reshape_persian('درآمد'),
                    color='#4A90D9', 
                    edgecolor='white', 
                    linewidth=1,
                    alpha=0.9)
    
    # میله‌های هزینه (قرمز)
    bars2 = ax1.bar(x + width/2, expenses, width,
                    label=reshape_persian('هزینه'),
                    color='#E74C3C',
                    edgecolor='white',
                    linewidth=1,
                    alpha=0.9)
    
    # تنظیمات محور اول
    ax1.set_xlabel(reshape_persian('روز'), fontsize=11, color='#2C3E50')
    ax1.set_ylabel(reshape_persian('مبلغ (ریال)'), fontsize=11, color='#2C3E50')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=9)
    ax1.tick_params(axis='y', labelcolor='#2C3E50')
    
    # فرمت محور Y
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format_amount(x)))
    
    # محور دوم برای خط روند (تراز)
    ax2 = ax1.twinx()
    
    # محاسبه تراز تجمعی
    cumulative_balance = []
    running_balance = 0
    for inc, exp in zip(incomes, expenses):
        running_balance += inc - exp
        cumulative_balance.append(running_balance)
    
    # خط روند سبز
    line = ax2.plot(x, cumulative_balance, 
                    color='#27AE60', 
                    linewidth=2.5,
                    marker='o',
                    markersize=6,
                    markerfacecolor='#27AE60',
                    markeredgecolor='white',
                    markeredgewidth=1.5,
                    label=reshape_persian('تراز تجمعی'),
                    zorder=5)
    
    ax2.set_ylabel(reshape_persian('تراز تجمعی'), fontsize=11, color='#27AE60')
    ax2.tick_params(axis='y', labelcolor='#27AE60')
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format_amount(x# ادامه‌ی create_bar_chart در charts.py
    ))
    
    # عنوان و تزئینات بصری
    ax1.set_title(reshape_persian('📈 روند ورود و خروج پول (روزانه)'), 
                  fontsize=14, fontweight='bold',
                  color='#2C3E50', pad=20)
    
    # خطوط شبکه، حذف حاشیه‌های بالا و راست
    ax1.grid(axis='y', linestyle='--', alpha=0.3, color='#BDC3C7')
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    # زیباتر کردن نمودار
    ax1.legend(loc='upper left', frameon=False)
    ax2.legend(loc='upper right', frameon=False)

    # نویسه‌ها روی هر میله
    for bar, val in zip(bars1, incomes):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                 format_amount(val),
                 ha='center', va='bottom', fontsize=9, color='#2C3E50')
    for bar, val in zip(bars2, expenses):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                 format_amount(val),
                 ha='center', va='bottom', fontsize=9, color='#C0392B')

    plt.tight_layout()

    # ذخیره در حافظه و برگرداندن به ربات
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='#FAFAFA')
    buf.seek(0)
    plt.close(fig)

    print("✅ نمودار میله‌ای ترکیبی ساخته شد")
    return buf
