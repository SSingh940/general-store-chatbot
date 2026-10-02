import os
import re
import json
import requests
import streamlit as st
from google import genai
from google.genai import types

# Secrets (Streamlit Cloud ke "Secrets" mein daalenge, code mein nahi)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
ORDERS_URL = os.environ.get("ORDERS_URL")        # Apps Script Web app URL
ITEMS_CSV_URL = os.environ.get("ITEMS_CSV_URL")  # Items sheet ka CSV link (optional)


@st.cache_data(ttl=300)
def get_items():
    """Google Sheet se items ki list laata hai (5 minute tak yaad rakhta hai)."""
    if not ITEMS_CSV_URL:
        return ""
    try:
        r = requests.get(ITEMS_CSV_URL, timeout=10)
        r.raise_for_status()
        return r.text
    except Exception:
        return ""


items_list = get_items()

# Business context - General Store ki jaankari
business_info = f"""
Tum "Sharma General Store" ke liye customer support aur order lene wale chatbot ho.
Store ki details:
- Timing: Subah 8 baje se raat 10 baje tak, saare din khula
- Location: Main Market, Mohali
- Available items: Grocery, snacks, cold drinks, daily use products, stationery
- Home delivery available hai 2km ke andar, minimum order ₹200
- Payment: Cash, UPI dono accept hote hain

Items ki list (price ke saath):
{items_list if items_list else "(list abhi available nahi hai)"}

Sirf store se related sawalon ka jawab do (timing, items, delivery, payment, order).
Agar koi doosra topic poochhe, politely bolo ki tum sirf store ki jaankari de sakte ho.
Hamesha Hindi mein friendly tareeke se short jawab do.

ORDER LENE KE RULES:
1. Customer order dena chahe toh poochho kaun se items aur kitni quantity.
2. Sirf wahi items lo jo list mein hain. Total list ke prices se hi banao, apne se price mat banao.
3. Order ke liye customer ka naam, phone number aur delivery address zaroor poochho.
4. Minimum order ₹200 hai. Isse kam ho toh batao ki aur items jodne padenge.
5. Saari details milne ke baad order ka summary dikhao (items, total, naam, phone, address)
   aur poochho "Confirm karein?".
6. Jab customer saaf taur par confirm kare (jaise "haan", "confirm"), tab dhanyavaad wala
   chhota message likho, aur apne jawab ki bilkul aakhri line mein ye likho:
   ORDER_JSON: {{"name": "...", "phone": "...", "address": "...", "items": "2 Maggi, 1 Parle-G", "total": 38}}
7. Confirm hone se pehle ORDER_JSON wali line kabhi mat likho. Ek order ke liye sirf ek baar likho.
"""


def send_order(order):
    """Order ko Google Sheet ke Orders tab mein bhejta hai."""
    if not ORDERS_URL:
        return False
    try:
        r = requests.post(ORDERS_URL, data=json.dumps(order), timeout=20)
        return r.status_code == 200
    except Exception:
        return False


st.title("Apna General Store 🛒")

# "content" = jo screen par dikhta hai, "raw" = jo bot ko wapas bheja jaata hai
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

user_input = st.chat_input("Apna sawaal ya order yaha likho...")

if user_input:
    st.session_state.messages.append(
        {"role": "user", "content": user_input, "raw": user_input}
    )
    with st.chat_message("user"):
        st.write(user_input)

    # Poori baat-cheet bot ko bhejte hain taaki use sab yaad rahe
    history = [
        types.Content(
            role="user" if m["role"] == "user" else "model",
            parts=[types.Part(text=m["raw"])],
        )
        for m in st.session_state.messages
    ]

    with st.chat_message("assistant"):
        try:
            with st.spinner("Soch raha hoon..."):
                response = client.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=history,
                    config=types.GenerateContentConfig(system_instruction=business_info),
                )
            raw_text = response.text or ""
        except Exception:
            raw_text = "Maaf kijiye, abhi kuch problem aa gayi. Thodi der baad dobara try karein."

        visible_text = raw_text
        match = re.search(r"ORDER_JSON:\s*(\{.*\})", raw_text, re.S)

        if match:
            visible_text = raw_text[: match.start()].strip()
            try:
                order = json.loads(match.group(1))
                if send_order(order):
                    visible_text += "\n\n✅ Aapka order dukaandaar tak pahunch gaya hai!"
                else:
                    visible_text += (
                        "\n\n⚠️ Order bhejne mein dikkat aayi. "
                        "Kripya store par call karke order confirm karein."
                    )
            except Exception:
                visible_text += "\n\n⚠️ Order save nahi ho paya. Kripya dobara try karein."

        st.write(visible_text)

    st.session_state.messages.append(
        {"role": "assistant", "content": visible_text, "raw": raw_text}
    )
