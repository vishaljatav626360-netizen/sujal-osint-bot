import requests

def handle_ip(bot, call, user_state):
    bot.send_message(call.message.chat.id, "🌐 Send the IP address to lookup (or leave empty for your IP):")
    user_state[call.from_user.id] = "ip_input"

def handle_input(bot, msg, user_state):
    user_id = msg.from_user.id
    ip = msg.text.strip()

    # Agar IP khali hai toh API server ki IP dikhayegi
    # ipinfo.io use kar rahe hain hum yahan
    url = f"https://ipinfo.io/{ip}/json"

    try:
        # Note: Ipinfo free mein 50k requests per month deta hai bina token ke
        response = requests.get(url, timeout=10).json()
    except Exception as e:
        bot.send_message(msg.chat.id, f"❌ API Error: {e}")
        user_state.pop(user_id, None)
        return

    # ipinfo.io mein status ki jagah error field hoti hai agar fail ho
    if "error" in response:
        bot.send_message(msg.chat.id, "⚠️ Invalid IP address or API limit reached.")
        user_state.pop(user_id, None)
        return

    # Lat/Lon ko alag karne ke liye (kyunki ipinfo "loc": "12.34,56.78" deta hai)
    loc = response.get('loc', '-').split(',')
    lat = loc[0] if len(loc) > 0 else '-'
    lon = loc[1] if len(loc) > 1 else '-'

    # Build clean output
    lines = [
        f"🌐 IP: {response.get('ip', '-')}",
        f"🏳️ Country: {response.get('country', '-')}",
        f"🏷️ Region: {response.get('region', '-')}",
        f"🏙️ City: {response.get('city', '-')}",
        f"🏤 ZIP: {response.get('postal', '-')}",
        f"📍 Location: {lat}, {lon}",
        f"⏱️ Timezone: {response.get('timezone', '-')}",
        f"📡 ISP/Org: {response.get('org', '-')}",
        f"🏢 Hostname: {response.get('hostname', '-')}"
    ]

    final_msg = "🔎 IP Lookup Result (via ipinfo.io)\n\n" + "\n".join(lines)
    bot.send_message(msg.chat.id, final_msg)
    user_state.pop(user_id, None)
