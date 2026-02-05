import streamlit as st
import pandas as pd
import json
import re
from google import genai
from google.genai import types
from datetime import datetime
from nba_api.stats.static import teams
from nba_api.stats.endpoints import commonteamroster

# --- 1. CONFIGURATION ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"] 
client = genai.Client(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="NBA Scout & Pulse", layout="wide", page_icon="🏀")

# --- 2. COMBINED STYLING ---
st.markdown("""
<style>
    /* Global Styles */
    .stApp { background-color: #FFFFFF; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
    
    /* Scout Report Styling */
    .scout-report-box { 
        background: #fff4e6; padding: 20px; border-radius: 12px; 
        border-left: 6px solid #e67e22; color: #d35400; 
        margin: 15px 0; font-size: 1.05rem; line-height: 1.6;
    }
    .section-title { font-weight: 800; color: #1c1c1e; margin-top: 25px; font-size: 1.1rem; border-bottom: 1px solid #eee; padding-bottom: 5px; }
    .section-content { color: #3a3a3c; line-height: 1.6; margin-bottom: 20px; }

    /* Compact Variance Button Styling */
    div.stButton > button {
        width: 100% !important; /* Adapt to column width */
        height: 32px !important;
        font-family: "Inter", sans-serif !important;
        font-size: 13px !important;
        background-color: #f8f9fa !important;
        color: #448aff !important;
        border: 1px solid #eee !important;
        text-align: left !important;
        margin-bottom: 4px !important;
        transition: 0.2s;
    }
    
    div.stButton > button:hover {
        background-color: #1e222d !important;
        color: #ffffff !important;
        border-color: #448aff !important;
    }

    /* Pulse/Scout Big Button */
    .generate-btn button {
        height: 3.5rem !important;
        background-color: #e67e22 !important;
        color: white !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. ENGINES ---

@st.cache_data(ttl=1800)
def get_scoring_variance_data():
    """Pulse Engine: Identifies scoring outliers."""
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
        # Robust JSON extraction
        match = re.search(r'\[.*\]', response.text, re.DOTALL)
        return json.loads(match.group(0)) if match else None
    except:
        return None

def get_nba_scout_report(team_name, roster_summary):
    """Scout Engine: Deep dive intelligence."""
    prompt = (
        f"Generate a professional scout report for the {team_name} on {datetime.now().strftime('%B %d, %Y')}. "
        f"DO NOT use conversational filler like 'Okay' or 'Here is your report'. "
        f"Format the response exactly as follows: "
        f"SUMMARY: A 3-sentence narrative about the team's current situation. "
        f"1. INJURY STATUS: Detailed update on absences and impact, two sentence. "
        f"2. STARTING 5: Likely lineup based on today's news. "
        f"3. FATIGUE FACTOR: Schedule analysis, other juicy news like lifestyle rumors or travel fatigue. "
        f"4. MARKET MOVEMENT: Trade rumors. "
        f"5. BETTING EDGE 1: what is at stake for this team? do a deep dive. "
        f"6. BETTING EDGE 2: find me the biggest edge against their next oponent that is not obvious to regular fans. "
        f"7. BETTING EDGE 3: give me a solid argument of why this team will win today based on past trends. "
        f"8. BETTING EDGE 4: what is the most interesting bet on the lowest odd to win for today? "
        f"9. BETTING EDGE 5: Last 10 games performance vs Spread and O/U. "
        f"10. BETTING EDGE 6: Biggest player edge against next opponent."
    )
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.1 
            )
        )
        return response.text
    except:
        return "Intelligence Offline"

# --- 4. MAIN UI LOGIC ---

# Sidebar Navigation / Details
if "sel_player" not in st.session_state:
    st.session_state.sel_player = None

# Detail Overlay for Pulse
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

# Top Section: Pulse (Variance)
st.title("🏀 NBA Pulse & Scout")
st.caption(f"Live Intelligence: {datetime.now().strftime('%B %d, %Y')}")

trends = get_scoring_variance_data()
if trends:
    st.subheader("⚡ Scoring Variance (Last 2 Games)")
    # Layout into 4 columns for compact look
    cols = st.columns(4)
    for i, item in enumerate(trends):
        with cols[i % 4]:
            # Color code based on direction
            prefix = "▲" if item['s'] == "UP" else "▼"
            label = f"{prefix} {item['p'][:12]} ({item['v']})"
            if st.button(label, key=f"pulse_{i}"):
                st.session_state.sel_player = item
                st.rerun()
else:
    st.info("Loading live variance data...")

st.divider()

# Bottom Section: Scout (Team Reports)
st.subheader("📋 Strategic Scout Report")
nba_teams = teams.get_teams()
team_map = {t['full_name']: t['id'] for t in nba_teams}
selected_team = st.selectbox("Select Team to Analyze", options=list(team_map.keys()), index=13)

# Wrap button in a div for specific styling
st.markdown('<div class="generate-btn">', unsafe_allow_html=True)
if st.button("Generate Intelligence Report"):
    team_id = team_map[selected_team]
    with st.spinner(f"Intercepting {selected_team} data..."):
        try:
            roster_data = commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]
            roster_names = ", ".join(roster_data['PLAYER'].tolist()[:12])
        except:
            roster_names = "Standard Roster"

        raw_report = get_nba_scout_report(selected_team, roster_names)
        
        # Display Logic
        parts = raw_report.split('\n')
        summary = ""
        points = []

        for p in parts:
            p = p.strip()
            if not p: continue
            if p.startswith("SUMMARY:"): 
                summary = p.replace("SUMMARY:", "").strip()
            elif any(p.startswith(f"{i}.") for i in range(1, 11)): 
                points.append(p)

        if summary:
            st.markdown(f'<div class="scout-report-box">{summary}</div>', unsafe_allow_html=True)

        for point in points:
            if ":" in point:
                title, content = point.split(":", 1)
                st.markdown(f'<div class="section-title">{title.strip()}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="section-content">{content.strip()}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="section-content"><b>{point}</b></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)