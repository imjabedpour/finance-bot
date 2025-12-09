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
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def create_pie_chart(transactions):
    """نمودار دایره‌ای هزینه‌ها"""
    category_totals = defaultdict(int)

    for tx in transactions:
        # tx: (id, user_id, amount, type, category, description, date)
        if len(tx) >= 5:
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

    title = reshape_persian(f'هزینه‌ها - مجموع: {total:,} ریال')
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


def create_bar_chart(transactions):
    """نمودار میله‌ای مقایسه درآمد و هزینه"""
    total_income = 0
    total_expense = 0

    for tx in transactions:
        if len(tx) >= 4:
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
    values = [total_income, total_expense]
    colors = ['#4A90D9', '#D9534F']

    bars = ax.bar(categories, values, color=colors, width=0.5, edgecolor='white')

    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax.annotate(f'{val:,}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    color='#333333', fontsize=12, weight='bold')

    ax.set_ylabel(reshape_persian('مبلغ (ریال)'), color='#333333')
    ax.tick_params(colors='#333333')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#E0E0E0')
    ax.spines['bottom'].set_color('#E0E0E0')
    ax.yaxis.grid(True, linestyle='-', alpha=0.3, color='#E0E0E0')

    balance = total_income - total_expense
    balance_text = reshape_persian(f'تراز: {balance:,} ریال')
    balance_color = '#5CB85C' if balance >= 0 else '#D9534F'

    title = reshape_persian('مقایسه درآمد و هزینه')
    ax.set_title(title, color='#333333', fontsize=14)
    
    ax.text(0.5, 0.95, balance_text, transform=ax.transAxes, 
            ha='center', color=balance_color, fontsize=12, weight='bold')

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    plt.close(fig)

    return buf


# تست
if __name__ == "__main__":
    test_transactions = [
        (1, 123, 500000, 'expense', 'خوراک', 'ناهار', '1404/09/18'),
        (2, 123, 200000, 'expense', 'حمل‌ونقل', 'تاکسی', '1404/09/18'),
        (3, 123, 5000000, 'income', 'حقوق', 'ماهانه', '1404/09/18'),
    ]

    chart = create_pie_chart(test_transactions)
    if chart:
        with open('test_pie.png', 'wb') as f:
            f.write(chart.read())
        print("✅ نمودار دایره‌ای ساخته شد")

    chart2 = create_bar_chart(test_transactions)
    if chart2:
        with open('test_bar.png', 'wb') as f:
            f.write(chart2.read())
        print("✅ نمودار میله‌ای ساخته شد")
