import streamlit as st
import os
import pandas as pd
from google import genai

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Yaha apna copy kiya hua Google Sheet ka link daalo (quotes ke andar)
SHEET_LINK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSL8wvNZs6lNwSLRDsiq0eEHbFeGGRau_Un1TlAD2VD-HimiaMfRQdV5b8PH9XzQShkIi2qdxEexLQu/pub?gid=0&single=true&output=csv"

st.markdown("""
    <style>
    .stApp {
        background-color: #1a1a2e;
    }
    .stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp span {
        color: #ffffff !important;
    }
    [data-testid="stChatInput"] textarea {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: #666666 !important;
        -webkit-text-fill-color: #666666 !important;
    }
    </style>
""", unsafe_allow_html=True)


# Sheet se data padho (har 60 second mein naya data aayega)
@st.cache_data(ttl=60)
def load_items():
    try:
        df = pd.read_csv(SHEET_LINK)
        lines = []
        for _, row in df.iterrows():
            if int(row["stock"]) == 0:
                lines.append(f"- {row['item']}: Rs {row['rate']} (STOCK KHATAM, available nahi hai)")
            else:
                lines.append(f"- {row['item']}: Rs {row['rate']} (stock: {row['stock']})")
        return "\n".join(lines)
    except Exception:
        return "Items ki list abhi load nahi ho payi."


items_list = load_items()

business_info = f"""
Tum "Sharma General Store" ke liye customer support chatbot ho.
Store ki details:
- Timing: Subah 8 baje se raat 10 baje tak, saare din khula
- Location: Main Market, Mohali
- Home delivery available hai 2km ke andar, minimum order Rs 200
- Payment: Cash, UPI dono accept hote hain

Items, rate aur stock ki latest list:
{items_list}

Rules:
- Sirf is list ke items aur rate batao, apni taraf se rate ya item mat banao.
- Jis item ka stock khatam hai, customer ko batao ki abhi available nahi hai.
- Jo item list mein nahi hai, bolo ki uski jaankari abhi nahi hai, dukaan pe pooch lein.
- Sirf store se related sawalon ka jawab do, doosre topic pe politely mana karo.
- Hamesha Hindi mein friendly tareeke se short jawab do.
"""

st.title("Sharma General Store 🛒")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

user_input = st.chat_input("Apna sawaal yaha likho...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=business_info + "\n\nCustomer ka sawaal: " + user_input
        )
        answer = response.text
    except Exception:
        answer = "Abhi thodi technical dikkat hai, kripya thodi der baad try karein."

    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.write(answer)
