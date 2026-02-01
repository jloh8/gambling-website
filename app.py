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

# --- 2. iPHONE OPTIMIZED UI ---
st.set_page_config(page_title="NBA Scout", layout="centered", page_icon="🏀")

# Custom CSS for "App-like" feel on mobile
st.markdown("""
<style>
    /* Dark Mode iOS Theme */
    .stApp { background-color: #000000; }
    
    /* Bigger Buttons for Thumbs */
    div.stButton > button:first-child {
        width: 100%;
        height: 3.5rem;
        border-radius: 12px;
        background: linear-gradient(135deg, #e67e22 0%, #d35400 100%);
        border: none;
        font-weight: 700;
        font-size: 1.1rem;
    }

    /* Card-style Scout Reports */
    .scout-report { 
        background: #1c1c1e; 
        padding: 18px; 
        border-radius: 16px; 
        border: 1px solid #38383a; 
        color: #f1f1f1; 
        margin-bottom: 20px;
        line-height: 1.5;
        font-size: 1rem;
    }

    /* Roster Styling */
    .roster-header { 
        color: #e67e22; 
        font-size: 1.2rem;
        font-weight: 800; 
        margin-top: 10px;
    }

    /* Responsive Spacing */
    .block-container { padding-top: 2rem !important; }
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
        f"4. **Betting Edge**: One-sentence locker room/trade vibe."
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
    return "⏭️ Intelligence unavailable. Try again in a minute."

# --- 4. MOBILE UI LAYOUT ---
st.title("🏀 NBA Scout")
st.caption("Live Intelligence • Grounded by Gemini AI")

# Team Selection (Dropdown is naturally good on iOS)
nba_teams = teams.get_teams()
team_map = {t['full_name']: t['id'] for t in nba_teams}
selected_team = st.selectbox("Choose a Team", options=list(team_map.keys()), index=13)

if st.button("Generate Scout Report"):
    team_id = team_map[selected_team]
    
    with st.spinner(f"Scouting the {selected_team}..."):
        # 1. Fetch Roster
        try:
            roster_data = commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]
            roster_summary = ", ".join(roster_data['PLAYER'].tolist()[:10])
        except:
            roster_summary = "Unknown"

        # 2. AI Intelligence (First for Mobile Priority)
        st.markdown("<p class='roster-header'>🔥 Live Intel</p>", unsafe_allow_html=True)
        report = get_nba_scout_report(selected_team, roster_summary)
        st.markdown(f"<div class='scout-report'>{report}</div>", unsafe_allow_html=True)
        
        # 3. Roster (Inside Expander to save vertical space)
        with st.expander("📋 View Full Roster"):
            if not roster_data.empty:
                st.dataframe(roster_data[['PLAYER', 'POSITION', 'HEIGHT']], use_container_width=True)
            else:
                st.write("Roster offline.")
        
        st.balloons()

st.divider()
st.caption("Designed for iPhone 13+ Pro • Source: NBA & Google")