import streamlit as st
import pandas as pd
from google import genai
from google.genai import types
from google.api_core import exceptions
import time
from datetime import datetime
from nba_api.stats.static import teams
from nba_api.stats.endpoints import commonteamroster

# --- 1. CONFIGURATION ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"] 
client = genai.Client(api_key=GEMINI_API_KEY)

# --- 2. THEME & PRIVACY CSS ---
st.set_page_config(page_title="NBA Scout", layout="centered", page_icon="🏀")

st.markdown("""
<style>
    /* 1. White Background & Readable Font */
    .stApp {
        background-color: #FFFFFF;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    
    /* 2. Hide GitHub/Deploy Menu (Top Right) & Footer (Bottom Right) */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    [data-testid="stDecoration"] {display: none;} /* Hides the top red bar */

    /* 3. Button Styling for High Contrast */
    div.stButton > button:first-child {
        width: 100%;
        height: 3.5rem;
        border-radius: 12px;
        background-color: #e67e22;
        color: white;
        border: none;
        font-weight: 700;
        font-size: 1.1rem;
    }

    /* 4. Scout Report Card (Subtle Light Theme) */
    .scout-report { 
        background: #f8f9fa; 
        padding: 20px; 
        border-radius: 16px; 
        border: 1px solid #dee2e6; 
        color: #212529; 
        margin-bottom: 20px;
        line-height: 1.6;
    }
    
    /* 5. Headers */
    h1, h2, h3 { color: #212529 !important; }
    .roster-header { 
        color: #e67e22; 
        font-size: 1.2rem;
        font-weight: 800; 
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. AI SCOUTING FUNCTION ---
def get_nba_scout_report(team_name, roster_summary, max_retries=3):
    prompt = (
        f"Research the {team_name} for {datetime.now().strftime('%B %d, %Y')}. "
        f"Provide a concise Scout Report for mobile users: "
        f"1. **Injury Status**: Key absences today. "
        f"2. **Starting 5**: Likely lineup. "
        f"3. **Fatigue**: Travel/Back-to-back info. "
        f"4. **Betting Edge**: One-sentence catalyst."
    )

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())])
            )
            return response.text
        except:
            time.sleep(5)
    return "⏭️ Intelligence unavailable. Try again shortly."

# --- 4. UI LAYOUT ---
st.title("🏀 NBA Scout")
st.write("Real-time intelligence on injuries and lineups.")

nba_teams = teams.get_teams()
team_map = {t['full_name']: t['id'] for t in nba_teams}
selected_team = st.selectbox("Choose a Team", options=list(team_map.keys()), index=13)

if st.button("Generate Scout Report"):
    team_id = team_map[selected_team]
    
    with st.spinner(f"Scouting the {selected_team}..."):
        try:
            roster_data = commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]
            roster_summary = ", ".join(roster_data['PLAYER'].tolist()[:10])
        except:
            roster_summary = "Unknown"

        st.markdown("<p class='roster-header'>🔥 Live Intel</p>", unsafe_allow_html=True)
        report = get_nba_scout_report(selected_team, roster_summary)
        st.markdown(f"<div class='scout-report'>{report}</div>", unsafe_allow_html=True)
        
        with st.expander("📋 View Official Roster"):
            if not roster_data.empty:
                st.dataframe(roster_data[['PLAYER', 'POSITION', 'HEIGHT']], use_container_width=True)
            else:
                st.write("Roster offline.")
        
        st.balloons()