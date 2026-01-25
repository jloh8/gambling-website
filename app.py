import streamlit as st
import pandas as pd
from nba_api.stats.static import teams
from nba_api.stats.endpoints import commonteamroster, teamdashlineups
from datetime import datetime
from nbainjuries import injury

# --- PAGE CONFIG ---
st.set_page_config(page_title="NBA Gambling Model", page_icon="🏀", layout="wide")
st.title("🚀 NBA Team Intelligence Dashboard")
st.markdown("Analyze team rosters and starting lineups for home-game win probability.")

# --- DATA FETCHING FUNCTIONS ---
@st.cache_data
def get_team_list():
    all_teams = teams.get_teams()
    return {team['full_name']: team['id'] for team in all_teams}

def get_lineup_data(team_id):
    """Fetches 5-man lineup stats and safely identifies columns."""
    try:
        lineup_bundle = teamdashlineups.TeamDashLineups(
            team_id=team_id, 
            group_quantity=5, 
            season='2025-26'
        )
        # Index [1] contains the specific 5-man lineup groups
        df = lineup_bundle.get_data_frames()[1]
        return df
    except Exception as e:
        st.error(f"Error fetching lineup data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def get_current_injuries():
    """
    Fetches the most recent official NBA injury report.
    Returns DataFrame with all current injuries league-wide.
    """
    try:
        # Get the most recent injury report (current datetime)
        injury_df = injury.get_reportdata(datetime.now(), return_df=True)
        return injury_df
    except Exception as e:
        st.error(f"Error fetching injury data: {e}")
        return pd.DataFrame()

def get_injuries_for_team(team_name, injury_df):
    """
    Filter injury report for specific team.
    Returns list of injured player names.
    """
    if injury_df.empty:
        return []
    
    # Filter by team name
    team_injuries = injury_df[injury_df['Team'].str.contains(team_name, case=False, na=False)]
    
    # Get players who are Out or Doubtful (not just Questionable)
    serious_injuries = team_injuries[
        team_injuries['Current Status'].isin(['Out', 'Doubtful'])
    ]
    
    injured_players = serious_injuries['Player Name'].tolist()
    return injured_players

# --- SIDEBAR SELECTION ---
team_dict = get_team_list()
selected_team_name = st.sidebar.selectbox("Select Team", sorted(team_dict.keys()))
team_id = team_dict[selected_team_name]

# --- MAIN TABS ---
tab1, tab2, tab3 = st.tabs(["📋 Full Team Roster", "🔥 Starting 5 Analysis", "🩺 Hurt Players"])

# TAB 1: FULL ROSTER
with tab1:
    st.subheader(f"{selected_team_name} - Current Roster")
    if st.button('Pull Latest Roster'):
        with st.spinner('Accessing NBA.com...'):
            roster_data = commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]
            st.dataframe(roster_data[['PLAYER', 'NUM', 'POSITION', 'HEIGHT', 'AGE', 'EXP']], use_container_width=True)

# TAB 3: AUTO-UPDATED INJURIES FROM OFFICIAL NBA REPORTS
with tab3:
    st.subheader("🩺 Official NBA Injury Report")
    st.caption("Auto-updated from NBA's official injury reports (Out/Doubtful players only)")
    
    if st.button('Refresh Injury Report', type="primary"):
        with st.spinner('Fetching latest official NBA injury data...'):
            # Clear cache and fetch fresh data
            get_current_injuries.clear()
            injury_df = get_current_injuries()
            
            if not injury_df.empty:
                injured_players = get_injuries_for_team(selected_team_name, injury_df)
                
                if injured_players:
                    st.warning(f"**{len(injured_players)} player(s) currently out/doubtful:**")
                    
                    # Show detailed injury info
                    team_injury_data = injury_df[
                        (injury_df['Team'].str.contains(selected_team_name, case=False, na=False)) &
                        (injury_df['Current Status'].isin(['Out', 'Doubtful']))
                    ]
                    
                    for _, row in team_injury_data.iterrows():
                        status_emoji = "🔴" if row['Current Status'] == 'Out' else "🟡"
                        st.write(f"{status_emoji} **{row['Player Name']}** - {row['Current Status']}")
                        st.caption(f"   └─ {row['Reason']}")
                    
                    # Store in session state for Tab 2
                    st.session_state['hurt_players'] = injured_players
                    st.session_state['injury_details'] = team_injury_data.to_dict('records')
                else:
                    st.success("✅ No players currently listed as Out or Doubtful")
                    st.session_state['hurt_players'] = []
            else:
                st.error("Could not retrieve injury data. Please try again.")
    
    # Show cached injury data if available
    elif 'hurt_players' in st.session_state and st.session_state['hurt_players']:
        st.info(f"**Cached injury data ({len(st.session_state['hurt_players'])} player(s)):**")
        
        if 'injury_details' in st.session_state:
            for injury in st.session_state['injury_details']:
                status_emoji = "🔴" if injury['Current Status'] == 'Out' else "🟡"
                st.write(f"{status_emoji} **{injury['Player Name']}** - {injury['Current Status']}")
                st.caption(f"   └─ {injury['Reason']}")
        
        st.caption("Click 'Refresh Injury Report' to update from official NBA sources")
    else:
        st.info("Click 'Refresh Injury Report' to load current injuries from official NBA reports")

# TAB 2: STARTING 5 & GAMBLING LOGIC
with tab2:
    st.subheader("Projected Starting 5 (Most Frequent Lineup)")
    st.caption("This tab analyzes the 5-man unit with the most minutes played this season.")
    
    if st.button('Run Lineup Analysis'):
        lineups = get_lineup_data(team_id)
        
        if lineups.empty:
            st.warning("No consistent lineup data found for this team yet this season.")
        else:
            potential_cols = ['GROUP_NAME', 'GROUP_ID', 'GROUP_VALUE', 'group_name']
            name_col = next((c for c in potential_cols if c in lineups.columns), None)
            
            if name_col:
                top_lineup = lineups.iloc[0]
                players = str(top_lineup[name_col]).replace(' - ', ', ').split(', ')
                
                # Get injuries from session state
                hurt_players = st.session_state.get('hurt_players', [])
                
                # Fuzzy match injured players with lineup names
                injured_starters = []
                for starter in players:
                    for injured in hurt_players:
                        # Match on last name
                        starter_last = starter.split()[-1].lower()
                        injured_last = injured.split(',')[0].lower()  # "Butler, Jimmy" -> "butler"
                        if starter_last == injured_last:
                            injured_starters.append(starter)
                            break
                
                healthy_players = [p for p in players if p not in injured_starters]
                availability_pct = (len(healthy_players) / len(players)) * 100 if players else 0
                
                col_left, col_right = st.columns([1, 2])
                
                with col_left:
                    st.write("### The Starters")
                    for i, p in enumerate(players, 1):
                        mark = " 🔴 (OUT)" if p in injured_starters else ""
                        st.write(f"**{i}.** {p}{mark}")
                
                with col_right:
                    st.write("### 🎲 Model Insights")
                    win_pct = top_lineup['W_PCT'] * 100
                    plus_minus = top_lineup['PLUS_MINUS']
                    gp = top_lineup['GP']
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Win %", f"{win_pct:.1f}%")
                    m2.metric("+/- Score", plus_minus)
                    m3.metric("Games Together", int(gp))

                    a1, a2 = st.columns([1,2])
                    a1.metric("Starters Available %", f"{availability_pct:.0f}%")
                    if injured_starters:
                        a2.error(f"🔴 {len(injured_starters)} injured starter(s): {', '.join(injured_starters)}")

                    if len(healthy_players) < len(players):
                        st.error("🚨 **Betting signal suspended:** One or more starters are officially OUT. Re-evaluate when starters are healthy.")
                    else:
                        if win_pct > 55 and gp > 5:
                            st.success("✅ **Betting Signal:** This lineup is highly efficient. Strong Home-Win potential.")
                        elif win_pct < 45 and gp > 5:
                            st.error("🚨 **Betting Signal:** This lineup is a net-negative. Risk of Home-Loss is high.")
                        else:
                            st.info("⚖️ **Betting Signal:** Low sample size or average performance. Check injury report.")
            else:
                st.error("Lineup table found, but player names column is missing. Contact support.")