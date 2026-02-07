import streamlit as st
import pandas as pd
import numpy as np
from nba_api.stats.static import teams
from nba_api.stats.endpoints import commonteamroster
from google import genai

# --- 1. CONFIG & CLIENT ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"] 
client = genai.Client(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="NBA Pulse", layout="wide", page_icon="🏀")

# --- 2. CUSTOM CSS FOR MATCHUP CARDS ---
st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; color: #1c1c1e; }
    
    /* Section Headers */
    .section-header {
        font-size: 0.75rem; font-weight: 700; color: #8e8e93;
        text-transform: uppercase; letter-spacing: 0.8px; margin: 20px 0 10px 0;
    }

    /* Kalshi-Style Card Container */
    .market-card {
        border: 1px solid #f2f2f7; border-radius: 16px;
        padding: 20px; margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02);
    }

    /* Team Row Layout */
    .team-row {
        display: flex; justify-content: space-between; align-items: center;
        padding: 8px 0;
    }
    .team-info { display: flex; align-items: center; gap: 12px; }
    .team-name { font-weight: 700; font-size: 1rem; color: #1c1c1e; }
    
    /* Probability & Price Styling */
    .prob-text { color: #8e8e93; font-size: 0.85rem; font-weight: 500; }
    
    /* Button Overrides */
    div.stButton > button {
        border-radius: 8px !important; border: 1px solid #e5e5ea !important;
        background: #f2f2f7 !important; color: #1c1c1e !important;
        font-weight: 700 !important; width: 100% !important; padding: 10px !important;
    }
    div.stButton > button:hover { background: #e8f5e9 !important; border-color: #c8e6c9 !important; color: #2e7d32 !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. MOCK MATCHUP DATA ---
# In a live app, you'd use leaguegamefinder for daily matchups
matchups = [
    {"home": "Oklahoma City", "away": "Denver", "prob": "40%", "price_yes": "40¢", "price_no": "61¢"},
    {"home": "Cleveland", "away": "New York", "prob": "23%", "price_yes": "23¢", "price_no": "78¢"},
    {"home": "Charlotte", "away": "Atlanta", "prob": "56%", "price_yes": "56¢", "price_no": "45¢"}
]

# --- 4. MAIN UI ---

col_left, col_right = st.columns([1.8, 1.2])

with col_left:
    st.markdown('<div class="section-header">Live Markets</div>', unsafe_allow_html=True)
    
    for i, m in enumerate(matchups):
        with st.container():
            st.markdown(f'<div class="market-card">', unsafe_allow_html=True)
            
            # Matchup Header
            st.markdown(f"**Championship: {m['away']} vs {m['home']}**")
            
            # Away Team Row
            r1_left, r1_mid, r1_btn1, r1_btn2 = st.columns([2, 1, 1, 1])
            with r1_left: st.markdown(f"🏀 **{m['away']}**")
            with r1_mid: st.markdown(f"<span class='prob-text'>{m['prob']}</span>", unsafe_allow_html=True)
            with r1_btn1: 
                if st.button(f"Yes {m['price_yes']}", key=f"y_{i}"):
                    st.session_state.selected_team = m['away']
            with r1_btn2: st.button(f"No {m['price_no']}", key=f"n_{i}")

            # Home Team Row
            r2_left, r2_mid, r2_btn1, r2_btn2 = st.columns([2, 1, 1, 1])
            with r2_left: st.markdown(f"🏀 **{m['home']}**")
            with r2_mid: st.markdown(f"<span class='prob-text'>{(100-int(m['prob'].strip('%')))}%</span>", unsafe_allow_html=True)
            with r2_btn1: 
                if st.button(f"Yes 50¢", key=f"y_h_{i}"):
                    st.session_state.selected_team = m['home']
            with r2_btn2: st.button(f"No 50¢", key=f"n_h_{i}")
            
            st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="section-header">Intelligence Report</div>', unsafe_allow_html=True)
    
    if "selected_team" in st.session_state:
        st.markdown(f'<div class="market-card" style="background:#f9f9fb;">', unsafe_allow_html=True)
        st.markdown(f"### Scouting: {st.session_state.selected_team}")
        
        with st.spinner(f"Analyzing {st.session_state.selected_team} strategy..."):
            # Fetch real roster for the selected team
            all_teams = teams.get_teams()
            team_id = next(t['id'] for t in all_teams if st.session_state.selected_team in t['full_name'])
            roster = commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]
            names = ", ".join(roster['PLAYER'].head(5).tolist())
            
            st.markdown(f"**Key Rotation:** {names}")
            st.info("Gemini Analysis: Expect high variance in perimeter defense for this matchup.")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="text-align:center; padding: 40px; color:#8e8e93;">Select a "Yes" contract to see team intel</div>', unsafe_allow_html=True)