# sms_parser.py
import re

def parse_bank_sms(text):
    """تحلیل پیام بانکی و استخراج اطلاعات"""
    
    result = {
        'amount': None,
        'type': None,
        'bank': None,
        'balance': None,
        'description': None,
        'category': None,
    }
    
    # تبدیل اعداد فارسی به انگلیسی
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    english_digits = '0123456789'
    translation_table = str.maketrans(persian_digits, english_digits)
    text = text.translate(translation_table)
    
    # حذف کاما و جداکننده
    text_clean = text.replace(',', '').replace('،', '')
    
    # تشخیص نوع تراکنش
    expense_keywords = ['برداشت', 'خرید', 'کارت به کارت', 'پرداخت', 'کسر', 'خریدکالا', 'خرید کالا']
    income_keywords = ['واریز', 'وصول', 'دریافت', 'حقوق', 'انتقال به']
    
    for keyword in expense_keywords:
        if keyword in text:
            result['type'] = 'expense'
            break
    
    if not result['type']:
        for keyword in income_keywords:
            if keyword in text:
                result['type'] = 'income'
                break
    
    # استخراج مبلغ - الگوهای مختلف بانک‌ها
    amount_patterns = [
        # بانک سامان: "برداشت مبلغ 4,730,000"
        r'(?:برداشت|واریز|خرید|پرداخت)\s*(?:مبلغ)?\s*[:\s]*(\d[\d,]*\d)',
        # الگوی "مبلغ X ریال"
        r'مبلغ[:\s]*(\d[\d,]*\d)',
        # الگوی عدد بزرگ (بیش از 4 رقم) قبل از "ریال"
        r'(\d{4,}[\d,]*)\s*(?:ریال|تومان)',
        # الگوی + یا - با عدد بزرگ
        r'[+\-]\s*(\d{4,}[\d,]*)',
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, text_clean)
        if match:
            try:
                amount_str = match.group(1).replace(',', '').replace('،', '')
                amount = int(amount_str)
                # فقط مبالغ بالای 1000 رو قبول کن (فیلتر شماره کارت)
                if amount >= 1000:
                    result['amount'] = amount
                    break
            except:
                continue
    
    # استخراج مانده
    balance_patterns = [
        r'مانده[:\s]*(\d[\d,]*\d)',
        r'موجودی[:\s]*(\d[\d,]*\d)',
    ]
    
    for pattern in balance_patterns:
        match = re.search(pattern, text_clean)
        if match:
            try:
                balance_str = match.group(1).replace(',', '').replace('،', '')
                result['balance'] = int(balance_str)
                break
            except:
                continue
    
    # تشخیص بانک
    banks = {
        'سامان': 'سامان',
        'ملت': 'ملت',
        'ملی': 'ملی',
        'صادرات': 'صادرات',
        'تجارت': 'تجارت',
        'سپه': 'سپه',
        'پاسارگاد': 'پاسارگاد',
        'پارسیان': 'پارسیان',
        'رسالت': 'رسالت',
        'شهر': 'شهر',
        'آینده': 'آینده',
        'مسکن': 'مسکن',
        'کشاورزی': 'کشاورزی',
        'رفاه': 'رفاه',
    }
    
    for bank_name in banks:
        if bank_name in text:
            result['bank'] = banks[bank_name]
            break
    
    # استخراج توضیحات (مثل خریدکالا)
    if 'خریدکالا' in text or 'خرید کالا' in text:
        result['description'] = 'خرید کالا'
        result['category'] = 'خرید'
    elif 'کارت به کارت' in text:
        result['description'] = 'کارت به کارت'
        result['category'] = 'سایر'
    elif result['type'] == 'expense':
        result['category'] = 'سایر'
    elif result['type'] == 'income':
        result['category'] = 'سایر'
    
    return result
