import sqlite3
import pandas as pd

def init_db():
    conn = sqlite3.connect('nba_intelligence.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS scout_reports
                 (team TEXT, date TEXT, summary TEXT, injuries TEXT, lineup TEXT, PRIMARY KEY (team, date))''')
    conn.commit()
    conn.close()

def save_report(team, date, report_data):
    conn = sqlite3.connect('nba_intelligence.db')
    c = conn.cursor()
    # Parsing the structured response from your prompt
    c.execute("INSERT OR REPLACE INTO scout_reports VALUES (?, ?, ?, ?, ?)", 
              (team, date, report_data['summary'], report_data['injuries'], report_data['lineup']))
    conn.commit()
    conn.close()