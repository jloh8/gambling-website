import streamlit as st
import json
import re
from google import genai
from google.genai import types
from datetime import datetime
from nba_api.stats.static import teams
from nba_api.stats.endpoints import commonteamroster

# --- 1. IMPORT PROMPT LIBRARY ---
# Ensure prompts.py is in the same directory
from prompts import get_variance_prompt, get_scout_report_prompt

# --- 2. CONFIGURATION ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"] 
client = genai.Client(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="NBA Scout & Pulse", layout="wide", page_icon="🏀")

# --- 3. GLOBAL STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; font-family: sans-serif; }
    .scout-report-box { 
        background: #fff4e6; padding: 20px; border-radius: 12px; 
        border-left: 6px solid #e67e22; color: #d35400; 
        margin: 15px 0; font-size: 1.05rem; line-height: 1.6;
    }
    .section-title { font-weight: 800; color: #1c1c1e; margin-top: 25px; border-bottom: 1px solid #eee; padding-bottom: 5px; }
    .section-content { color: #3a3a3c; line-height: 1.6; margin-bottom: 20px; }
    
    /* Base button style */
    div.stButton > button {
        width: 100% !important; height: 45px !important;
        background-color: #ffffff !important;
        text-align: left !important;
        font-size: 13px !important;
        margin-bottom: 5px !important;
    }
    .generate-btn button {
        height: 3.5rem !important; background-color: #e67e22 !important;
        color: white !important; font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. DATA ENGINES ---

@st.cache_data(ttl=1800)
def get_scoring_variance_data():
    """Pulse Engine: Fetches players with high variance + Team names."""
    today = datetime.now().strftime('%B %d, %Y')
    # Update this context as the season progresses
    context = "Focus on recent trades and 2026 rookie impacts like Cooper Flagg."
    prompt = get_variance_prompt(today, context)
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.0
            )
        )
        # Extract JSON from the markdown response
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        return json.loads(match.group(0)) if match else None
    except:
        return None

def get_nba_scout_report(team_name, roster_summary):
    """Scout Engine: Generates deep-dive team analysis."""
    today = datetime.now().strftime('%B %d, %Y')
    prompt = get_scout_report_prompt(team_name, today, roster_summary)
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.1 
            )
        )
        return response.text
    except:
        return "Intelligence Offline"

# --- 5. MAIN INTERFACE ---

if "sel_player" not in st.session_state:
    st.session_state.sel_player = None

# Spotlight View (when a player button is clicked)
if st.session_state.sel_player:
    s = st.session_state.sel_player
    st.header(f"🎯 {s['p']} Spotlight")
    col1, col2 = st.columns([1, 2])
    col1.metric("Variance", s['v'], delta=s['v'] if s['s'] == "UP" else f"-{s['v']}")
    col2.info(s['desc'])
    if st.button("Close Spotlight"):
        st.session_state.sel_player = None
        st.rerun()
    st.divider()

st.title("🏀 NBA Pulse & Scout")
st.caption(f"Live Intelligence Dashboard • {datetime.now().strftime('%B %d, %Y')}")

# --- PULSE GRID (Hot/Cold Players) ---
trends = get_scoring_variance_data()
if trends:
    st.subheader("⚡ Scoring Variance (Last 2 Games)")
    cols = st.columns(4)
    for i, item in enumerate(trends):
        with cols[i % 4]:
            is_up = item['s'] == "UP"
            btn_color = "#2ecc71" if is_up else "#e74c3c"  # Green vs Red
            prefix = "▲" if is_up else "▼"
            
            # --- DYNAMIC CSS INJECTOR ---
            # Targets buttons specifically by their key to prevent style leakage
            st.markdown(f"""
                <style>
                div[class*="st-key-pulse_{i}"] button {{
                    color: {btn_color} !important;
                    border: 1px solid {btn_color}55 !important;
                    font-weight: bold !important;
                }}
                div[class*="st-key-pulse_{i}"] button:hover {{
                    background-color: {btn_color} !important;
                    color: white !important;
                }}
                </style>
            """, unsafe_allow_html=True)
            
            # Label format: "▲ Player Name [Team] (+20%)"
            label = f"{prefix} {item['p']}\n{item['v']}"
            if st.button(label, key=f"pulse_{i}"):
                st.session_state.sel_player = item
                st.rerun()

st.divider()

# --- SCOUT REPORT SECTION ---
st.subheader("📋 Strategic Scout Report")
all_nba_teams = teams.get_teams()
team_map = {t['full_name']: t['id'] for t in all_nba_teams}
selected_team = st.selectbox("Select Team to Analyze", options=list(team_map.keys()), index=0)

st.markdown('<div class="generate-btn">', unsafe_allow_html=True)
if st.button("Generate Intelligence Report"):
    team_id = team_map[selected_team]
    with st.spinner(f"Intercepting {selected_team} data..."):
        try:
            # Fetch real roster to give Gemini more context
            roster_df = commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]
            roster_summary = ", ".join(roster_df['PLAYER'].tolist()[:12])
        except:
            roster_summary = "Roster data unavailable."

        report = get_nba_scout_report(selected_team, roster_summary)
        
        # Parse the plain-text report from Gemini
        lines = report.split('\n')
        for line in lines:
            line = line.strip()
            if not line: continue
            
            if line.startswith("SUMMARY:"): 
                st.markdown(f'<div class="scout-report-box">{line.replace("SUMMARY:", "").strip()}</div>', unsafe_allow_html=True)
            elif ":" in line:
                title, content = line.split(":", 1)
                st.markdown(f'<div class="section-title">{title.strip()}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="section-content">{content.strip()}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="section-content">{line}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)