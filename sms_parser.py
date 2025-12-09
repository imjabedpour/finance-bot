# sms_parser.py - تحلیل پیام‌های بانکی
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
    
    # حذف کاراکترهای خاص یونیکد (مثل ‪ و ‬)
    text = re.sub(r'[\u200e\u200f\u202a\u202b\u202c\u202d\u202e]', '', text)
    
    # ===== تشخیص نوع تراکنش از کلمات کلیدی (اول!) =====
    
    expense_keywords = ['برداشت', 'خرید', 'کارت به کارت', 'پرداخت', 'کسر', 'خریدکالا', 'انتقال از']
    income_keywords = ['واریز', 'وصول', 'دریافت', 'حقوق', 'انتقال به', 'واریزی']
    
    text_lower = text.lower()
    
    for keyword in expense_keywords:
        if keyword in text:
            result['type'] = 'expense'
            break
    
    for keyword in income_keywords:
        if keyword in text:
            result['type'] = 'income'
            break
    
    # ===== استخراج مانده (اول مانده رو پیدا کن تا با مبلغ اشتباه نشه) =====
    
    balance_patterns = [
        r'مانده[:\s]*([۰-۹0-9,،]+)',
        r'موجودی[:\s]*([۰-۹0-9,،]+)',
    ]
    
    for pattern in balance_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                balance_str = match.group(1).replace(',', '').replace('،', '')
                result['balance'] = int(balance_str)
                break
            except:
                continue
    
    # ===== استخراج مبلغ =====
    
    # خطوط رو جدا کن
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        
        # اگه خط با مانده یا موجودی شروع میشه، رد کن
        if 'مانده' in line or 'موجودی' in line:
            continue
        
        # اگه خط شامل شماره حساب/کارت هست (مثل 101-1-6220704-1)، رد کن
        if re.match(r'^.*:\s*[\d\-]+$', line) and '-' in line and line.count('-') >= 2:
            continue
        
        # الگوی مبلغ با علامت + یا - در ابتدای خط
        amount_match = re.match(r'^([+\-])\s*([۰-۹0-9,،]+)\s*$', line)
        if amount_match:
            sign = amount_match.group(1)
            amount_str = amount_match.group(2).replace(',', '').replace('،', '')
            try:
                amount = int(amount_str)
                if amount >= 1000:  # حداقل ۱۰۰۰ ریال
                    result['amount'] = amount
                    # اگه نوع هنوز مشخص نشده، از علامت استفاده کن
                    if result['type'] is None:
                        result['type'] = 'income' if sign == '+' else 'expense'
                    break
            except:
                continue
    
    # اگه هنوز مبلغ پیدا نشده، الگوهای دیگه رو چک کن
    if result['amount'] is None:
        # حذف خطوط شماره حساب
        clean_text = text
        # حذف خطوطی که شماره حساب دارن
        clean_text = re.sub(r'(برداشت|واریز)[:\s]*[\d\-]+', '', clean_text)
        
        amount_patterns = [
            # مبلغ با کلمه "مبلغ"
            r'مبلغ[:\s]*([۰-۹0-9,،]+)',
            # عدد بزرگ تنها در یک خط (بدون شماره حساب)
            r'^[+\-]?\s*([۰-۹0-9]{1,3}(?:[,،][۰-۹0-9]{3})+)\s*$',
            # عدد ۶ رقمی یا بیشتر
            r'(?<![۰-۹0-9\-])([۰-۹0-9]{6,})(?![۰-۹0-9\-])',
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, clean_text, re.MULTILINE)
            for match in matches:
                try:
                    amount_str = match.replace(',', '').replace('،', '')
                    amount = int(amount_str)
                    # مبلغ باید بین ۱۰۰۰ ریال و ۱۰۰ میلیارد ریال باشه
                    # و نباید برابر مانده باشه
                    if 1000 <= amount <= 100000000000:
                        if result['balance'] is None or amount != result['balance']:
                            result['amount'] = amount
                            break
                except:
                    continue
            if result['amount']:
                break
    
    # ===== تشخیص بانک =====
    
    banks = {
        'سامان': 'سامان', 'ملت': 'ملت', 'ملی': 'ملی',
        'صادرات': 'صادرات', 'تجارت': 'تجارت', 'سپه': 'سپه',
        'پاسارگاد': 'پاسارگاد', 'پارسیان': 'پارسیان',
        'رسالت': 'رسالت', 'شهر': 'شهر', 'آینده': 'آینده',
        'مسکن': 'مسکن', 'کشاورزی': 'کشاورزی', 'رفاه': 'رفاه',
    }
    
    for bank_name in banks:
        if bank_name in text:
            result['bank'] = banks[bank_name]
            break
    
    # ===== دسته‌بندی پیش‌فرض =====
    
    if 'خریدکالا' in text or 'خرید کالا' in text:
        result['description'] = 'خرید کالا'
        result['category'] = 'خرید'
    elif result['type'] == 'expense':
        result['category'] = 'سایر'
    elif result['type'] == 'income':
        result['category'] = 'سایر'
    
    return result
