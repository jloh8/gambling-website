import streamlit as st
import json
import re
from google import genai
from google.genai import types

# --- 1. CONFIGURATION ---
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

st.set_page_config(page_title="NBA Pulse", layout="wide")

# CSS for the exact 102.67 x 20 compact entry size
st.markdown("""
<style>
    /* Mimic the container from the screenshot */
    .stButton>button {
        width: 103px !important;
        height: 20px !important;
        min-height: 20px !important;
        padding: 0px 4px !important;
        font-family: "Finviz Sans", "Inter Fallback", sans-serif !important;
        font-size: 12px !important;
        line-height: 20px !important;
        background-color: transparent !important;
        color: #448aff !important; /* The specific blue from the image */
        border: none !important;
        text-align: left !important;
        display: flex !important;
        justify-content: space-between !important;
        margin-bottom: 2px !important;
    }
    
    .stButton>button:hover {
        background-color: #1e222d !important;
        color: #ffffff !important;
    }

    /* Variance Labels (Green/Red blocks) */
    .trend-pill {
        font-weight: bold;
        font-size: 11px;
        padding: 0 4px;
        border-radius: 2px;
        line-height: 16px;
        display: inline-block;
        margin-left: 5px;
    }
    .pill-up { color: #26a69a; }
    .pill-down { color: #ef5350; }
    
    /* Highlighted block style for specific movers */
    .pill-block-up { background-color: #26a69a; color: white !important; }
    .pill-block-down { background-color: #ef5350; color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. ENGINE (Refreshed for Feb 4, 2026) ---
@st.cache_data(ttl=1800)
def get_scoring_data():
    prompt = (
        "Identify 8 healthy NBA players scoring significantly ABOVE their season average in the last 2 games "
        "and 8 healthy players scoring significantly BELOW. Exclude injuries/DNPs. "
        "Context: Feb 4, 2026. Include Cooper Flagg (up ~+90% after 49pt game), Jaden Ivey (new role in Chicago), "
        "and Alperen Sengun. "
        "Return ONLY a JSON list: "
        '[{"p": "NAME", "v": "+45%", "s": "UP", "desc": "Short summary"}]'
    )
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.0
            )
        )
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        return json.loads(match.group(0)) if match else None
    except:
        return None

# --- 3. STATE & DETAIL VIEW ---
if "sel" not in st.session_state:
    st.session_state.sel = None

if st.session_state.sel:
    s = st.session_state.sel
    st.button("← Back")
    st.subheader(f"{s['p']} Spotlight")
    st.metric("Scoring Variance", s['v'])
    st.info(s['desc'])
    if st.button("Close"):
        st.session_state.sel = None
        st.rerun()
    st.stop()

# --- 4. MAIN CRAMPED DISPLAY ---
st.caption("⚡ NBA SCORING VARIANCE (COMPACT)")

trends = get_scoring_data()

if trends:
    # 4 columns for a dense grid layout
    cols = st.columns(4)
    for i, item in enumerate(trends):
        with cols[i % 4]:
            # Formatted label for the button: Name (Space) Variance
            # Slicing Name to 5 chars to ensure fit in 103px
            label = f"{item['p'][:5]} {item['v']}"
            
            if st.button(label, key=f"btn_{i}"):
                st.session_state.sel = item
                st.rerun()
else:
    st.warning("Fetching live trends...")