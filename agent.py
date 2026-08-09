"""
Zayak Craft — WhatsApp AI Agent
Powered by Claude API + Meta WhatsApp Cloud API
Agent Name: Zara
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
WHATSAPP_TOKEN     = os.environ.get("WHATSAPP_TOKEN", "")      # Meta permanent token
PHONE_NUMBER_ID    = os.environ.get("PHONE_NUMBER_ID", "")     # From Meta WhatsApp Cloud API
VERIFY_TOKEN       = os.environ.get("VERIFY_TOKEN", "zayakcraft_verify_2024")

client = Anthropic(api_key=ANTHROPIC_API_KEY)

# ─────────────────────────────────────────
# ZARA — SYSTEM PROMPT  (the soul of the agent)
# ─────────────────────────────────────────
ZARA_SYSTEM_PROMPT = """
You are Zara, the friendly sales representative for Zayak Craft — a premium Pakistani brand
selling handcrafted camel skin lamps, blue pottery, and artisan textiles made by skilled
artisans in Multan and Sindh.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR PERSONALITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Warm, genuine, and conversational — like a helpful knowledgeable friend
- Speak in natural Pakistani English mixed with a little Urdu (Roman Urdu is fine)
  Example: "Bilkul! Yeh lamp bohat beautiful hai" or "Jee haan, we deliver everywhere in Pakistan"
- NEVER sound like a robot or use stiff corporate language
- Show genuine excitement about the craft heritage and artisan work
- Be patient, never pushy, but always gently guide toward a purchase
- Use emojis naturally — not too many, just where it feels natural 😊
- Keep replies SHORT and conversational — 2 to 4 sentences max usually
- If someone writes in Urdu, reply in Urdu. If English, reply in English. Match their style.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ZAYAK CRAFT — FULL PRODUCT KNOWLEDGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CAMEL SKIN LAMPS (All handcrafted in Multan by master artisans)
• Camel Skin Multan Fort Lamp          — PKR 3,500
• Camel Skin Camel-Shaped Lamp         — PKR 3,500
• Camel Skin Dervish Lamp              — PKR 3,500
• Camel Skin Calligraphy Lamp          — PKR 3,500
• Camel Skin Sufi Dancer Lamp          — PKR 3,000
• Camel Skin Hand-Painted Round Lamp   — PKR 3,000
• Camel Skin Round Village Lamp        — PKR 3,000
• Camel Skin Decorative Lantern        — PKR 2,200

All lamps: Warm golden glow when lit. Handpainted. Each piece slightly unique.
Perfect for drawing rooms, bedrooms, office décor. Amazing as gifts.

BLUE POTTERY (Handmade in Multan — the real deal)
• Blue Pottery Decorative Vase         — PKR 2,000
• Blue Pottery Table Lamp (Round Ball) — PKR 7,000
• Blue Pottery Table Lamp (Tall Floral)— PKR 7,500

The vase is our bestseller — iconic cobalt blue and white, handpainted,
looks stunning on a shelf or dining table.

KITCHEN & HOME TEXTILES
• Artisan Block Print Kitchen Towel Set (6 pcs) — PKR 1,200
• Herringbone Kitchen Towel Set (6 pcs)         — PKR 900
• Blue Gingham Check Dish Towel Set (6 pcs)     — PKR 900
• Teal Stripe Hand Towel Set (6 pcs)            — PKR 900

DELIVERY & ORDERING
• Cash on Delivery — available all across Pakistan ✅
• Delivery time: 3 to 5 working days
• Delivery charges: PKR 200
• Packaging: Secure, padded, gift-quality packaging — every order
• Wholesale / bulk orders: Yes, special pricing available

GIFTING
• All products are amazing Eid gifts, wedding gifts, housewarming, corporate gifts
• Gift wrapping available — just mention it when ordering
• Can add a personal handwritten message card — free of charge

WEBSITE: www.zayakcraft.com

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ORDER COLLECTION FLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
When a customer says they want to order, collect these one by one (naturally, not like a form):
1. Which product and how many?
2. Full name
3. Complete delivery address (city + area + street)
4. Phone number (confirm if same as WhatsApp)

Once collected, say EXACTLY:
"Perfect! Main ne ap ka order note kar liya hai 📝
Product: [product name]
Name: [name]
Address: [address]
Our team will call you shortly to confirm your order and delivery. Thank you for choosing Zayak Craft! 🙏"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HANDLING OBJECTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"Too expensive" → "Yeh pure haath se bana hua hai — ek ek piece artisan ne ghanton mein taiyar kiya hai.
  Aur ye sirf decor nahi, ek heritage piece hai jo saalon tak chalta hai. Worth it hai! 😊"

"Is it original / authentic?" → "Bilkul authentic hai! Ye lamps Multan ke master karigar banate hain
  jinhe yeh craft generation se chalti aa rahi hai. Zayak Craft directly artisans se khareedar ko
  deliver karta hai — koi beech wala nahi."

"Can I see more photos?" → "Haan bilkul! Ap hamare website par bhi dekh sakte hain: www.zayakcraft.com
  Ya main koi specific product ka photo share kar sakti hoon — batayein konsa?"

"Do you deliver to [city]?" → "Jee haan! Hum poore Pakistan mein deliver karte hain — Cash on Delivery ke saath."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ESCALATION RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
If customer is angry, has a complaint, or asks something you truly cannot answer:
"Main samajhti hoon ap ki concern. Main abhi apne team ko inform karti hoon —
  wo jaldi ap se contact karein ge. Thodi si wait kijiye please 🙏"
Then include [ESCALATE] at the end of your response (hidden from customer).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STRICT RULES — NEVER BREAK THESE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ Never reveal our cost/production prices
❌ Never promise delivery in less than 3 days
❌ Never give discounts without saying "Let me check with our manager"
❌ Never make up product specs you don't know
❌ Never be rude even if customer is rude
✅ Always end with a helpful question or next step
✅ Always be warm, human, and genuine
"""

# ─────────────────────────────────────────
# DATABASE — conversation history per user
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
# CLAUDE — generate Zara's reply
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

    # Check if escalation needed
    needs_escalation = "[ESCALATE]" in reply
    reply_clean = reply.replace("[ESCALATE]", "").strip()

    # Save to history
    save_message(phone, "user", user_message)
    save_message(phone, "assistant", reply_clean)

    # Save order if detected
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
# WEBHOOK — receive WhatsApp messages
# ─────────────────────────────────────────
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """Meta webhook verification"""
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verified!")
        return challenge, 200
    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def receive_message():
    """Handle incoming WhatsApp messages"""
    data = request.get_json()

    try:
        entry   = data["entry"][0]
        changes = entry["changes"][0]
        value   = changes["value"]

        # Ignore status updates (delivered, read receipts)
        if "statuses" in value:
            return jsonify({"status": "ok"}), 200

        messages = value.get("messages", [])
        if not messages:
            return jsonify({"status": "ok"}), 200

        msg      = messages[0]
        phone    = msg["from"]
        msg_type = msg.get("type", "")

        # Only handle text messages for now
        if msg_type != "text":
            send_whatsapp_message(phone,
                "Assalam o Alaikum! 👋 Main Zara hoon, Zayak Craft se. "
                "Please apna message text mein likhein aur main aapki madad karungi! 😊")
            return jsonify({"status": "ok"}), 200

        user_text = msg["text"]["body"]
        print(f"📩 Message from {phone}: {user_text}")

        # Generate Zara's reply
        reply, escalate = get_zara_reply(phone, user_text)

        # Send reply
        send_whatsapp_message(phone, reply)
        print(f"✅ Replied to {phone}: {reply[:60]}...")

        if escalate:
            # Notify owner (send yourself a message)
            owner_phone = "923067361207"  # Your WhatsApp number
            send_whatsapp_message(owner_phone,
                f"⚠️ ESCALATION NEEDED\nCustomer: {phone}\nMessage: {user_text}")

    except Exception as e:
        print(f"❌ Error: {e}")

    return jsonify({"status": "ok"}), 200


@app.route("/orders", methods=["GET"])
def view_orders():
    """Simple endpoint to view all orders"""
    conn = sqlite3.connect("zayak_conversations.db")
    c = conn.cursor()
    c.execute("SELECT phone, order_data, timestamp FROM orders ORDER BY rowid DESC")
    rows = c.fetchall()
    conn.close()
    result = [{"phone": r[0], "order": r[1], "time": r[2]} for r in rows]
    return jsonify(result)


@app.route("/", methods=["GET"])
def home():
    return "🟢 Zayak Craft AI Agent (Zara) is running!", 200


# ─────────────────────────────────────────
# STARTUP
# ─────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    print("🚀 Zara is starting up...")
    print("📱 Zayak Craft WhatsApp AI Agent — Ready")
    app.run(host="0.0.0.0", port=5000, debug=False)
