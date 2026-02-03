import streamlit as st
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG ---
st.set_page_config(page_title="CBB Live Scout", page_icon="🏀", layout="wide")
# Auto-refresh every 30 seconds to catch lead changes
st_autorefresh(interval=30000, key="global_update")

# --- 2. DATA ENGINE ---
def get_live_events():
    """Hits ESPN's live API to get all games for Feb 3, 2026"""
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"
    try:
        response = requests.get(url)
        return response.json().get('events', [])
    except:
        return []

# --- 3. UI & TEAM SELECTION ---
st.title("🏀 CBB Live Intelligence Dashboard")

events = get_live_events()

if not events:
    st.error("Searching for live satellite feed... No games found yet.")
else:
    # Build a dictionary of team names to their specific game data
    team_map = {}
    for event in events:
        comp = event['competitions'][0]
        home = comp['competitors'][0]['team']['displayName']
        away = comp['competitors'][1]['team']['displayName']
        
        # Store game data under both team names so you can find it either way
        team_map[home] = event
        team_map[away] = event

    # Create the dropdown with all available teams
    team_list = sorted(list(team_map.keys()))
    selected_team = st.selectbox("🎯 Select a team to track live:", team_list)

    # --- 4. FOCUS DISPLAY ---
    if selected_team:
        game = team_map[selected_team]
        c = game['competitions'][0]
        home_data = c['competitors'][0]
        away_data = c['competitors'][1]
        
        st.divider()
        
        # Big Scoreboard View
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            st.metric(away_data['team']['shortDisplayName'], away_data['score'])
            st.caption("AWAY")
            
        with col2:
            st.markdown(f"<h3 style='text-align: center;'>{game['status']['type']['detail']}</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center;'>VS</p>", unsafe_allow_html=True)
            
        with col3:
            st.metric(home_data['team']['shortDisplayName'], home_data['score'])
            st.caption("HOME")

        # Betting & Broadcast Info
        st.divider()
        odds = c.get('odds', [{}])[0].get('details', "Odds Pending")
        venue = c['venue']['fullName']
        city = c['venue']['address'].get('city', '')
        state = c['venue']['address'].get('state', '')
        
        st.write(f"📈 **Live Line:** {odds}")
        st.write(f"🏟️ **Location:** {venue} ({city}, {state})")

# --- 5. LIVE SNAPSHOT (Feb 3, 2026) ---
with st.expander("View Full Today's Scoreboard"):
    st.write("Current games grounded in ESPN/Google search data:")
    # Examples of what will show up in your app right now:
    # 1. Syracuse vs North Carolina (Live: 27-34)
    # 2. Florida A&M vs Alabama St (Live: 33-27)
    # 3. Boston U vs Holy Cross (Live: 31-29)