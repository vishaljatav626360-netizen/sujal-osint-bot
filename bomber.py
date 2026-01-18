# bomber.py
import requests

# ----------------------- HANDLE BOMBER BUTTON -----------------------
def handle_bomber(bot, call, user_state):
    """
    Jab user BOMBER button dabata hai.
    Ye function user se number maangta hai aur state set karta hai.
    """
    bot.send_message(call.message.chat.id, "📞 Enter the number you want to bomb:")
    user_state[call.from_user.id] = "bomber_input"


# ----------------------- HANDLE USER INPUT FOR BOMBING -----------------------
def handle_bomber_input(msg, bot, user_state):
    """
    User jab number bhejta hai → API call hota hai → bombing start.
    """
    user_id = msg.from_user.id
    number = msg.text.strip()

    # API URL
    url = f"https://mix-rootx-new.vercel.app/bomb?number={requests.utils.quote(number)}"

    # Pehle reply: Bombing start
    bot.send_message(msg.chat.id, f"🔥 Bombing started on **{number}**\n⚡ Please wait...")

    try:
        response = requests.get(url, timeout=1000)
    except Exception as e:
        bot.send_message(msg.chat.id, f"❌ time out 1000 sec")
        user_state.pop(user_id, None)
        return

    # API generally {"status": true, "msg": "..."} deta hai
    try:
        data = response.json()
        status_msg = data.get("msg") or data.get("message") or "Bombing request sent!"
    except:
        status_msg = "Bombing triggered successfully!"

    bot.send_message(
        msg.chat.id,
        f"✅ **Success!**\n{status_msg}\n\n💣 Bombing is now running...",
        parse_mode="Markdown"
    )

    user_state.pop(user_id, None)


