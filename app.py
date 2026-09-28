import streamlit as st
import os
from google import genai

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
st.markdown("""
    <style>
    .stApp {
        background-color: #f0f8f0;
    }
    </style>
""", unsafe_allow_html=True)
# Business context - General Store ki jaankari
business_info = """
Tum "Sharma General Store" ke liye customer support chatbot ho.
Store ki details:
- Timing: Subah 8 baje se raat 10 baje tak, saare din khula
- Location: Main Market, Mohali
- Available items: Grocery, snacks, cold drinks, daily use products, stationery
- Home delivery available hai 2km ke andar, minimum order ₹200
- Payment: Cash, UPI dono accept hote hain

Sirf store se related sawalon ka jawab do (timing, items, delivery, payment).
Agar koi doosra topic poochhe, politely bolo ki tum sirf store ki jaankari de sakte ho.
Hamesha Hindi mein friendly tareeke se short jawab do.
"""

st.title("Apna General Store 🛒")

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
    
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=business_info + "\n\nCustomer ka sawaal: " + user_input
    )
    
    st.session_state.messages.append({"role": "assistant", "content": response.text})
    with st.chat_message("assistant"):
        st.write(response.text)
