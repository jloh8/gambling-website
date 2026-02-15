import sqlite3
import time
from datetime import datetime
from nba_api.stats.static import teams
from nba_api.stats.endpoints import commonteamroster
from google import genai
import os
from prompts import get_scout_report_prompt
from dotenv import load_dotenv

load_dotenv() # This looks for a .env file in your folder

# Client Setup
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def update_all_teams():
    conn = sqlite3.connect('nba_intel.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS reports (team TEXT, report_date TEXT, content TEXT, PRIMARY KEY (team, report_date))')
    
    all_nba_teams = teams.get_teams()
    today = datetime.now().strftime("%Y-%m-%d")
    
    for team_info in all_nba_teams:
        team_name = team_info['full_name']
        print(f"Updating {team_name}...")
        
        try:
            # Get roster for context
            roster = commonteamroster.CommonTeamRoster(team_id=team_info['id']).get_data_frames()[0]
            player_names = ", ".join(roster['PLAYER'].head(10).tolist())
            
            # Get Gemini result
            prompt = get_scout_report_prompt(team_name, today, player_names)
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            
            # Save to DB
            c.execute("INSERT OR REPLACE INTO reports VALUES (?, ?, ?)", (team_name, today, response.text))
            conn.commit()
            
            # Small delay to avoid API rate limits
            time.sleep(2) 
        except Exception as e:
            print(f"Skipped {team_name}: {e}")

    conn.close()

if __name__ == "__main__":
    update_all_teams()