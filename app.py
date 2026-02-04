import streamlit as st
import json
import re
from google import genai
from google.genai import types

# --- 1. CONFIGURATION ---
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

def extract_json_list(text):
    """Finds and extracts a JSON list from AI text."""
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return None

# --- 2. GLOBAL TREND ENGINE ---
@st.cache_data(ttl=1800)
def get_global_trends():
    """Scans the entire NBA for upward/downward trends from Feb 2-4, 2026."""
    prompt = (
        "Analyze the entire NBA for games played on February 2, 3, and 4, 2026. "
        "Find 3 players or teams trending UP and 3 trending DOWN. "
        "Consider: Alperen Sengun's 39pts, Harden/Garland trade, Anthony Edwards' back spasms, "
        "and Cade Cunningham leading the Pistons' upset over Denver. "
        "Return ONLY a JSON list: "
        '[{"subject": "Name", "team": "Team", "status": "UP/DOWN", "stat": "Why?", "note": "Scout detail"}]'
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
        return extract_json_list(response.text)
    except:
        return None

# --- 3. UI LAYOUT ---
st.title("🏀 NBA Global Momentum")
st.write("League-wide performance shifts from the last 48 hours.")

trends = get_global_trends()

if trends:
    # Separate into columns for Up/Down
    up_trends = [t for t in trends if t['status'].upper() == 'UP']
    down_trends = [t for t in trends if t['status'].upper() == 'DOWN']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Trending UP")
        for item in up_trends:
            with st.container():
                st.markdown(f"""
                    <div style="background:#e6fffa; padding:15px; border-radius:10px; border-left:5px solid #38a169; margin-bottom:10px;">
                        <h4 style="margin:0; color:#2f855a;">{item['subject']} ({item['team']})</h4>
                        <p style="margin:5px 0; font-weight:bold;">{item['stat']}</p>
                        <p style="margin:0; font-size:0.85rem; color:#4a5568;">{item['note']}</p>
                    </div>
                """, unsafe_allow_html=True)

    with col2:
        st.subheader("📉 Trending DOWN")
        for item in down_trends:
            with st.container():
                st.markdown(f"""
                    <div style="background:#fff5f5; padding:15px; border-radius:10px; border-left:5px solid #e53e3e; margin-bottom:10px;">
                        <h4 style="margin:0; color:#c53030;">{item['subject']} ({item['team']})</h4>
                        <p style="margin:5px 0; font-weight:bold;">{item['stat']}</p>
                        <p style="margin:0; font-size:0.85rem; color:#4a5568;">{item['note']}</p>
                    </div>
                """, unsafe_allow_html=True)
else:
    st.error("Real-time pulse currently unavailable. Refreshing...")

st.divider()
st.caption("Data dynamically analyzed from live NBA box scores and trade trackers as of Feb 4, 2026.")