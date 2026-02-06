# prompts.py

# def get_variance_prompt(date, context_notes):
#     """Generates the prompt for the Scoring Variance engine."""
#     return f"""
#     Identify 8 healthy NBA players scoring significantly ABOVE their season average 
#     in the last 2 games and 8 healthy players scoring significantly BELOW. 
#     Exclude injuries/DNPs. 
    
#     Current Date: {date}
#     Context/Specifics: {context_notes}
    
#     CRITICAL: You must include the player's team in brackets after their name.
#     Example: "LeBron James [LAL]" or "Cooper Flagg [DAL]".
    
#     Return ONLY a raw JSON list in this exact format:
#     [
#       {{"p": "PLAYER NAME [TEAM]", "v": "+45%", "s": "UP", "desc": "Short summary"}}
#     ]
#     """




# prompts.py

def get_variance_prompt(date, context_notes):
    """Generates the prompt for the Scoring Variance engine."""
    return f"""
    Identify 8 healthy NBA players scoring significantly ABOVE their season average 
    in the last 2 games and 8 healthy players scoring significantly BELOW. 
    
    Current Date: {date}
    Context: {context_notes}
    
    MANDATORY FORMATTING RULE:
    Every player name MUST be followed by their full team name in square brackets.
    Example: "Luka Doncic [Dallas Mavericks]" or "Jayson Tatum [Boston Celtics]".
    
    Return ONLY a raw JSON list:
    [
      {{"p": "PLAYER NAME [FULL TEAM NAME]", "v": "+45%", "s": "UP", "desc": "Summary"}}
    ]
    """

# (get_scout_report_prompt remains the same)

def get_scout_report_prompt(team_name, date, roster_names):
    """Generates the prompt for the Team Scout engine."""
    return f"""
    Generate a professional scout report for the {team_name} on {date}.
    ROSTER CONTEXT: {roster_names}

    DO NOT use conversational filler. Format the response EXACTLY as follows:

    SUMMARY: A 3-sentence narrative about the team's current situation.
    1. INJURY STATUS: Detailed update on absences and impact (2 sentences).
    2. STARTING 5: Likely lineup based on today's news.
    3. FATIGUE FACTOR: Schedule analysis and lifestyle/travel factors.
    4. MARKET MOVEMENT: Trade rumors or internal friction.
    5. BETTING EDGE 1: Deep dive into team stakes.
    6. BETTING EDGE 2: The 'hidden' edge against next opponent.
    7. BETTING EDGE 3: give me some betting suggestions for this team against their oponent ex: feb 5th 2026 senguin's been heating up scoring higher than average, i then put a bet for him to score 15+ points which is pretty safe.
    8. BETTING EDGE 4: Most interesting low-odds value bet.
    9. BETTING EDGE 5: Last 10 games performance vs Spread and O/U.
    10. BETTING EDGE 6: Biggest player-specific matchup advantage.
    """