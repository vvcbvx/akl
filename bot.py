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
BASE_URL = "https://your-app-name.railway.app"  # سيتم تغييره بعد النشر

# تخزين بيانات المستخدمين
user_sessions = {}

# إعداد Flask لخادم الويب
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
        
        .user-info {
            background: #f8f9fa;
            padding: 15px;
            text-align: center;
            border-bottom: 1px solid #eee;
        }
        
        .user-info .name {
            font-weight: bold;
            color: #2d3436;
        }
        
        .user-info .id {
            color: #636e72;
            font-size: 14px;
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
        }
        
        .form-group input, .form-group select {
            width: 100%;
            padding: 15px;
            border: 2px solid #e9ecef;
            border-radius: 12px;
            font-size: 16px;
            transition: all 0.3s;
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
        }
        
        .package:hover, .package.selected {
            border-color: #667eea;
            background: #f8f9ff;
        }
        
        .package .amount {
            font-size: 18px;
            font-weight: bold;
            color: #2d3436;
        }
        
        .package .price {
            color: #00b894;
            font-weight: 600;
            margin-top: 5px;
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
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 184, 148, 0.3);
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            color: #636e72;
            font-size: 14px;
            border-top: 1px solid #eee;
        }
        
        .success-message {
            background: #d4edda;
            color: #155724;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            margin-top: 20px;
            display: none;
        }
        
        @media (max-width: 480px) {
            .container {
                margin: 10px;
            }
            
            .packages {
                grid-template-columns: 1fr;
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
            <form id="chargeForm">
                <div class="form-group">
                    <label for="playerId">🎯 رقم اللاعب (Player ID)</label>
                    <input type="text" id="playerId" placeholder="أدخل رقم اللاعب" required>
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
                    </select>
                </div>
                
                <button type="submit" class="btn">⚡ شحن الآن</button>
            </form>
            
            <div class="success-message" id="successMessage">
                ✅ تم استلام طلبك بنجاح! سيتم الشحن خلال 5 دقائق
            </div>
        </div>
        
        <div class="footer">
            ⏰ خدمة عملاء 24/7 | 🛡️ ضمان استعادة الاموال
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
                alert('⚠️ يرجى ملء جميع الحقول');
                return;
            }
            
            // إظهار رسالة النجاح
            document.getElementById('successMessage').style.display = 'block';
            
            // إرسال البيانات إلى الخادم (يمكنك إضافة هذا لاحقاً)
            fetch('/process-payment', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    playerId: playerId,
                    package: package,
                    payment: payment,
                    userId: '{{user_id}}'
                })
            });
            
            // إعادة تعيين النموذج بعد 3 ثوان
            setTimeout(() => {
                this.reset();
                document.querySelectorAll('.package').forEach(p => p.classList.remove('selected'));
                document.getElementById('successMessage').style.display = 'none';
            }, 3000);
        });
    </script>
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
        return "❌ رابط غير صحيح أو منتهي الصلاحية"

@app.route('/process-payment', methods=['POST'])
def process_payment():
    """معالجة الدفع (يمكن تطويره لاحقاً)"""
    data = request.json
    print(f"📦 طلب شحن جديد: {data}")
    return {"status": "success", "message": "تم استلام الطلب"}

def run_web_server():
    """تشغيل خادم الويب"""
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

# وظائف البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        [InlineKeyboardButton("🌐 صفحتي الشخصية", url=user_link)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_html(
        f"مرحباً {user.mention_html()}! 👋\n\n"
        f"🎮 <b>بوت شحن شدات ببجي</b>\n\n"
        f"🌐 <b>رابطك الشخصي:</b>\n<code>{user_link}</code>\n\n"
        f"✅ يمكنك استخدام الرابط أعلاه في أي متصفح\n"
        f"📱 متوافق مع جميع الأجهزة\n"
        f"🛡️ آمن ومشفّر",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_id = str(user.id)
    user_link = f"{BASE_URL}/charge/{user_id}"
    
    if query.data == "charge":
        keyboard = [
            [InlineKeyboardButton("🌐 فتح صفحتي", url=user_link)],
            [InlineKeyboardButton("🔄 إنشاء رابط جديد", callback_data="new_link")],
            [InlineKeyboardButton("📞 الدعم الفني", url="https://t.me/your_support")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🎮 <b>شحن شدات ببجي</b>\n\n"
            f"🌐 <b>رابطك الشخصي:</b>\n<code>{user_link}</code>\n\n"
            f"📋 <b>طريقة الاستخدام:</b>\n"
            f"1. اضغط على 'فتح صفحتي'\n"
            f"2. املأ البيانات المطلوبة\n"
            f"3. اختر الباقة والدفع\n"
            f"4. تأكيد الطلب\n\n"
            f"⚡ الشحن خلال 5 دقائق",
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
            f"🌐 <b>رابطك الجديد:</b>\n<code>{new_link}</code>",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

def main():
    # تشغيل خادم الويب في thread منفصل
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()
    
    # تشغيل البوت
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("🚀 البوت وخادم الويب يعملان الآن...")
    application.run_polling()

if __name__ == "__main__":
    main()