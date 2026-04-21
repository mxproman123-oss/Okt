import telebot
from telebot import types
import requests
from flask import Flask
import threading

# --- [ CONFIG ] ---
API_TOKEN = 'BOT_TOKEN'
ADMIN_ID = 8700421304  # 
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# ተጠቃሚዎችን ለመመዝገብ (ለ Broadcast እንዲመች)
all_users = set()
user_langs = {}

LANGUAGES = {
    "Amharic 🇪🇹": "am",
    "English 🇺🇸": "en",
    "Arabic 🇸🇦": "ar",
    "Hindi 🇮🇳": "hi",
    "Chinese 🇨🇳": "zh-CN",
    "French 🇫🇷": "fr",
    "Spanish 🇪🇸": "es",
    "German 🇩🇪": "de",
    "Russian 🇷🇺": "ru",
    "Turkish 🇹🇷": "tr"
}

# --- [ HEALTH CHECK FOR DOCKER ] ---
@app.route('/')
def health_check():
    return "Bot is running!", 200

def omni_translate(text, target_lang):
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx", "sl": "auto", "tl": target_lang, "dt": "t", "q": text
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            result = response.json()
            return "".join([s[0] for s in result[0]])
        return "❌ Engine Error."
    except: return "❌ Timeout."

def get_lang_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(text=name, callback_data=f"setlang_{code}") 
               for name, code in LANGUAGES.items()]
    markup.add(*buttons)
    return markup

# --- [ ADMIN BROADCAST HANDLER ] ---
@bot.message_handler(commands=['bc'])
def broadcast(message):
    if message.chat.id == ADMIN_ID:
        if message.reply_to_message:
            success, failed = 0, 0
            for user in list(all_users):
                try:
                    bot.copy_message(user, message.chat.id, message.reply_to_message.message_id)
                    success += 1
                except: failed += 1
            bot.reply_to(message, f"📢 Broadcast:\n✅ Success: {success}\n❌ Failed: {failed}")
        else:
            bot.reply_to(message, "⚠️ Please reply to a text or photo with /bc")

# --- [ MAIN HANDLERS ] ---
@bot.message_handler(commands=['start', 'setting'])
def start_cmd(message):
    all_users.add(message.chat.id) # ተጠቃሚውን መመዝገብ
    text = "🌐 MX Ultimate Pro\n\nPlease select the language you would like me to translate your messages into:"
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=get_lang_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("setlang_"))
def callback_set_lang(call):
    lang_code = call.data.split("_")[1]
    user_langs[call.message.chat.id] = lang_code
    lang_name = next(name for name, code in LANGUAGES.items() if code == lang_code)
    
    bot.answer_callback_query(call.id, f"language into {lang_name} changed !")
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"✅ your language selected \n\nnow your text translates into {lang_name} \n\nif u want change language /setting ✌️",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: True)
def handle_translation(message):
    chat_id = message.chat.id
    all_users.add(chat_id)
    
    if chat_id not in user_langs:
        bot.reply_to(message, "⚠️ please first choice your language /start ")
        return

    bot.send_chat_action(chat_id, 'typing')
    target = user_langs[chat_id]
    translated = omni_translate(message.text, target)
    bot.reply_to(message, f"📝 **Translated:**\n\n```@Officialcoders\n{translated}```", parse_mode="Markdown")

if __name__ == "__main__":
    # Flask ለ Docker Health Check በ Thread ይነሳል
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=7860)).start()
    print("💀 Ultimate Pro Translator is Active...")
    bot.infinity_polling()
