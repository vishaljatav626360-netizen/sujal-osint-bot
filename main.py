import os
import logging
from threading import Thread
import telebot
import requests
import json
import re
from flask import Flask
from telebot.apihelper import ApiTelegramException
import upi
import bomber
import imei

# ----------------------- FORCE SUB FIX -----------------------
FORCE_CHANNEL = -1003223668976   # <-- YOUR PRIVATE CHANNEL CHAT ID

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(FORCE_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


# ----------------------- CONFIG -----------------------
TOKEN = "7868875982:AAGfgaRxkAgepAO-Y1ja-16qOz6sB_GZe7g"
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

app = Flask("render_web")

user_state = {}

BASE_API = "https://api.b77bf911.workers.dev"
ENDPOINTS = {
    'mobile': f'{BASE_API}/mobile?number=',
    'aadhaar': f'{BASE_API}/aadhaar?id=',
    'gst': f'{BASE_API}/gst?number=',
    'ifsc': f'{BASE_API}/ifsc?code=',
    'rashan': f'{BASE_API}/rashan?aadhaar=',
    'vehicle': f'{BASE_API}/vehicle?registration='
}

# ----------------------- CLEAN & PRETTY FORMATTER -----------------------
def clean_text(text):
    if text is None:
        return ""
    text = str(text)
    text = text.replace("!", ", ")
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r",\s*(,|\s)+", ", ", text)
    text = text.strip(" ,\n\t")
    text = text.replace("*", "").replace("_", "").replace("`", "")
    return text

def pretty_address(raw):
    if not raw:
        return ""
    parts = re.split(r"[!|;\/\\\n]+", str(raw))
    parts = [clean_text(p) for p in parts if p.strip()]
    seen = set()
    out = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return ", ".join(out)

def pretty_format(data, indent=2):
    """Recursive pretty format for any JSON structure."""
    if isinstance(data, dict):
        text = ""
        for k, v in data.items():
            if v in [None, "", "N/A"]:
                continue
            key = str(k).replace("_", " ").title()
            text += f"🔹 **{key}:** {pretty_format(v)}\n"
        return text
    elif isinstance(data, list):
        text = ""
        for i, item in enumerate(data, 1):
            text += f"\n------ 🌸 Record 🌸{i} ------\n"
            text += pretty_format(item)
        return text
    else:
        return str(data)

# ----------------------- START COMMAND -----------------------
import mongo  # mongo.py jisme add_user & broadcast_message hai

OWNER_ID = 8535060154  # <-- yaha apna Telegram ID daalo

# ---------- /start & /help ---------- (tumhara original code exactly)
@bot.message_handler(commands=['start', 'help'])
def start(msg):
    user_id = msg.from_user.id

    # SAVE USER IN MONGO
    mongo.add_user(user_id)

    # -------- FORCE SUBSCRIBE CHECK (NO DP) --------
    if not is_subscribed(user_id):
        kb = telebot.types.InlineKeyboardMarkup()
        kb.add(
            telebot.types.InlineKeyboardButton(
                "💥 Join Our Channel 💥",
                url="https://t.me/+2q1EoC5BVyM2MjI1"
            )
        )

        bot.send_message(
            msg.chat.id,
            "🔴 **To use this bot, please join our channel first.**\n\nAfter joining, click /start",
            reply_markup=kb,
            parse_mode="Markdown"
        )
        return   # STOP — force-sub, no DP

    # -------- REST OF ORIGINAL FLOW --------
    photos = bot.get_user_profile_photos(user_id)
    dp_exists = photos.total_count > 0

    caption_text = "**🔍 OSINT Lookup Bot**\nChoose the service:"

    kb = telebot.types.InlineKeyboardMarkup()
    kb.add(
        telebot.types.InlineKeyboardButton("📱 Mobile", callback_data="mobile"),
        telebot.types.InlineKeyboardButton("🆔 Aadhaar", callback_data="aadhaar")
    )
    kb.add(
        telebot.types.InlineKeyboardButton("🧾 GST", callback_data="gst"),
        telebot.types.InlineKeyboardButton("📍 PINCODE", callback_data="pincode")
    )
    kb.add(
        telebot.types.InlineKeyboardButton("🧔🏻 NUM 2 Family", callback_data="family")
    )
    kb.add(
        telebot.types.InlineKeyboardButton("👩🏻 AADHAR 2 Family", callback_data="aadhfamily")
    )

    kb.add(
        telebot.types.InlineKeyboardButton("🏦 IFSC", callback_data="ifsc"),
        telebot.types.InlineKeyboardButton("🍚 Ration", callback_data="rashan")
    )
    kb.add(
        telebot.types.InlineKeyboardButton("🚗 Vehicle", callback_data="vehicle"),
        telebot.types.InlineKeyboardButton("💲 UPI", callback_data="upi")
    )
    kb.add(
        telebot.types.InlineKeyboardButton("💣 BOMBER", callback_data="bomber")
    )
    kb.add(
        telebot.types.InlineKeyboardButton("📱 IMEI", callback_data="imei"),
        telebot.types.InlineKeyboardButton("🌐 IP ADDRESS", callback_data="ip")
    )
    kb.add(
        telebot.types.InlineKeyboardButton("👤 Owner", url="https://t.me/selectionsevabot")
    )

    if dp_exists:
        file_id = photos.photos[0][0].file_id
        bot.send_photo(
            msg.chat.id,
            file_id,
            caption=caption_text,
            reply_markup=kb,
            parse_mode="Markdown"
        )
    else:
        bot.send_message(
            msg.chat.id,
            caption_text,
            reply_markup=kb,
            parse_mode="Markdown"
        )

# ---------- Owner-only broadcast command ----------
# ---------- Owner-only broadcast command ----------
@bot.message_handler(commands=['broadcast'])
def broadcast(msg):
    if msg.from_user.id != OWNER_ID:
        bot.reply_to(msg, "❌ You are not allowed to use this command.")
        return

    try:
        text_to_send = msg.text.split(" ", 1)[1]  # /broadcast <message>
    except IndexError:
        bot.reply_to(msg, "Usage: /broadcast <message>")
        return

    result = mongo.broadcast_message(bot, text_to_send)

    # Clear formatted message
    reply_text = (
        f"✅ **Broadcast Complete!**\n\n"
        f"📌 Total Users: {result['total']}\n"
        f"✅ Sent Successfully: {result['success']}\n"
        f"❌ Failed: {result['failed']}"
    )

    bot.send_message(msg.chat.id, reply_text, parse_mode="Markdown")




# ----------------------- CALLBACK HANDLER -----------------------
@bot.callback_query_handler(func=lambda c: True)
def callback(call):
    user_state[call.from_user.id] = call.data
    prompts = {
        "mobile": "📱 Send Mobile Number:",
        "aadhaar": "🆔 Send Aadhaar ID:",
        "gst": "🧾 Send GST Number:",
        "ifsc": "🏦 Send IFSC Code:",
        "rashan": "🍚 Send Aadhaar Number for Ration Info:",
        "vehicle": "🚗 Send Vehicle Number:"
    }

    if call.data == "family":
        import family
        family.handle_family(bot, call, user_state)

    elif call.data == "aadhfamily":
        import aadhfamily
        aadhfamily.handle_aadhfamily(bot, call, user_state)

    elif call.data == "upi":
        import upi
        upi.handle_upi(bot, call, user_state)

    elif call.data == "bomber":
        import bomber
        bomber.handle_bomber(bot, call, user_state)

    elif call.data == "imei":
        import imei
        imei.handle_imei(bot, call, user_state)

    elif call.data == "ip":
        import ip
        ip.handle_ip(bot, call, user_state)

    elif call.data == "pincode":
        import pincode
        pincode.handle_pincode(bot, call, user_state)

    else:
        bot.send_message(call.message.chat.id, prompts.get(call.data, "Send Input"))


# ----------------------- USER INPUT HANDLER -----------------------
@bot.message_handler(func=lambda m: m.from_user.id in user_state)
def handle_input(msg):
    user_id = msg.from_user.id
    service = user_state[user_id]
    value = msg.text.strip()

    # ------------------ FAMILY ------------------
    if service == "family_input":
        import family
        family.handle_input(bot, msg, user_state)
        return
    
    # ------------------ AADHAR FAMILY ------------------
    if service == "aadhfamily_input":
        import aadhfamily
        aadhfamily.handle_input(bot, msg, user_state)
        return

    # ------------------ UPI ------------------
    if service == "upi_input":
        import upi
        upi.handle_upi_input(msg, bot, user_state)
        return

    # ------------------ BOMBER ------------------
    if service == "bomber_input":
        import bomber
        bomber.handle_bomber_input(msg, bot, user_state)
        return

    # ------------------ IMEI ------------------
    if service == "imei":
        import imei
        imei.handle_input(bot, msg, user_state)
        return

    # ------------------ IP ------------------
    if service == "ip_input":
        import ip
        ip.handle_input(bot, msg, user_state)
        return

    # ------------------ PINCODE ------------------
    if service == "pincode":
        import pincode
        pincode.handle_pincode_input(bot, msg, user_state)
        return

    # ------------------ DEFAULT API HANDLER ------------------
    if service not in ENDPOINTS:
        bot.send_message(msg.chat.id, f"❌ Unknown service: {service}")
        user_state.pop(user_id, None)
        return

    url = ENDPOINTS[service] + requests.utils.quote(value)

    try:
        response = requests.get(url, timeout=10).json()
    except Exception as e:
        bot.send_message(msg.chat.id, f"❌ API Error: {e}")
        user_state.pop(user_id, None)
        return

    data = response.get("data") or response.get("result") or response.get("info") or response
    formatted = pretty_format(data)

    final_msg = f"### 🔍 **{service.upper()} Result**\n\n{formatted}"

    # ------------------ FIX MARKDOWN ERROR ------------------
    def escape_markdown(text: str):
        escape_chars = ['*', '_', '`', '[', ']']
        for ch in escape_chars:
            text = text.replace(ch, f'\\{ch}')
        return text

    safe_msg = escape_markdown(final_msg)

    bot.send_message(msg.chat.id, safe_msg, parse_mode="Markdown")
    user_state.pop(user_id, None)


if __name__ == "__main__":
    logging.info("Bot starting...")

    def run_flask():
        port = int(os.environ.get("PORT", 10000))
        app.run(host="0.0.0.0", port=port)

    # Start Flask in a separate thread
    Thread(target=run_flask, daemon=True).start()

    # Start polling in retry loop
    import time
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print("Polling error:", e)
            time.sleep(5)


