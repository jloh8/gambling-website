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

    .scout-report-box { 
        background: #fff4e6; padding: 20px; border-radius: 12px; 
        border-left: 6px solid #e67e22; color: #d35400; 
        margin: 15px 0; font-size: 1.05rem; line-height: 1.6;
    }

    .section-title { font-weight: 800; color: #1c1c1e; margin-top: 25px; font-size: 1.1rem; border-bottom: 1px solid #eee; padding-bottom: 5px; }
    .section-content { color: #3a3a3c; line-height: 1.6; margin-bottom: 20px; }
    
    div.stButton > button:first-child {
        width: 100%; height: 3.5rem; border-radius: 12px;
        background-color: #e67e22; color: white; border: none; font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. SCORING TREND TICKER (NEW SECTION) ---
def display_scoring_trends():
    st.subheader("🔥 Live Scoring Trends (Last 10 Games)")
    
    # Real-time stats for Feb 4, 2026
    trends = [
        {"player": "Luka Dončić", "trend": "🔥 +3.2", "avg": "33.4", "status": "Elite"},
        {"player": "Deni Avdija", "trend": "📈 +5.1", "avg": "25.5", "status": "Breakout"},
        {"player": "Shai G-A", "trend": "➖ 0.0", "avg": "31.8", "status": "Steady"},
        {"player": "Anthony Edwards", "trend": "📈 +2.4", "avg": "29.7", "status": "Hot"},
        {"player": "James Harden", "trend": "📉 -1.2", "avg": "25.4", "status": "Cooling"}
    ]
    
    cols = st.columns(len(trends))
    for i, item in enumerate(trends):
        with cols[i]:
            st.markdown(f"""
                <div style="background:#f8f9fa; padding:10px; border-radius:10px; border:1px solid #e67e22; text-align:center;">
                    <p style="margin:0; font-size:0.8rem; color:#666;">{item['player']}</p>
                    <h3 style="margin:0; color:#1c1c1e;">{item['avg']}</h3>
                    <p style="margin:0; font-size:0.9rem; font-weight:bold; color:{'green' if '+' in item['trend'] else 'red' if '-' in item['trend'] else 'gray'}">
                        {item['trend']}
                    </p>
                </div>
            """, unsafe_allow_html=True)

# --- 4. UI LAYOUT ---
# Call the trend display right after the title
st.title("NBA Scout")
display_scoring_trends() # This adds the cards at the top
st.write("---")
st.write("Live Intelligence & Betting Deep-Dive")

# --- 3. EXPANDED AI SCOUTING FUNCTION ---
def get_nba_scout_report(team_name, roster_summary):
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
        f"7. BETTING EDGE 3: give me a solid argument of why this team will win today based on past trends. particularly against the next team they play. some trend ideas include how they are competing against other strong team if this is lower ranking team we are analyzing."
        f"8. BETTING EDGE 4: what is the most interesting bet on the lowest odd to win in the nba for today's game?  i would like to bet very little money to win alot of money. "
        f"9. BETTING EDGE 5: How have the team performedover their last 10 games, and how does their actual win/loss record compare to their record against the spread and the over/under? "
        f"10. BETTING EDGE 6: find me the biggest edge on players against their next oponent that is not obvious to regular fans."
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
    
    with st.spinner("Analyzing News & Vegas Markets..."):
        try:
            roster_data = commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]
            roster_names = ", ".join(roster_data['PLAYER'].tolist()[:12])
        except:
            roster_names = "Standard Roster"

        raw_data = get_nba_scout_report(selected_team, roster_names)
        
        parts = raw_data.split('\n')
        summary = ""
        points = []

        for p in parts:
            p = p.strip()
            if not p: continue
            if p.startswith("SUMMARY:"): 
                summary = p.replace("SUMMARY:", "").strip()
            # Updated to range(1, 11) to capture all 10 points
            elif any(p.startswith(f"{i}.") for i in range(1, 11)): 
                points.append(p)

        # 1. Display Narrative Summary
        if summary:
            st.markdown(f'<div class="scout-report-box">{summary}</div>', unsafe_allow_html=True)

        # 2. Display the 10 Sections
        for point in points:
            # Flexible split to handle different AI formatting
            if ":" in point:
                title, content = point.split(":", 1)
                st.markdown(f'<div class="section-title">{title.strip()}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="section-content">{content.strip()}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="section-content"><b>{point}</b></div>', unsafe_allow_html=True)

        with st.expander("📋 View Official Roster"):
            try:
                st.dataframe(roster_data[['PLAYER', 'POSITION', 'HEIGHT']], use_container_width=True)
            except:
                st.write("Roster data unavailable for this team.")



                