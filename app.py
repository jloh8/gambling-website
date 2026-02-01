import streamlit as st
import pandas as pd
from google import genai
from google.genai import types
from google.api_core import exceptions
import time
from datetime import datetime
from nba_api.stats.static import teams
from nba_api.stats.endpoints import commonteamroster

# --- CONFIGURATION ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"] 
client = genai.Client(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="Gemini NBA Scout", layout="wide", page_icon="🏀")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .scout-report { background: #fff4e6; padding: 20px; border-radius: 12px; border-left: 6px solid #e67e22; color: #d35400; margin: 15px 0; }
    .roster-card { font-size: 0.9rem; color: #2c3e50; }
</style>
""", unsafe_allow_html=True)

# --- AI SCOUTING FUNCTION ---
def get_nba_scout_report(team_name, roster_summary, max_retries=3):
    """
    Uses Gemini with Google Search Grounding to find 'Betting Intel'.
    """
    prompt = (
        f"Act as a professional NBA betting analyst. Research the {team_name} for today, {datetime.now().strftime('%B %d, %Y')}. "
        f"Provide a concise Scout Report covering: "
        f"1. **Injury/Hurt List**: Who is out or questionable? "
        f"2. **Projected Starting 5**: Given injuries, who is likely starting? "
        f"3. **Fatigue Factor**: Are they on a back-to-back? Recent travel schedule? "
        f"4. **Roster Drama**: Any contract issues, trade rumors, or 'locker room' vibes? "
        f"Reference current news from today's beat reporters."
    )

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            return response.text
        except exceptions.ResourceExhausted:
            wait_time = (2 ** attempt) * 10
            st.warning(f"⚠️ Rate limit hit. Waiting {wait_time}s...")
            time.sleep(wait_time)
        except Exception as e:
            return f"❌ AI Error: {str(e)}"
    return "⏭️ Max retries reached."

# --- MAIN UI ---
st.title("🏀 Gemini NBA Betting Scout")
st.write("Real-time intelligence on injuries, lineups, and travel fatigue.")

# Get all NBA teams for the dropdown
nba_teams = teams.get_teams()
team_map = {t['full_name']: t['id'] for t in nba_teams}

with st.sidebar:
    st.header("Select Your Matchup")
    selected_team = st.selectbox("Team to Scout", options=list(team_map.keys()), index=13) # Default Lakers
    st.info("💡 Uses Google Search to find 'invisible' data like travel fatigue and locker room news.")

if st.button("Generate Scout Report", type="primary", use_container_width=True):
    team_id = team_map[selected_team]
    
    with st.spinner(f"Gathering intel on the {selected_team}..."):
        # 1. Get Static Roster Data (from nba_api)
        try:
            roster = commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]
            roster_names = roster['PLAYER'].tolist()
            roster_summary = ", ".join(roster_names[:10]) # Send top 10 names for context
        except:
            roster_summary = "Unknown"
            st.error("Could not fetch official roster, proceeding with AI search only.")

        # 2. Get AI Analysis
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("📋 Official Roster")
            if not roster.empty:
                st.dataframe(roster[['PLAYER', 'NUM', 'POSITION', 'HEIGHT']], height=400)
            else:
                st.write("Roster data unavailable.")

        with col2:
            st.subheader("🔥 Live Scout Report")
            report = get_nba_scout_report(selected_team, roster_summary)
            st.markdown(f"<div class='scout-report'>{report}</div>", unsafe_allow_html=True)
            
        st.balloons()

st.markdown("---")
st.caption("Data sources: NBA.com (Static) & Google Search Grounding (Live Catalyst). Use for informational purposes only.")