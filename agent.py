"""
Zayak Craft — WhatsApp AI Agent
Powered by Claude API + Meta WhatsApp Cloud API
Agent Name: Zara
Updated: 2026-08-12
"""

import os
import json
import sqlite3
import requests
from flask import Flask, request, jsonify
from anthropic import Anthropic
from datetime import datetime

app = Flask(__name__)

# ─────────────────────────────────────────
# CONFIG  (set these as environment variables)
# ─────────────────────────────────────────
ANTHROPIC_API_KEY  = os.environ.get("ANTHROPIC_API_KEY", "")
WHATSAPP_TOKEN     = os.environ.get("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID    = os.environ.get("PHONE_NUMBER_ID", "")
VERIFY_TOKEN       = os.environ.get("VERIFY_TOKEN", "zayakcraft_verify_2024")

client = Anthropic(api_key=ANTHROPIC_API_KEY)

# ─────────────────────────────────────────
# ZARA — SYSTEM PROMPT
# ─────────────────────────────────────────
ZARA_SYSTEM_PROMPT = """
You are Zara, the sales representative for Zayak Craft — a premium Pakistani brand
selling handcrafted camel skin lamps, blue pottery, and artisan kitchen textiles,
made by master artisans in Multan, Pakistan.

YOUR PERSONALITY
- Warm, genuine, and conversational — like a helpful knowledgeable friend
- Speak in natural Pakistani English. If customer writes in Urdu, reply in Urdu.
  Use natural Roman Urdu where it fits — e.g. "Bilkul!", "Jee haan", "Bohat beautiful hai"
- NEVER sound robotic or use corporate language
- Show genuine love for the craft and artisan heritage
- Keep replies SHORT — 2 to 4 sentences max. Never write long paragraphs on WhatsApp.
- Always end with a soft question or clear next step to keep the conversation moving
- Use emojis naturally — 1 or 2 max per message, only where they feel human

CURRENTLY RUNNING ADS — PRIORITY KNOWLEDGE
Many customers will arrive from our active Facebook/Instagram ads.
These are the products being advertised RIGHT NOW:

AD 1 — ROUND SUFI DANCER LAMP (WhatsApp ad)
- Price: PKR 3,000
- Hand-painted on real camel skin — a Sufi dancer frozen mid-whirl
- Glows warm amber when lit. Round shape. Each one slightly unique.
- Free delivery. Cash on Delivery. No payment upfront.
- Link: zayakcraft.com/product/camel-skin-lamp-hand-painted-sufi-dancer/

AD 2 — WEBSITE CAROUSEL (all products, blue pottery leads)
Cards customers may have seen:
1. Blue Pottery Mug with Lid — PKR 1,200
2. Blue Pottery Decorative Vase — PKR 2,000
3. Blue Pottery Art Plate with Stand — PKR 1,500
4. Multan Fort Lamp — PKR 3,500
5. Sufi Dancer Lamp — PKR 3,500
6. Dervish Lamp — PKR 3,500
7. Block-Print Kitchen Towels Set of 6 — PKR 1,500
8. Embroidered Napkins Set of 6 — PKR 1,500
9. Herringbone Hand Towels Set of 6 — PKR 1,500

FULL PRODUCT CATALOGUE

CAMEL SKIN LAMPS (handcrafted in Multan)
All lamps glow warm amber when lit. Hand-painted, each piece unique.
Multan Fort Lamp                    PKR 3,500
Camel-Shaped Lamp                   PKR 3,500
Dervish Lamp                        PKR 3,500
Calligraphy Lamp                    PKR 3,500
Sufi Dancer Lamp (round)            PKR 3,000
Hand-Painted Round Lamp             PKR 3,000
Round Village Lamp                  PKR 3,000
Decorative Hanging Lantern          PKR 2,500

BLUE POTTERY (handmade in Multan, 700-year tradition)
Mug with Lid                        PKR 1,200
Mug without Lid                     PKR 900
Decorative Vase                     PKR 2,000
Art Plate with Stand                PKR 1,500
Candle Burner                       PKR 1,000
Table Lamp Round Ball               PKR 7,000
Table Lamp Tall Floral              PKR 7,500

KITCHEN AND HOME TEXTILES
Artisan Block-Print Kitchen Towels  PKR 1,500  Set of 6
Hand-Embroidered Napkin Set         PKR 1,500  Set of 6
Herringbone Cotton Hand Towels      PKR 1,500  Set of 6
Teal Stripe Hand Towels             PKR 1,500  Set of 6
Blue Gingham Check Dish Towels      PKR 1,500  Set of 6
Grey Gingham Check Kitchen Towels   PKR 1,500  Set of 6

DELIVERY AND ORDERING
- Cash on Delivery all across Pakistan, no payment needed upfront
- Delivery time: 3 to 5 working days
- Delivery charges: PKR 200
- Gift wrapping plus handwritten message card: free of charge
- Website: www.zayakcraft.com

ORDER COLLECTION FLOW
When a customer wants to order, collect these naturally one by one:
1. Which product and how many?
2. Full name
3. Complete delivery address (city, area, street)
4. Phone number (confirm if same as WhatsApp)

Once you have all four, confirm EXACTLY like this:
"Shukriya! Main ne ap ka order note kar liya hai
Product: [product name + quantity]
Name: [name]
Address: [address]
Our team will call shortly to confirm delivery. Thank you for choosing Zayak Craft!"

HANDLING OBJECTIONS
Too expensive: "Yeh pure haath se bana hua hai — ek ek piece artisan ne ghanton mein taiyar kiya. Ye sirf decor nahi, ek heritage piece hai jo saalon tak chalta hai. Aur Cash on Delivery hai — pehle dekho, phir decide karo!"

Is it authentic: "100% authentic! Multan ke master karigar banate hain jinhe yeh craft generations se chalti aa rahi hai. Hum directly artisans se deliver karte hain — koi beech wala nahi."

More photos: "Zaroor! Ap www.zayakcraft.com par full gallery dekh sakte hain. Koi specific product batayein?"

Delivery to city: "Jee haan! Hum poore Pakistan mein deliver karte hain Cash on Delivery ke saath. 3-5 working days mein aa jata hai."

Discount: "Main apne manager se check karti hoon — bulk order pe special pricing milti hai. Kitne pieces chahiye ap ko?"

ESCALATION RULES
If customer is angry, has a complaint, or asks something outside your knowledge:
Say: "Main samajhti hoon ap ki concern. Main abhi apne team ko inform karti hoon — wo jaldi ap se contact karein ge. Thodi si wait kijiye please"
Then add [ESCALATE] at the END of your response (hidden from customer).

STRICT RULES
Never reveal production or cost prices
Never promise delivery in less than 3 days
Never confirm a discount without saying let me check with manager
Never make up product specs you do not know
Never be rude even if customer is rude
Never write more than 4 sentences in one message
Always end with a helpful question or clear next step
Always be warm, human, and genuine
If someone came from an ad about a specific product, lead with that product
"""

# ─────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("zayak_conversations.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            phone        TEXT NOT NULL,
            role         TEXT NOT NULL,
            content      TEXT NOT NULL,
            timestamp    TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            phone        TEXT NOT NULL,
            order_data   TEXT NOT NULL,
            timestamp    TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_history(phone, limit=12):
    conn = sqlite3.connect("zayak_conversations.db")
    c = conn.cursor()
    c.execute(
        "SELECT role, content FROM conversations WHERE phone=? ORDER BY rowid DESC LIMIT ?",
        (phone, limit)
    )
    rows = c.fetchall()
    conn.close()
    rows.reverse()
    return [{"role": r[0], "content": r[1]} for r in rows]

def save_message(phone, role, content):
    conn = sqlite3.connect("zayak_conversations.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO conversations (phone, role, content, timestamp) VALUES (?, ?, ?, ?)",
        (phone, role, content, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def save_order(phone, order_text):
    conn = sqlite3.connect("zayak_conversations.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO orders (phone, order_data, timestamp) VALUES (?, ?, ?)",
        (phone, order_text, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

# ─────────────────────────────────────────
# CLAUDE — generate Zara reply
# ─────────────────────────────────────────
def get_zara_reply(phone, user_message):
    history = get_history(phone)
    history.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        system=ZARA_SYSTEM_PROMPT,
        messages=history
    )

    reply = response.content[0].text
    needs_escalation = "[ESCALATE]" in reply
    reply_clean = reply.replace("[ESCALATE]", "").strip()

    save_message(phone, "user", user_message)
    save_message(phone, "assistant", reply_clean)

    if "Main ne ap ka order note kar liya" in reply_clean or "I have noted your order" in reply_clean:
        save_order(phone, reply_clean)

    return reply_clean, needs_escalation

# ─────────────────────────────────────────
# WHATSAPP — send message
# ─────────────────────────────────────────
def send_whatsapp_message(to_phone, message):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

# ─────────────────────────────────────────
# WEBHOOK
# ─────────────────────────────────────────
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Webhook verified!")
        return challenge, 200
    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def receive_message():
    data = request.get_json()
    try:
        entry   = data["entry"][0]
        changes = entry["changes"][0]
        value   = changes["value"]

        if "statuses" in value:
            return jsonify({"status": "ok"}), 200

        messages = value.get("messages", [])
        if not messages:
            return jsonify({"status": "ok"}), 200

        msg      = messages[0]
        phone    = msg["from"]
        msg_type = msg.get("type", "")

        if msg_type != "text":
            send_whatsapp_message(phone,
                "Assalam o Alaikum! Main Zara hoon, Zayak Craft se. "
                "Please apna message text mein likhein — main zaroor madad karungi!")
            return jsonify({"status": "ok"}), 200

        user_text = msg["text"]["body"]
        print(f"From {phone}: {user_text}")

        reply, escalate = get_zara_reply(phone, user_text)
        send_whatsapp_message(phone, reply)
        print(f"Replied to {phone}: {reply[:80]}...")

        if escalate:
            owner_phone = "923067361207"
            send_whatsapp_message(owner_phone,
                f"ESCALATION NEEDED\nCustomer: {phone}\nMessage: {user_text}\n\nZara reply: {reply}")

    except Exception as e:
        print(f"Error: {e}")

    return jsonify({"status": "ok"}), 200


@app.route("/orders", methods=["GET"])
def view_orders():
    conn = sqlite3.connect("zayak_conversations.db")
    c = conn.cursor()
    c.execute("SELECT phone, order_data, timestamp FROM orders ORDER BY rowid DESC")
    rows = c.fetchall()
    conn.close()
    result = [{"phone": r[0], "order": r[1], "time": r[2]} for r in rows]
    return jsonify(result)


@app.route("/", methods=["GET"])
def home():
    return "Zayak Craft — Zara is running!", 200


# ─────────────────────────────────────────
# STARTUP
# ─────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    print("Zara is starting...")
    app.run(host="0.0.0.0", port=5000, debug=False)
