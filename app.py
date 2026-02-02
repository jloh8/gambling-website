import streamlit as st
import pandas as pd
from google import genai
from google.genai import types
from datetime import datetime
from nba_api.stats.static import teams
from nba_api.stats.endpoints import commonteamroster

# --- 1. CONFIGURATION ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"] 
client = genai.Client(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="NBA Scout", layout="centered", page_icon="🏀")

# --- 2. CLEAN UI & PRIVACY CSS ---
st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
    header, footer, #MainMenu {visibility: hidden;}
    [data-testid="stDecoration"] {display: none;}

    /* Top Narrative Box (Live Intel) */
    .scout-report-box { 
        background: #fff4e6; padding: 20px; border-radius: 12px; 
        border-left: 6px solid #e67e22; color: #d35400; 
        margin: 15px 0; font-size: 1.05rem; line-height: 1.6;
    }

    /* Numbered Deep Dive Sections (Matching your Image) */
    .section-title { font-weight: 800; color: #1c1c1e; margin-top: 25px; font-size: 1.1rem; }
    .section-content { color: #3a3a3c; line-height: 1.6; margin-bottom: 20px; }
    
    div.stButton > button:first-child {
        width: 100%; height: 3.5rem; border-radius: 12px;
        background-color: #e67e22; color: white; border: none; font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. EXPANDED AI SCOUTING FUNCTION ---
def get_nba_scout_report(team_name, roster_summary):
    prompt = (
        f"Generate a professional scout report for the {team_name} on {datetime.now().strftime('%B %d, %Y')}. "
        f"DO NOT use conversational filler like 'Okay' or 'Here is your report'. "
        f"Format the response exactly as follows: "
        f"SUMMARY: A 3-sentence narrative about the team's current situation. "
        f"1. INJURY STATUS: Detailed update on absences and impact. "
        f"2. STARTING 5: Likely lineup based on today's news. "
        f"3. FATIGUE FACTOR: Schedule analysis (back-to-backs/travel). "
        f"4. MARKET MOVEMENT: Trade rumors or betting line shifts. "
        f"5. KEY MATCHUP: Which player is the 'X-factor' for today. "
        f"6. BETTING EDGE: Final actionable betting recommendation."
    )

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

# --- 4. UI LAYOUT ---
st.title("NBA Scout")
st.write("Live Intelligence & Betting Deep-Dive")

nba_teams = teams.get_teams()
team_map = {t['full_name']: t['id'] for t in nba_teams}
selected_team = st.selectbox("Select Team", options=list(team_map.keys()), index=13)

if st.button("Generate Scout Report"):
    team_id = team_map[selected_team]
    
    with st.spinner("Analyzing News..."):
        try:
            roster_data = commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]
            roster_names = ", ".join(roster_data['PLAYER'].tolist()[:12])
        except:
            roster_names = "Standard Roster"

        raw_data = get_nba_scout_report(selected_team, roster_names)
        
        # Parsing the Summary and the 6 numbered points
        parts = raw_data.split('\n')
        summary = ""
        points = []

        for p in parts:
            if p.startswith("SUMMARY:"): summary = p.replace("SUMMARY:", "").strip()
            elif any(p.startswith(f"{i}.") for i in range(1, 7)): points.append(p)

        # 1. Display Narrative Summary (The Orange Box)
        st.markdown(f'<div class="scout-report-box">{summary}</div>', unsafe_allow_html=True)

        # 2. Display the 6 Numbered Sections (Matching the Image style)
        for point in points:
            title, content = point.split(":", 1) if ":" in point else (point, "")
            st.markdown(f'<div class="section-title">{title.strip()}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="section-content">{content.strip()}</div>', unsafe_allow_html=True)

        with st.expander("📋 View Official Roster"):
            st.dataframe(roster_data[['PLAYER', 'POSITION', 'HEIGHT']], use_container_width=True)