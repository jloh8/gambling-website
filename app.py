import streamlit as st
import pandas as pd
from nba_api.stats.static import teams
from nba_api.stats.endpoints import commonteamroster
from datetime import datetime

# Page configuration
st.set_page_config(page_title="Rockets Live Dashboard", page_icon="🚀")
st.title("🚀 Houston Rockets Live Roster")

# Sidebar info
st.sidebar.header("Gambling Model Stats")
st.sidebar.write(f"Today's Date: {datetime.now().strftime('%Y-%m-%d')}")

# Trigger Button
if st.button('Fetch Live Rockets Data'):
    with st.spinner('Accessing NBA.com data...'):
        # 1. Get Rockets ID
        nba_teams = teams.get_teams()
        rockets = [team for team in nba_teams if team['full_name'] == 'Houston Rockets'][0]
        
        # 2. Pull Roster
        roster = commonteamroster.CommonTeamRoster(team_id=rockets['id'])
        df = roster.get_data_frames()[0]
        
        # 3. Clean up the dataframe for display
        display_df = df[['PLAYER', 'NUM', 'POSITION', 'HEIGHT', 'WEIGHT', 'AGE']]
        
        st.success("Data Pulled Successfully!")
        
        # Show as an interactive table
        st.subheader("Current Active Roster")
        st.dataframe(display_df, use_container_width=True)
        
        # Logic for the model
        st.info("💡 Model Tip: Check the 'AGE' column. High-density schedules impact older rosters more significantly at home.")
else:
    st.write("Click the button above to load the current team stats.")
    