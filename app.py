import streamlit as st
import json
import re
from google import genai
from google.genai import types
from datetime import datetime
from nba_api.stats.static import teams
from nba_api.stats.endpoints import commonteamroster

# --- 1. IMPORT PROMPT LIBRARY ---
from prompts import get_variance_prompt, get_scout_report_prompt

# --- 2. CONFIGURATION ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"] 
client = genai.Client(api_key=GEMINI_API_KEY)

st.set_page_config(
    page_title="NBA Pulse", 
    layout="wide", 
    page_icon="🏀",
    initial_sidebar_state="collapsed"
)

# --- 3. MOBILE-FIRST GLOBAL STYLING ---
st.markdown("""
<style>
    /* Main container adjustments */
    .stApp { background-color: #FFFFFF; }
    
    /* Responsive Scout Box */
    .scout-report-box { 
        background: #fff4e6; padding: 15px; border-radius: 8px; 
        border-left: 5px solid #e67e22; color: #d35400; 
        margin: 10px 0; font-size: 0.95rem; line-height: 1.4;
    }
    
    .section-title { font-weight: 800; color: #1c1c1e; margin-top: 18px; font-size: 1rem; border-bottom: 1px solid #eee; }
    .section-content { color: #3a3a3c; font-size: 0.9rem; line-height: 1.5; margin-bottom: 15px; }

    /* Touch-friendly Buttons */
    div.stButton > button {
        width: 100% !important; 
        height: auto !important;
        padding: 10px 5px !important;
        background-color: #ffffff !important;
        text-align: center !important;
        font-size: 12px !important;
        margin-bottom: 8px !important;
        border-radius: 8px !important;
        white-space: normal !important; /* Allows text to wrap on small screens */
    }

    /* Big Generate Button */
    .generate-btn button {
        height: 4rem !important; 
        background-color: #e67e22 !important;
        color: white !important; 
        font-weight: 700 !important;
        font-size: 1.1rem !important;
    }

    /* Reduce vertical whitespace for mobile */
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
</style>
""", unsafe_allow_html=True)

# --- 4. ENGINES ---

@st.cache_data(ttl=1800)
def get_scoring_variance_data():
    today = datetime.now().strftime('%B %d, %Y')
    context = "2026 Season context: Cooper Flagg (Mavs), Jaden Ivey (Bulls), Sengun (Rockets)."
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
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        return json.loads(match.group(0)) if match else None
    except:
        return None

def get_nba_scout_report(team_name, roster_summary):
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

# --- 5. UI LOGIC ---

if "sel_player" not in st.session_state:
    st.session_state.sel_player = None

# Spotlight View (Optimized for Mobile overlay)
if st.session_state.sel_player:
    s = st.session_state.sel_player
    st.subheader(f"🎯 Spotlight: {s['p']}")
    v_color = "green" if s['s'] == "UP" else "red"
    st.markdown(f"**Variance:** <span style='color:{v_color}; font-weight:bold;'>{s['v']}</span>", unsafe_allow_html=True)
    st.info(s['desc'])
    if st.button("← Back to Dashboard"):
        st.session_state.sel_player = None
        st.rerun()
    st.divider()

st.title("🏀 NBA Pulse")
st.caption(f"Intelligence Update: {datetime.now().strftime('%b %d')}")

# --- PULSE GRID (2 columns on mobile, 4 on desktop) ---
trends = get_scoring_variance_data()
if trends:
    st.write("⚡ **Hot & Cold Variance**")
    # On mobile, we use 2 columns to keep buttons large enough to tap
    cols = st.columns(2) 
    for i, item in enumerate(trends):
        col_idx = i % 2 # Force 2nd column wrap
        with cols[col_idx]:
            is_up = item['s'] == "UP"
            btn_color = "#2ecc71" if is_up else "#e74c3c"
            prefix = "▲" if is_up else "▼"
            
            st.markdown(f"""
                <style>
                div[class*="st-key-pulse_{i}"] button {{
                    color: {btn_color} !important;
                    border: 1.5px solid {btn_color} !important;
                }}
                </style>
            """, unsafe_allow_html=True)
            
            # Label with Player [Team] and Variance
            label = f"{prefix} {item['p']}\n{item['v']}"
            if st.button(label, key=f"pulse_{i}"):
                st.session_state.sel_player = item
                st.rerun()

st.divider()

# --- SCOUT REPORT SECTION ---
st.subheader("📋 Team Scout")
all_teams = teams.get_teams()
team_map = {t['full_name']: t['id'] for t in all_teams}
selected_team = st.selectbox("Pick a Team", options=list(team_map.keys()), index=0)

st.markdown('<div class="generate-btn">', unsafe_allow_html=True)
if st.button("Get Intelligence"):
    team_id = team_map[selected_team]
    with st.spinner("Intercepting..."):
        try:
            roster_df = commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]
            roster_summary = ", ".join(roster_df['PLAYER'].tolist()[:10])
        except:
            roster_summary = "Roster loading error."

        report = get_nba_scout_report(selected_team, roster_summary)
        
        # Mobile Parsing Render
        lines = report.split('\n')
        for line in lines:
            line = line.strip()
            if not line: continue
            
            if line.startswith("SUMMARY:"): 
                st.markdown(f'<div class="scout-report-box">{line.replace("SUMMARY:", "").strip()}</div>', unsafe_allow_html=True)
            elif ":" in line:
                title, content = line.split(":", 1)
                st.markdown(f"**{title.strip()}**")
                st.markdown(f"<div class='section-content'>{content.strip()}</div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)