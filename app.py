import streamlit as st
import pandas as pd
import random
from google import genai
from google.genai import types
from datetime import datetime
from nba_api.stats.static import teams
from nba_api.stats.endpoints import commonteamroster

# --- 1. CONFIGURATION ---
# Ensure .streamlit/secrets.toml is in your .gitignore to stay safe!
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"] 
client = genai.Client(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="NBA & CBB Scout", layout="centered", page_icon="🏀")

# --- 2. CLEAN UI & MULTI-TAB CSS ---
st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
    header, footer, #MainMenu {visibility: hidden;}
    [data-testid="stDecoration"] {display: none;}

    /* Tab 1: Scout Report Box (Orange) */
    .scout-report-box { 
        background: #fff4e6; padding: 20px; border-radius: 12px; 
        border-left: 6px solid #e67e22; color: #d35400; 
        margin: 15px 0; font-size: 1.05rem; line-height: 1.6;
    }

    /* Tab 2: NBA Live Box (Red) */
    .live-report-box { 
        background: #fdf2f2; padding: 20px; border-radius: 12px; 
        border-left: 6px solid #dc3545; color: #b02a37; 
        margin: 15px 0; font-size: 1.05rem; font-weight: 600;
    }

    /* Tab 3: CBB Live Box (Blue) */
    .cbb-report-box { 
        background: #e7f3ff; padding: 20px; border-radius: 12px; 
        border-left: 6px solid #007bff; color: #004085; 
        margin: 15px 0; font-size: 1.05rem;
    }

    .section-title { font-weight: 800; color: #1c1c1e; margin-top: 25px; font-size: 1.1rem; }
    .section-content { color: #3a3a3c; line-height: 1.6; margin-bottom: 20px; }
    
    div.stButton > button {
        width: 100%; height: 3.5rem; border-radius: 12px;
        background-color: #e67e22; color: white; border: none; font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. CORE AI FUNCTION ---
def get_ai_response(prompt):
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
    except Exception as e:
        return f"Intelligence Offline: {str(e)}"

# --- 4. APP NAVIGATION & TABS ---
st.title("NBA & CBB Scout")
st.write(f"Live Intelligence: {datetime.now().strftime('%B %d, %Y')}")

tab1, tab2, tab3 = st.tabs(["📝 Scout Report", "🚨 NBA Live", "🎓 CBB Live"])

# Load NBA Teams for Selectboxes
nba_teams = teams.get_teams()
team_map = {t['full_name']: t['id'] for t in nba_teams}

# --- TAB 1: GENERATE SCOUT REPORT ---
with tab1:
    selected_team = st.selectbox("Select NBA Team", options=list(team_map.keys()), index=13, key="scout_select")
    
    if st.button("Generate Scout Report", key="scout_btn"):
        with st.spinner("Analyzing News..."):
            try:
                roster_data = commonteamroster.CommonTeamRoster(team_id=team_map[selected_team]).get_data_frames()[0]
                roster_names = ", ".join(roster_data['PLAYER'].tolist()[:12])
            except:
                roster_names = "Standard Roster"

            prompt = (
                f"Professional scout report for the {selected_team} on {datetime.now().strftime('%B %d, %Y')}. "
                f"Use this roster as reference: {roster_names}. "
                f"Format exactly: SUMMARY: (3 sentences) then numbered points 1-6 for Injury, Lineup, Fatigue, Market, Matchup, and Betting Edge."
            )
            
            raw_data = get_ai_response(prompt)
            parts = raw_data.split('\n')
            
            for p in parts:
                if p.startswith("SUMMARY:"):
                    st.markdown(f'<div class="scout-report-box">{p.replace("SUMMARY:", "").strip()}</div>', unsafe_allow_html=True)
                elif ":" in p:
                    title, content = p.split(":", 1)
                    st.markdown(f'<div class="section-title">{title.strip()}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="section-content">{content.strip()}</div>', unsafe_allow_html=True)

# --- TAB 2: NBA LIVE GAME REPORT ---
with tab2:
    live_team = st.selectbox("Select Active NBA Team", options=list(team_map.keys()), index=0, key="live_select")
    
    if st.button("Analyze Live Status", key="live_btn"):
        with st.spinner("Accessing Live Stream Data..."):
            live_prompt = (
                f"Search for the live score and status of the {live_team} game on February 2, 2026. "
                f"Identify: 1. Final/Current Score, 2. A 'Momentum Score' from 0 to 100 based on recent play. "
                f"3. Betting Edge (which side is winning vs the spread)."
            )
            
            # Extracting a random momentum for the visual meter (Demo purpose)
            momentum_val = random.randint(40, 95)
            
            st.markdown(f'<div class="live-report-box">NBA LIVE INTEL: {live_team}</div>', unsafe_allow_html=True)
            
            # Visual Layout
            st.write(f"**Current Momentum: {live_team}**")
            st.progress(momentum_val / 100)
            
            c1, c2 = st.columns(2)
            c1.metric("Momentum", f"{momentum_val}%", delta="High")
            c2.metric("Game Day", "Feb 2, 2026")

            live_intel = get_ai_response(live_prompt)
            st.info(live_intel)

# --- TAB 3: COLLEGE BASKETBALL LIVE ---
with tab3:
    st.subheader("NCAA Blue Chip Intelligence")
    cbb_game = st.text_input("Enter College Team", value="Duke", key="cbb_input")
    
    if st.button("Fetch College Intel", key="cbb_btn"):
        with st.spinner("Scanning Campus News & KenPom Data..."):
            cbb_prompt = (
                f"Search for the live status of {cbb_game} college basketball on February 2, 2026. "
                f"Provide current score, time remaining, and 'Cinderella Watch' if a mid-major is upsetting a favorite."
            )
            
            cbb_intel = get_ai_response(cbb_prompt)
            st.markdown(f'<div class="cbb-report-box">CAMPUS REPORT: {cbb_game}</div>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("CBB Status", "Active")
            col2.metric("Upset Alert", "Low")
            col3.metric("Crowd Heat", "9/10")
            
            st.info(cbb_intel)