# sms_parser.py - پارسر پیامک‌های بانکی
import re

def parse_bank_sms(text):
    """تحلیل پیام بانکی و استخراج اطلاعات"""
    
    result = {
        'amount': None,
        'type': None,  # 'income' یا 'expense'
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
    
    # حذف کاراکترهای اضافی
    text_clean = text.replace(',', '').replace('،', '')
    
    # ===== تشخیص نوع تراکنش =====
    
    # الگوی واریز با + در ابتدا (مثل پیام شما)
    if re.search(r'\+\s*\d+', text_clean):
        result['type'] = 'income'
    # الگوی برداشت با - در ابتدا
    elif re.search(r'-\s*\d+', text_clean) and not re.search(r'مانده|موجودی', text_clean.split('-')[0]):
        result['type'] = 'expense'
    # کلمات کلیدی واریز
    elif re.search(r'واریز|وصول|دریافت|حقوق|انتقال به|به حساب شما', text, re.IGNORECASE):
        result['type'] = 'income'
    # کلمات کلیدی برداشت
    elif re.search(r'برداشت|خرید|کارت به کارت|انتقال از|پرداخت|کسر', text, re.IGNORECASE):
        result['type'] = 'expense'
    
    # ===== استخراج مبلغ =====
    
    # الگوی مبلغ با + یا - (فرمت جدید)
    amount_match = re.search(r'[+\-]\s*(\d[\d,]*\d|\d+)', text_clean)
    if amount_match:
        amount_str = amount_match.group(1).replace(',', '')
        try:
            result['amount'] = int(amount_str)
        except:
            pass
    
    # اگه پیدا نشد، الگوهای دیگه رو امتحان کن
    if not result['amount']:
        patterns = [
            r'مبلغ[:\s]*(\d+)',
            r'(\d+)\s*ریال',
            r'(\d+)\s*تومان',
            r'مبلغ\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text_clean)
            if match:
                try:
                    result['amount'] = int(match.group(1))
                    break
                except:
                    continue
    
    # ===== استخراج مانده =====
    balance_patterns = [
        r'مانده[:\s]*(\d+)',
        r'موجودی[:\s]*(\d+)',
    ]
    
    for pattern in balance_patterns:
        match = re.search(pattern, text_clean)
        if match:
            try:
                result['balance'] = int(match.group(1))
                break
            except:
                continue
    
    # ===== تشخیص بانک =====
    banks = {
        'ملت': 'ملت',
        'ملی': 'ملی', 
        'صادرات': 'صادرات',
        'تجارت': 'تجارت',
        'سپه': 'سپه',
        'پاسارگاد': 'پاسارگاد',
        'سامان': 'سامان',
        'پارسیان': 'پارسیان',
        'اقتصاد': 'اقتصاد نوین',
        'رسالت': 'رسالت',
        'شهر': 'شهر',
        'آینده': 'آینده',
        'دی': 'دی',
        'سینا': 'سینا',
        'مسکن': 'مسکن',
        'کشاورزی': 'کشاورزی',
        'رفاه': 'رفاه',
    }
    
    for key, value in banks.items():
        if key in text:
            result['bank'] = value
            break
    
    # ===== تعیین دسته‌بندی پیش‌فرض =====
    if result['type'] == 'expense':
        if re.search(r'خرید|فروشگاه|مارکت|سوپر', text, re.IGNORECASE):
            result['category'] = 'خرید'
        elif re.search(r'رستوران|فست|غذا|کافه', text, re.IGNORECASE):
            result['category'] = 'خوراک'
        elif re.search(r'اسنپ|تپسی|تاکسی|بنزین|پارکینگ', text, re.IGNORECASE):
            result['category'] = 'حمل‌ونقل'
        elif re.search(r'قبض|برق|گاز|آب|تلفن|اینترنت', text, re.