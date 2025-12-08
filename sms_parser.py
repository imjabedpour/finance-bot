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
    if re.search(r'\+\s*\d+', text_clean):
        result['type'] = 'income'
    elif re.search(r'واریز|وصول|دریافت|حقوق', text):
        result['type'] = 'income'
    elif re.search(r'برداشت|خرید|کارت به کارت|پرداخت|کسر', text):
        result['type'] = 'expense'
    elif re.search(r'-\s*\d+', text_clean):
        result['type'] = 'expense'
    
    # استخراج مبلغ با + یا -
    amount_match = re.search(r'[+\-]\s*(\d+)', text_clean)
    if amount_match:
        try:
            result['amount'] = int(amount_match.group(1))
        except:
            pass
    
    # اگه پیدا نشد
    if not result['amount']:
        patterns = [
            r'مبلغ[:\s]*(\d+)',
            r'(\d+)\s*ریال',
            r'(\d+)\s*تومان',
        ]
        for pattern in patterns:
            match = re.search(pattern, text_clean)
            if match:
                try:
                    result['amount'] = int(match.group(1))
                    break
                except:
                    continue
    
    # استخراج مانده
    balance_match = re.search(r'مانده[:\s]*(\d+)', text_clean)
    if balance_match:
        try:
            result['balance'] = int(balance_match.group(1))
        except:
            pass
    
    # تشخیص بانک
    banks = ['ملت', 'ملی', 'صادرات', 'تجارت', 'سپه', 'پاسارگاد', 'سامان', 'پارسیان', 'رسالت', 'شهر', 'آینده', 'مسکن', 'کشاورزی', 'رفاه']
    for bank in banks:
        if bank in text:
            result['bank'] = bank
            break
    
    # دسته‌بندی پیش‌فرض
    if result['type'] == 'expense':
        result['category'] = 'سایر'
    elif result['type'] == 'income':
        result['category'] = 'سایر'
    
    return result
