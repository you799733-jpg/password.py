import telebot
from telebot import types
import random
import time
import threading
import string
import hashlib
import base64
from datetime import datetime, timedelta

BOT_TOKEN = '8258092241:AAFFjF3T2RzWkSDDSaOwkW9MNYYTNpk0R9c'

bot = telebot.TeleBot(BOT_TOKEN)

# ========== قواعد البيانات المؤقتة ==========
# تخزين بيانات المستخدم الحالية (أثناء المحادثة)
user_data = {}

# تخزين آخر 5 كلمات سر لكل مستخدم
user_passwords = {}

# تخزين نقاط كل مستخدم
user_points = {}

# تخزين اللينكات المؤقتة
temp_links = {}

# ========== دالة توليد كلمة السر (الوضع العادي) ==========
def generate_password_normal(name, day, month, year):
    """
    توليد كلمة سر من الاسم وتاريخ الميلاد.
    """
    replacements = {
        'a': '@', 'A': '@',
        'o': '0', 'O': '0',
        'e': '3', 'E': '3',
        'i': '1', 'I': '1',
        's': '$', 'S': '$',
        't': '7', 'T': '7',
        'b': '8', 'B': '8',
        'g': '9', 'G': '9'
    }
    
    if name:
        first_char = name[0].upper()
        rest = name[1:] if len(name) > 1 else ""
        
        modified_rest = ""
        for char in rest:
            modified_rest += replacements.get(char, char)
        
        modified_name = first_char + modified_rest
    else:
        modified_name = "User"
    
    year_part = str(year)[-2:]
    
    symbols = ['!', '@', '#', '$', '%', '&', '*', 'Xz', 'Qp', 'Lm', 'Kt', 'Mn']
    random_symbol = random.choice(symbols)
    
    password = f"{modified_name}_{day}{month}_{year_part}{random_symbol}"
    
    return password

# ========== دالة توليد كلمة سر عشوائية ==========
def generate_password_random(length=16):
    """
    توليد كلمة سر عشوائية بالكامل.
    """
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    symbols = '!@#$%&*_-+='
    
    # نتأكد إن كل الأنواع موجودة
    password = [
        random.choice(lowercase),
        random.choice(uppercase),
        random.choice(digits),
        random.choice(symbols)
    ]
    
    # نكمل الباقي عشوائي
    all_chars = lowercase + uppercase + digits + symbols
    for i in range(length - 4):
        password.append(random.choice(all_chars))
    
    # نخلط الترتيب
    random.shuffle(password)
    
    return ''.join(password)

# ========== دالة توليد كلمة سر من عبارة ==========
def generate_password_phrase(phrase):
    """
    تحويل جملة لكلمة سر قوية.
    """
    replacements = {
        'a': '@', 'A': '4',
        'e': '3', 'E': '3',
        'i': '1', 'I': '1',
        'o': '0', 'O': '0',
        's': '$', 'S': '5',
        't': '7', 'T': '7',
        ' ': '_'
    }
    
    # ناخد أول حرف من كل كلمة + نستبدل الحروف
    words = phrase.split()
    result = ""
    
    for word in words:
        if word:
            # نضيف الحرف الأول كبير
            char = word[0].upper()
            result += replacements.get(char, char)
    
    # نضيف الطول الإجمالي في الآخر
    result += str(len(phrase))
    
    # نضيف رموز عشوائية
    symbols = ['!', '@', '#', '$', '%']
    result += random.choice(symbols)
    
    return result

# ========== دالة تحليل قوة كلمة السر ==========
def analyze_password(password):
    """
    تحليل قوة كلمة السر وترجيع تقرير مفصل.
    """
    score = 0
    feedback = []
    
    # الطول
    length = len(password)
    if length >= 16:
        score += 40
        feedback.append("✅ طول كلمة السر ممتاز (16+ حرف)")
    elif length >= 12:
        score += 30
        feedback.append("✅ طول كلمة السر جيد (12-15 حرف)")
    elif length >= 8:
        score += 20
        feedback.append("⚠️ طول كلمة السر متوسط (8-11 حرف)")
    else:
        score += 5
        feedback.append("❌ كلمة السر قصيرة جداً (أقل من 8 حروف)")
    
    # وجود حروف كبيرة وصغيرة
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    
    if has_upper and has_lower:
        score += 20
        feedback.append("✅ فيها حروف كبيرة وصغيرة")
    else:
        feedback.append("❌ ناقصة حروف كبيرة أو صغيرة")
    
    # وجود أرقام
    has_digit = any(c.isdigit() for c in password)
    if has_digit:
        score += 15
        feedback.append("✅ فيها أرقام")
    else:
        feedback.append("❌ مفيش أرقام")
    
    # وجود رموز
    has_symbol = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/~`' for c in password)
    if has_symbol:
        score += 15
        feedback.append("✅ فيها رموز خاصة")
    else:
        feedback.append("❌ مفيش رموز خاصة")
    
    # تنوع الأحرف
    unique_chars = len(set(password.lower()))
    if unique_chars >= 12:
        score += 10
        feedback.append("✅ تنوع الأحرف ممتاز")
    elif unique_chars >= 8:
        score += 5
        feedback.append("⚠️ تنوع الأحرف متوسط")
    else:
        feedback.append("❌ في تكرار كبير في الأحرف")
    
    # تحديد مستوى القوة
    if score >= 80:
        strength = "قوية جداً 💪💪💪"
        color = "🟢"
    elif score >= 60:
        strength = "قوية 💪💪"
        color = "🟡"
    elif score >= 40:
        strength = "متوسطة 💪"
        color = "🟠"
    else:
        strength = "ضعيفة"
        color = "🔴"
    
    return {
        'score': score,
        'strength': strength,
        'color': color,
        'feedback': feedback,
        'length': length
    }

# ========== دالة حفظ كلمة السر في القائمة ==========
def save_password(chat_id, password):
    """
    حفظ آخر 5 كلمات سر للمستخدم.
    """
    if chat_id not in user_passwords:
        user_passwords[chat_id] = []
    
    # نضيف كلمة السر مع وقت التوليد
    user_passwords[chat_id].append({
        'password': password,
        'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    # نخلي 5 بس
    if len(user_passwords[chat_id]) > 5:
        user_passwords[chat_id] = user_passwords[chat_id][-5:]

# ========== دالة إضافة نقاط ==========
def add_points(chat_id, points):
    """
    إضافة نقاط للمستخدم.
    """
    if chat_id not in user_points:
        user_points[chat_id] = 0
    user_points[chat_id] += points

# ========== دالة إنشاء لينك مؤقت ==========
def create_temp_link(chat_id, password):
    """
    إنشاء لينك مؤقت لمشاركة كلمة السر (يصلح لمدة 5 دقايق).
    """
    # ننشئ كود فريد
    timestamp = str(int(time.time()))
    code = hashlib.md5(f"{chat_id}{timestamp}{password}".encode()).hexdigest()[:10]
    
    # نخزن البيانات
    temp_links[code] = {
        'chat_id': chat_id,
        'password': password,
        'expires': datetime.now() + timedelta(minutes=5)
    }
    
    return code

# ========== دالة تشفير كلمة السر ==========
def encrypt_password(password, key):
    """
    تشفير كلمة السر بمفتاح المستخدم.
    """
    # تشفير بسيط باستخدام XOR مع المفتاح
    encrypted = ""
    key = key * (len(password) // len(key) + 1)
    
    for i in range(len(password)):
        encrypted += chr(ord(password[i]) ^ ord(key[i]))
    
    # تحويل لـ base64 عشان يبقى قابل للطباعة
    return base64.b64encode(encrypted.encode()).decode()

# ========== أمر البداية ==========
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("توليد كلمة سر 🔐", callback_data="menu_generate"))
    markup.add(types.InlineKeyboardButton("تحليل كلمة سر 🔍", callback_data="menu_analyze"))
    markup.add(types.InlineKeyboardButton("كلمات السر بتاعتي 📋", callback_data="menu_my_passwords"))
    markup.add(types.InlineKeyboardButton("الإحصائيات 📊", callback_data="menu_stats"))
    markup.add(types.InlineKeyboardButton("عن البوت ℹ️", callback_data="menu_about"))
    
    welcome_msg = bot.send_message(
        chat_id,
        "مرحب بيك في بوت توليد أقوى كلمات السر 🔐\n\n"
        "تقدر:\n"
        "• تولد كلمة سر قوية من اسمك وتاريخك\n"
        "• تحلل قوة أي كلمة سر\n"
        "• تحفظ آخر 5 كلمات سر\n"
        "• تشارك كلمة السر بأمان\n\n"
        "اختار من القايمة تحت 👇",
        reply_markup=markup
    )
    
    user_data[chat_id] = {'main_msg_id': welcome_msg.message_id}

# ========== دالة حذف الرسالة بعد 5 ثواني ==========
def delete_after_5(chat_id, message_id):
    time.sleep(5)
    try:
        bot.delete_message(chat_id, message_id)
    except:
        pass

# ========== التعامل مع القايمة الرئيسية ==========
@bot.callback_query_handler(func=lambda call: call.data.startswith('menu_'))
def menu_handler(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    action = call.data.replace('menu_', '')
    
    if action == 'about':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("رجوع للقايمة 🔙", callback_data="menu_back"))
        
        bot.edit_message_text(
            "البوت ده بيساعدك تولد كلمات سر قوية جداً بطرق مختلفة:\n\n"
            "1. من اسمك وتاريخ ميلادك\n"
            "2. كلمة سر عشوائية بالكامل\n"
            "3. تحويل جملة لكلمة سر\n"
            "4. توليد مخصص بطول معين\n\n"
            "وكمان تقدر تحلل قوة أي كلمة سر وتشوف نقاط ضعفها.\n"
            "بيقدر يحفظلك آخر 5 كلمات سر ويشاركها بأمان.\n\n"
            "كل ده ببلاش 😉",
            chat_id,
            msg_id,
            reply_markup=markup
        )
    
    elif action == 'back':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("توليد كلمة سر 🔐", callback_data="menu_generate"))
        markup.add(types.InlineKeyboardButton("تحليل كلمة سر 🔍", callback_data="menu_analyze"))
        markup.add(types.InlineKeyboardButton("كلمات السر بتاعتي 📋", callback_data="menu_my_passwords"))
        markup.add(types.InlineKeyboardButton("الإحصائيات 📊", callback_data="menu_stats"))
        markup.add(types.InlineKeyboardButton("عن البوت ℹ️", callback_data="menu_about"))
        
        bot.edit_message_text(
            "مرحب بيك في بوت توليد أقوى كلمات السر 🔐\n\n"
            "تقدر:\n"
            "• تولد كلمة سر قوية من اسمك وتاريخك\n"
            "• تحلل قوة أي كلمة سر\n"
            "• تحفظ آخر 5 كلمات سر\n"
            "• تشارك كلمة السر بأمان\n\n"
            "اختار من القايمة تحت 👇",
            chat_id,
            msg_id,
            reply_markup=markup
        )
    
    elif action == 'generate':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("من الاسم والتاريخ 👤", callback_data="gen_normal"))
        markup.add(types.InlineKeyboardButton("عشوائية 🎲", callback_data="gen_random"))
        markup.add(types.InlineKeyboardButton("من عبارة 📝", callback_data="gen_phrase"))
        markup.add(types.InlineKeyboardButton("مخصصة ⚙️", callback_data="gen_custom"))
        markup.add(types.InlineKeyboardButton("رجوع 🔙", callback_data="menu_back"))
        
        bot.edit_message_text(
            "اختار طريقة توليد كلمة السر اللي تناسبك 👇",
            chat_id,
            msg_id,
            reply_markup=markup
        )
    
    elif action == 'analyze':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("رجوع 🔙", callback_data="menu_back"))
        
        bot.edit_message_text(
            "ابعتلي كلمة السر اللي عايز تحللها، وهقولك هي قوية ولا ضعيفة وفيها إيه 🔍",
            chat_id,
            msg_id,
            reply_markup=markup
        )
        
        user_data[chat_id] = {
            'step': 'analyze',
            'main_msg_id': msg_id
        }
        
        bot.register_next_step_handler(call.message, analyze_user_password, chat_id, msg_id)
    
    elif action == 'my_passwords':
        show_my_passwords(chat_id, msg_id)
    
    elif action == 'stats':
        show_stats(chat_id, msg_id)

# ========== التعامل مع طرق التوليد ==========
@bot.callback_query_handler(func=lambda call: call.data.startswith('gen_'))
def generate_handler(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    gen_type = call.data.replace('gen_', '')
    
    if gen_type == 'normal':
        # نفس الطريقة القديمة
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("إلغاء ❌", callback_data="menu_generate"))
        
        bot.edit_message_text(
            "خلينا نبدأ...\n\n"
            "اكتب اسمك الأول بس ✍️",
            chat_id,
            msg_id,
            reply_markup=markup
        )
        
        user_data[chat_id] = {
            'step': 'name',
            'main_msg_id': msg_id,
            'gen_type': 'normal',
            'data': {}
        }
        
        bot.register_next_step_handler(call.message, get_name_normal, chat_id, msg_id)
    
    elif gen_type == 'random':
        # توليد كلمة سر عشوائية فوراً
        password = generate_password_random()
        save_password(chat_id, password)
        add_points(chat_id, 10)
        
        show_password_result(chat_id, msg_id, password, "عشوائية")
    
    elif gen_type == 'phrase':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("إلغاء ❌", callback_data="menu_generate"))
        
        bot.edit_message_text(
            "اكتب أي عبارة أو جملة، وهحولها لكلمة سر قوية 📝\n\n"
            "مثال: 'أنا بحب القهوة الصبح'",
            chat_id,
            msg_id,
            reply_markup=markup
        )
        
        user_data[chat_id] = {
            'step': 'phrase',
            'main_msg_id': msg_id
        }
        
        bot.register_next_step_handler(call.message, get_phrase, chat_id, msg_id)
    
    elif gen_type == 'custom':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("إلغاء ❌", callback_data="menu_generate"))
        
        bot.edit_message_text(
            "اكتب طول كلمة السر اللي عايزها (رقم من 8 لـ 32) ⚙️",
            chat_id,
            msg_id,
            reply_markup=markup
        )
        
        user_data[chat_id] = {
            'step': 'custom_length',
            'main_msg_id': msg_id
        }
        
        bot.register_next_step_handler(call.message, get_custom_length, chat_id, msg_id)

# ========== استقبال الاسم (الطريقة العادية) ==========
def get_name_normal(message, chat_id, main_msg_id):
    name = message.text.strip()
    
    threading.Thread(target=delete_after_5, args=(chat_id, message.message_id)).start()
    
    if len(name) > 50:
        msg = bot.send_message(chat_id, "❌ الاسم طويل شوية، اكتب اسم أقصر")
        threading.Thread(target=delete_after_5, args=(chat_id, msg.message_id)).start()
        bot.register_next_step_handler(message, get_name_normal, chat_id, main_msg_id)
        return
    
    user_data[chat_id]['data']['name'] = name
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("إلغاء ❌", callback_data="menu_generate"))
    
    bot.edit_message_text(
        "تمام، اكتب يوم ميلادك (رقم من 1 لـ 31) 📅",
        chat_id,
        main_msg_id,
        reply_markup=markup
    )
    
    user_data[chat_id]['step'] = 'day'
    bot.register_next_step_handler(message, get_day_normal, chat_id, main_msg_id)

# ========== استقبال اليوم ==========
def get_day_normal(message, chat_id, main_msg_id):
    try:
        day = int(message.text.strip())
        if day < 1 or day > 31:
            raise ValueError
    except:
        msg = bot.send_message(chat_id, "❌ مظبوط، اكتب رقم من 1 لـ 31")
        threading.Thread(target=delete_after_5, args=(chat_id, msg.message_id)).start()
        bot.register_next_step_handler(message, get_day_normal, chat_id, main_msg_id)
        return
    
    threading.Thread(target=delete_after_5, args=(chat_id, message.message_id)).start()
    
    user_data[chat_id]['data']['day'] = day
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("إلغاء ❌", callback_data="menu_generate"))
    
    bot.edit_message_text(
        "تمام، اكتب شهر ميلادك (رقم من 1 لـ 12) 📅",
        chat_id,
        main_msg_id,
        reply_markup=markup
    )
    
    user_data[chat_id]['step'] = 'month'
    bot.register_next_step_handler(message, get_month_normal, chat_id, main_msg_id)

# ========== استقبال الشهر ==========
def get_month_normal(message, chat_id, main_msg_id):
    try:
        month = int(message.text.strip())
        if month < 1 or month > 12:
            raise ValueError
    except:
        msg = bot.send_message(chat_id, "❌ مظبوط، اكتب رقم من 1 لـ 12")
        threading.Thread(target=delete_after_5, args=(chat_id, msg.message_id)).start()
        bot.register_next_step_handler(message, get_month_normal, chat_id, main_msg_id)
        return
    
    threading.Thread(target=delete_after_5, args=(chat_id, message.message_id)).start()
    
    user_data[chat_id]['data']['month'] = month
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("إلغاء ❌", callback_data="menu_generate"))
    
    bot.edit_message_text(
        "تمام، اكتب سنة ميلادك (زي: 1995) 📅",
        chat_id,
        main_msg_id,
        reply_markup=markup
    )
    
    user_data[chat_id]['step'] = 'year'
    bot.register_next_step_handler(message, get_year_normal, chat_id, main_msg_id)

# ========== استقبال السنة وتوليد كلمة السر ==========
def get_year_normal(message, chat_id, main_msg_id):
    try:
        year = int(message.text.strip())
        if year < 1900 or year > 2026:
            raise ValueError
    except:
        msg = bot.send_message(chat_id, "❌ سنة مش صحيحة، اكتب سنة بين 1900 و 2026")
        threading.Thread(target=delete_after_5, args=(chat_id, msg.message_id)).start()
        bot.register_next_step_handler(message, get_year_normal, chat_id, main_msg_id)
        return
    
    threading.Thread(target=delete_after_5, args=(chat_id, message.message_id)).start()
    
    name = user_data[chat_id]['data']['name']
    day = user_data[chat_id]['data']['day']
    month = user_data[chat_id]['data']['month']
    
    password = generate_password_normal(name, day, month, year)
    save_password(chat_id, password)
    add_points(chat_id, 10)
    
    show_password_result(chat_id, main_msg_id, password, "من الاسم والتاريخ")

# ========== استقبال العبارة ==========
def get_phrase(message, chat_id, main_msg_id):
    phrase = message.text.strip()
    
    threading.Thread(target=delete_after_5, args=(chat_id, message.message_id)).start()
    
    if len(phrase) < 3:
        msg = bot.send_message(chat_id, "❌ العبارة قصيرة، اكتب جملة أطول شوية")
        threading.Thread(target=delete_after_5, args=(chat_id, msg.message_id)).start()
        bot.register_next_step_handler(message, get_phrase, chat_id, main_msg_id)
        return
    
    password = generate_password_phrase(phrase)
    save_password(chat_id, password)
    add_points(chat_id, 10)
    
    show_password_result(chat_id, main_msg_id, password, "من عبارة")

# ========== استقبال الطول المخصص ==========
def get_custom_length(message, chat_id, main_msg_id):
    try:
        length = int(message.text.strip())
        if length < 8 or length > 32:
            raise ValueError
    except:
        msg = bot.send_message(chat_id, "❌ اكتب رقم من 8 لـ 32")
        threading.Thread(target=delete_after_5, args=(chat_id, msg.message_id)).start()
        bot.register_next_step_handler(message, get_custom_length, chat_id, main_msg_id)
        return
    
    threading.Thread(target=delete_after_5, args=(chat_id, message.message_id)).start()
    
    password = generate_password_random(length)
    save_password(chat_id, password)
    add_points(chat_id, 10)
    
    show_password_result(chat_id, main_msg_id, password, f"مخصصة (طول {length})")

# ========== عرض نتيجة كلمة السر مع خيارات ==========
def show_password_result(chat_id, msg_id, password, method):
    """
    عرض كلمة السر المتولدة مع تحليل سريع وخيارات متعددة.
    """
    analysis = analyze_password(password)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("مشاركة برابط آمن 🔗", callback_data=f"share_{password}"))
    markup.add(types.InlineKeyboardButton("تحليل مفصل 🔍", callback_data=f"analyze_{password}"))
    markup.add(types.InlineKeyboardButton("توليد كلمة تانية 🔄", callback_data="menu_generate"))
    markup.add(types.InlineKeyboardButton("القايمة الرئيسية 🏠", callback_data="menu_back"))
    
    bot.edit_message_text(
        f"تم توليد كلمة السر ✅\n\n"
        f"الطريقة: {method}\n"
        f"القوة: {analysis['strength']}\n"
        f"الطول: {analysis['length']} حرف\n\n"
        f"كلمة السر:\n"
        f"`{password}`\n\n"
        f"متشاركهاش مع أي حد وخليها في مكان آمن 🔒",
        chat_id,
        msg_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )
    
    if chat_id in user_data:
        del user_data[chat_id]

# ========== التعامل مع أزرار المشاركة والتحليل ==========
@bot.callback_query_handler(func=lambda call: call.data.startswith('share_') or call.data.startswith('analyze_'))
def password_actions_handler(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    action = call.data.split('_')[0]
    password = '_'.join(call.data.split('_')[1:])
    
    if action == 'share':
        # إنشاء لينك مؤقت
        code = create_temp_link(chat_id, password)
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("رجوع 🔙", callback_data="menu_generate"))
        
        bot.edit_message_text(
            f"تم إنشاء رابط مؤقت لكلمة السر 🔗\n\n"
            f"الرابط: `/get_password_{code}`\n\n"
            f"⚠️ الرابط هيفضل شغال لمدة 5 دقايق بس.\n"
            f"⚠️ الرابط هيشتغل مرة واحدة وبعدين يمسح نفسه.\n\n"
            f"ابعت الرابط ده للشخص اللي عايزه يشوف كلمة السر.",
            chat_id,
            msg_id,
            reply_markup=markup,
            parse_mode="Markdown"
        )
    
    elif action == 'analyze':
        # تحليل مفصل
        analysis = analyze_password(password)
        
        feedback_text = ""
        for item in analysis['feedback']:
            feedback_text += f"{item}\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("رجوع 🔙", callback_data="menu_generate"))
        
        bot.edit_message_text(
            f"تحليل كلمة السر 🔍\n\n"
            f"القوة: {analysis['strength']}\n"
            f"النقاط: {analysis['score']}/100\n"
            f"الطول: {analysis['length']} حرف\n\n"
            f"التفاصيل:\n"
            f"{feedback_text}",
            chat_id,
            msg_id,
            reply_markup=markup
        )

# ========== استقبال كلمة سر للتحليل من المستخدم ==========
def analyze_user_password(message, chat_id, main_msg_id):
    password = message.text.strip()
    
    threading.Thread(target=delete_after_5, args=(chat_id, message.message_id)).start()
    
    analysis = analyze_password(password)
    
    feedback_text = ""
    for item in analysis['feedback']:
        feedback_text += f"{item}\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("حلل كلمة تانية 🔍", callback_data="menu_analyze"))
    markup.add(types.InlineKeyboardButton("القايمة الرئيسية 🏠", callback_data="menu_back"))
    
    bot.edit_message_text(
        f"نتيجة التحليل 🔍\n\n"
        f"كلمة السر: `{password}`\n"
        f"القوة: {analysis['strength']}\n"
        f"النقاط: {analysis['score']}/100\n"
        f"الطول: {analysis['length']} حرف\n\n"
        f"التفاصيل:\n"
        f"{feedback_text}",
        chat_id,
        main_msg_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )
    
    if chat_id in user_data:
        del user_data[chat_id]

# ========== عرض كلمات السر المحفوظة ==========
def show_my_passwords(chat_id, msg_id):
    if chat_id not in user_passwords or len(user_passwords[chat_id]) == 0:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("توليد كلمة سر 🔐", callback_data="menu_generate"))
        markup.add(types.InlineKeyboardButton("القايمة الرئيسية 🏠", callback_data="menu_back"))
        
        bot.edit_message_text(
            "لسه مفيش كلمات سر محفوظة 📋\n\n"
            "روح ولد كلمة سر الأول 😉",
            chat_id,
            msg_id,
            reply_markup=markup
        )
        return
    
    passwords_text = ""
    for i, entry in enumerate(user_passwords[chat_id], 1):
        passwords_text += f"{i}. `{entry['password']}` - {entry['time']}\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("مسح كل الكلمات 🗑️", callback_data="clear_passwords"))
    markup.add(types.InlineKeyboardButton("تصدير الكلمات 📤", callback_data="export_passwords"))
    markup.add(types.InlineKeyboardButton("القايمة الرئيسية 🏠", callback_data="menu_back"))
    
    bot.edit_message_text(
        f"آخر 5 كلمات سر 🔐\n\n"
        f"{passwords_text}\n"
        f"اختار اللي عايزه 👇",
        chat_id,
        msg_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

# ========== مسح كلمات السر ==========
@bot.callback_query_handler(func=lambda call: call.data == 'clear_passwords')
def clear_passwords_handler(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    if chat_id in user_passwords:
        user_passwords[chat_id] = []
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("توليد كلمة سر 🔐", callback_data="menu_generate"))
    markup.add(types.InlineKeyboardButton("القايمة الرئيسية 🏠", callback_data="menu_back"))
    
    bot.edit_message_text(
        "تم مسح كل كلمات السر 🗑️\n\n"
        "تقدر تولد كلمات جديدة دلوقتي.",
        chat_id,
        msg_id,
        reply_markup=markup
    )

# ========== تصدير كلمات السر ==========
@bot.callback_query_handler(func=lambda call: call.data == 'export_passwords')
def export_passwords_handler(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    if chat_id not in user_passwords or len(user_passwords[chat_id]) == 0:
        bot.answer_callback_query(call.id, "مفيش كلمات سر عشان تصدرها")
        return
    
    # نطلب من المستخدم يدخل كلمة سر للتشفير
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("إلغاء ❌", callback_data="menu_back"))
    
    bot.edit_message_text(
        "عشان تصدر كلمات السر بشكل آمن، اكتب كلمة سر للتشفير 🔐\n\n"
        "الكلمة دي هتستخدم عشان تقدر تقرا الملف بعد كده.",
        chat_id,
        msg_id,
        reply_markup=markup
    )
    
    user_data[chat_id] = {
        'step': 'export_key',
        'main_msg_id': msg_id
    }
    
    bot.register_next_step_handler(call.message, get_export_key, chat_id, msg_id)

def get_export_key(message, chat_id, main_msg_id):
    key = message.text.strip()
    
    threading.Thread(target=delete_after_5, args=(chat_id, message.message_id)).start()
    
    # ننشئ محتوى الملف
    content = "كلمات السر المحفوظة:\n"
    content += "=" * 30 + "\n\n"
    
    for i, entry in enumerate(user_passwords.get(chat_id, []), 1):
        encrypted = encrypt_password(entry['password'], key)
        content += f"{i}. الوقت: {entry['time']}\n"
        content += f"   كلمة السر المشفرة: {encrypted}\n\n"
    
    content += "\n⚠️ استخدم نفس كلمة السر اللي دخلتها عشان تفك التشفير."
    
    # نبعته كملف
    bot.send_document(
        chat_id,
        content.encode(),
        visible_file_name="passwords_backup.txt"
    )
    
    # نمسح البيانات المؤقتة
    if chat_id in user_data:
        del user_data[chat_id]
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("القايمة الرئيسية 🏠", callback_data="menu_back"))
    
    bot.edit_message_text(
        "تم تصدير كلمات السر في ملف 📤\n\n"
        "الملف متشفر بكلمة السر اللي دخلتها.\n"
        "متنساش كلمة السر دي عشان تقدر تقرا الملف.",
        chat_id,
        main_msg_id,
        reply_markup=markup
    )

# ========== عرض الإحصائيات ==========
def show_stats(chat_id, msg_id):
    points = user_points.get(chat_id, 0)
    passwords_count = len(user_passwords.get(chat_id, []))
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("القايمة الرئيسية 🏠", callback_data="menu_back"))
    
    bot.edit_message_text(
        f"الإحصائيات بتاعتك 📊\n\n"
        f"النقاط: {points} ⭐\n"
        f"عدد كلمات السر المحفوظة: {passwords_count}/5\n"
        f"عدد مرات الاستخدام النهاردة: {points // 10}\n\n"
        f"كل ما تستخدم البوت أكتر، بتكسب نقاط أكتر 👆",
        chat_id,
        msg_id,
        reply_markup=markup
    )

# ========== استقبال رابط كلمة السر المؤقتة ==========
@bot.message_handler(commands=['get_password'])
def get_temp_password(message):
    chat_id = message.chat.id
    
    # نجيب الكود من الأمر
    try:
        code = message.text.split('_')[2]
    except:
        bot.reply_to(message, "❌ رابط غير صحيح")
        return
    
    if code not in temp_links:
        bot.reply_to(message, "❌ الرابط ده مش موجود أو انتهت صلاحيته")
        return
    
    link_data = temp_links[code]
    
    # نتأكد من الصلاحية
    if datetime.now() > link_data['expires']:
        del temp_links[code]
        bot.reply_to(message, "❌ الرابط ده انتهت صلاحيته (5 دقايق)")
        return
    
    # نعرض كلمة السر
    password = link_data['password']
    
    msg = bot.reply_to(message, f"🔐 كلمة السر:\n`{password}`\n\n⚠️ متشاركهاش مع أي حد تاني", parse_mode="Markdown")
    
    # نمسح الرابط بعد ما استخدم
    del temp_links[code]

# ========== تشغيل البوت ==========
print("✅ البوت الجبار شغال ومستني رسايل...")
print("الميزات:")
print("- 4 طرق لتوليد كلمة السر")
print("- تحليل قوة أي كلمة سر")
print("- حفظ آخر 5 كلمات سر")
print("- مشاركة برابط مؤقت")
print("- تصدير مشفر")
print("- نظام نقاط")
bot.infinity_polling()
