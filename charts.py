# charts.py - ساخت نمودارهای مالی
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from bidi.algorithm import get_display
import arabic_reshaper
import io
from collections import defaultdict

plt.rcParams['font.family'] = 'DejaVu Sans'


def reshape_persian(text):
    """تبدیل متن فارسی برای نمایش صحیح"""
    try:
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    except:
        return str(text)


def create_pie_chart(transactions):
    """نمودار دایره‌ای هزینه‌ها"""
    print("📊 شروع create_pie_chart...")
    
    category_totals = defaultdict(int)

    for tx in transactions:
        try:
            # tx: (id, user_id, amount, type, category, description, date)
            if len(tx) >= 5:
                amount = int(tx[2])  # ✅ تبدیل به int
                tx_type = str(tx[3])
                category = str(tx[4])

                if tx_type == 'expense':
                    category_totals[category] += amount
        except Exception as e:
            print(f"⚠️ خطا در پردازش تراکنش: {e}")
            continue

    print(f"📊 دسته‌بندی‌ها: {dict(category_totals)}")

    if not category_totals:
        print("⚠️ هیچ هزینه‌ای یافت نشد")
        return None

    categories = list(category_totals.keys())
    amounts = list(category_totals.values())
    total = sum(amounts)

    print(f"📊 مجموع هزینه: {total}")

    colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
              '#FF9F40', '#FF6384', '#C9CBCF', '#7BC225', '#B97CD1']

    fig, ax = plt.subplots(figsize=(10, 8), facecolor='white')

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
        text.set_fontsize(11)
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
    """نمودار میله‌ای مقایسه درآمد و هزینه"""
    print("📊 شروع create_bar_chart...")
    
    total_income = 0
    total_expense = 0

    for tx in transactions:
        try:
            if len(tx) >= 4:
                amount = int(tx[2])  # ✅ تبدیل به int
                tx_type = str(tx[3])

                if tx_type == 'income':
                    total_income += amount
                elif tx_type == 'expense':
                    total_expense += amount
        except Exception as e:
            print(f"⚠️ خطا در پردازش: {e}")
            continue

    print(f"📊 درآمد: {total_income}, هزینه: {total_expense}")

    if total_income == 0 and total_expense == 0:
        print("⚠️ داده‌ای برای نمودار نیست")
        return None

    fig, ax = plt.subplots(figsize=(8, 6), facecolor='white')

    categories = [reshape_persian('درآمد'), reshape_persian('هزینه')]
    values = [total_income, total_expense]
    colors = ['#4BC0C0', '#FF6384']

    bars = ax.bar(categories, values, color=colors, width=0.5, edgecolor='white')

    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax.annotate(f'{val:,}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=12, weight='bold')

    ax.set_ylabel(reshape_persian('مبلغ (ریال)'))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.yaxis.grid(True, linestyle='--', alpha=0.3)

    balance = total_income - total_expense
    balance_color = '#4BC0C0' if balance >= 0 else '#FF6384'
    balance_text = reshape_persian(f'تراز: {balance:,} ریال')

    ax.set_title(reshape_persian('مقایسه درآمد و هزینه'), fontsize=14)
    ax.text(0.5, 0.95, balance_text, transform=ax.transAxes,
            ha='center', color=balance_color, fontsize=12, weight='bold')

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close(fig)

    print("✅ نمودار میله‌ای ساخته شد")
    return buf
