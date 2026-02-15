import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime
from nba_api.stats.static import teams
from nba_api.stats.endpoints import commonteamroster
from google import genai
from prompts import get_scout_report_prompt

# --- 1. CONFIG & CLIENT ---
# Ensure your Secrets are set in Streamlit Cloud or .streamlit/secrets.toml
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"] 
client = genai.Client(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="NBA Pulse", layout="wide", page_icon="🏀")

# --- 2. DATABASE SYSTEM ---
def init_db():
    """Creates the database and table if they don't exist."""
    try:
        conn = sqlite3.connect('nba_intel.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS reports
                     (team TEXT, report_date TEXT, content TEXT, 
                     PRIMARY KEY (team, report_date))''')
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Database Initialization Error: {e}")

def get_cached_report(team, date):
    """Checks if we already have a report for this team today."""
    conn = sqlite3.connect('nba_intel.db')
    c = conn.cursor()
    c.execute("SELECT content FROM reports WHERE team = ? AND report_date = ?", (team, date))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def save_report(team, date, content):
    """Saves the Gemini result so we don't have to pay for it again today."""
    conn = sqlite3.connect('nba_intel.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO reports (team, report_date, content) VALUES (?, ?, ?)", 
              (team, date, content))
    conn.commit()
    conn.close()

# Initialize the database immediately
init_db()

# --- 3. STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; color: #1c1c1e; }
    .section-header { font-size: 0.75rem; font-weight: 700; color: #8e8e93; text-transform: uppercase; margin: 20px 0 10px 0; }
    .market-card { border: 1px solid #f2f2f7; border-radius: 16px; padding: 20px; margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.02); }
</style>
""", unsafe_allow_html=True)

# --- 4. DATA ---
matchups = [
    {"home": "Oklahoma City Thunder", "away": "Denver Nuggets", "prob": "40%"},
    {"home": "Cleveland Cavaliers", "away": "New York Knicks", "prob": "23%"},
    {"home": "Charlotte Hornets", "away": "Atlanta Hawks", "prob": "56%"}
]

# --- 5. UI LAYOUT ---
col_left, col_right = st.columns([1.8, 1.2])

with col_left:
    st.markdown('<div class="section-header">Live NBA Markets</div>', unsafe_allow_html=True)
    for i, m in enumerate(matchups):
        with st.container():
            st.markdown('<div class="market-card">', unsafe_allow_html=True)
            st.write(f"**{m['away']} @ {m['home']}**")
            
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1: st.markdown(f"🏀 {m['away']}")
            with c3: 
                if st.button(f"Scout {m['away']}", key=f"btn_away_{i}"):
                    st.session_state.selected_team = m['away']
            
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1: st.markdown(f"🏠 {m['home']}")
            with c3: 
                if st.button(f"Scout {m['home']}", key=f"btn_home_{i}"):
                    st.session_state.selected_team = m['home']
            st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="section-header">Intelligence Report</div>', unsafe_allow_html=True)
    
    if "selected_team" in st.session_state:
        team = st.session_state.selected_team
        today = datetime.now().strftime("%Y-%m-%d")
        
        st.markdown(f"### 🛡️ {team}")
        
        # STEP 1: Check Database
        cached_data = get_cached_report(team, today)
        
        if cached_data:
            st.success("Loaded from Database (Saved API Credits)")
            st.markdown(cached_data)
        else:
            # STEP 2: If not in DB, run the AI
            with st.spinner(f"Querying Gemini for {team}..."):
                try:
                    # Get Roster Data
                    all_teams = teams.get_teams()
                    team_info = next(t for t in all_teams if team.lower() in t['full_name'].lower())
                    roster = commonteamroster.CommonTeamRoster(team_id=team_info['id']).get_data_frames()[0]
                    player_names = ", ".join(roster['PLAYER'].head(10).tolist())

                    # Get Prompt from prompts.py
                    prompt_text = get_scout_report_prompt(team, today, player_names)
                    
                    # Call Gemini
                    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt_text)
                    final_report = response.text
                    
                    # STEP 3: Save to Database for next time
                    save_report(team, today, final_report)
                    
                    st.markdown(final_report)
                except Exception as e:
                    st.error(f"Analysis Failed: {e}")
    else:
        st.info("Select a team on the left to generate or view its scouting report.")