# sms_parser.py - پارسر پیامک‌های بانکی ایران
import re

def parse_bank_sms(text):
    """تحلیل پیامک بانکی و استخراج اطلاعات"""
    
    result = {
        'amount': None,
        'type': None,  # expense یا income
        'bank': None,
        'balance': None,
        'description': None,
    }
    
    # تبدیل اعداد فارسی به انگلیسی
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    english_digits = '0123456789'
    translation_table = str.maketrans(persian_digits, english_digits)
    text = text.translate(translation_table)
    
    # حذف کاما و فاصله از اعداد
    text_clean = text.replace(',', '').replace('،', '')
    
    # ---------- تشخیص بانک ----------
    banks = {
        'ملت': ['ملت', 'mellat', 'بانک ملت'],
        'ملی': ['ملی', 'melli', 'بانک ملی'],
        'صادرات': ['صادرات', 'saderat'],
        'تجارت': ['تجارت', 'tejarat'],
        'سپه': ['سپه', 'sepah'],
        'پاسارگاد': ['پاسارگاد', 'pasargad'],
        'سامان': ['سامان', 'saman'],
        'پارسیان': ['پارسیان', 'parsian'],
        'اقتصاد نوین': ['اقتصاد', 'eghtesad', 'نوین'],
        'آینده': ['آینده', 'ayandeh'],
        'شهر': ['شهر', 'shahr'],
        'کشاورزی': ['کشاورزی', 'keshavarzi'],
        'رفاه': ['رفاه', 'refah'],
        'مسکن': ['مسکن', 'maskan'],
        'توسعه': ['توسعه', 'tose'],
        'دی': ['بانک دی', 'day'],
        'سینا': ['سینا', 'sina'],
        'خاورمیانه': ['خاورمیانه'],
        'ایران زمین': ['ایران زمین'],
        'کارآفرین': ['کارآفرین'],
    }
    
    text_lower = text.lower()
    for bank_name, keywords in banks.items():
        for keyword in keywords:
            if keyword in text_lower or keyword in text:
                result['bank'] = bank_name
                break
        if result['bank']:
            break
    
    # ---------- تشخیص نوع تراکنش ----------
    
    # کلمات برداشت/هزینه
    expense_keywords = [
        'برداشت', 'خرید', 'کسر', 'پرداخت', 'انتقال به', 
        'واریز به', 'بدهکار', 'کارت به کارت', 'قبض',
        'برداشت از', 'withdraw', 'purchase'
    ]
    
    # کلمات واریز/درآمد
    income_keywords = [
        'واریز', 'دریافت', 'انتقال از', 'بستانکار',
        'واریز از', 'حقوق', 'deposit', 'credit'
    ]
    
    for keyword in expense_keywords:
        if keyword in text:
            result['type'] = 'expense'
            break
    
    if not result['type']:
        for keyword in income_keywords:
            if keyword in text:
                result['type'] = 'income'
                break
    
    # ---------- استخراج مبلغ ----------
    
    # الگوهای مختلف مبلغ
    amount_patterns = [
        # برداشت 1,800,000 یا برداشت1800000
        r'برداشت\s*[:\s]*([0-9,]+)',
        # واریز 1,800,000
        r'واریز\s*[:\s]*([0-9,]+)',
        # مبلغ: 1,800,000
        r'مبلغ\s*[:\s]*([0-9,]+)',
        # خرید 500000 ریال
        r'خرید\s*[:\s]*([0-9,]+)',
        # پرداخت 500000
        r'پرداخت\s*[:\s]*([0-9,]+)',
        # کسر 500000
        r'کسر\s*[:\s]*([0-9,]+)',
        # -500,000 یا +500,000
        r'[+\-]\s*([0-9,]+)',
        # عدد بزرگ بین 10000 تا 999999999999
        r'\b([0-9]{5,12})\b',
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, text_clean)
        if match:
            amount_str = match.group(1).replace(',', '').replace(' ', '')
            try:
                amount = int(amount_str)
                # فقط مبالغ معقول (بین 1000 ریال تا 100 میلیارد ریال)
                if 1000 <= amount <= 100000000000:
                    result['amount'] = amount
                    break
            except ValueError:
                continue
    
    # ---------- استخراج مانده ----------
    balance_patterns = [
        r'مانده\s*[:\s]*([0-9,]+)',
        r'موجودی\s*[:\s]*([0-9,]+)',
        r'باقیمانده\s*[:\s]*([0-9,]+)',
    ]
    
    for pattern in balance_patterns:
        match = re.search(pattern, text_clean)
        if match:
            balance_str = match.group(1).replace(',', '').replace(' ', '')
            try:
                result['balance'] = int(balance_str)
                break
            except ValueError:
                continue
    
    # ---------- تشخیص خودکار نوع از روی مانده ----------
    # اگه نوع مشخص نشد ولی مانده کمتر از مبلغه، پس برداشته
    if not result['type'] and result['amount'] and result['balance']:
        if result['balance'] < result['amount']:
            result['type'] = 'expense'
    
    # اگه "برداشت" توی متن بود، حتماً expense هست
    if 'برداشت' in text:
        result['type'] = 'expense'
    elif 'واریز' in text and 'واریز به' not in text:
        result['type'] = 'income'
    
    # ---------- استخراج توضیحات ----------
    # شماره حساب
    account_match = re.search(r'حساب\s*[:\s]*([0-9]+)', text_clean)
    if account_match:
        result['description'] = f"حساب {account_match.group(1)}"
    
    return result


def test_parser():
    """تست پارسر با نمونه پیامک‌ها"""
    test_messages = [
        "حساب5710088813 برداشت1,800,000 مانده10,987,578 04/09/12-10:07",
        "بانک ملت\nبرداشت: 500,000 ریال\nمانده: 2,500,000 ریال",
        "واریز به حساب شما\nمبلغ: 5,000,000 ریال\nمانده: 7,500,000",
        "خرید از فروشگاه\nمبلغ 250000 ریال کسر شد",
    ]
    
    for msg in test_messages:
        print(f"\n{'='*50}")
        print(f"پیام: {msg[:50]}...")
        result = parse_bank_sms(msg)
        print(f"نتیجه: {result}")


if __name__ == "__main__":
    test_parser()
