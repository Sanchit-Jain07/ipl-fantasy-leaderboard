import streamlit as st
import json
from util import SQUADS, D11_TEAMS, RESTRICTED_TEAMS
import re
# Load points data
with open("points.json", "r") as f:
    points_data = json.load(f)

teams = SQUADS
d11_teams = D11_TEAMS
restricted_teams = RESTRICTED_TEAMS
# Compute team scores
team_scores = {
    team: (
        sum(int(points_data.get(player, 0)) for player in players),
        sum(int(points_data.get(player, 0)) * 1 for player in D11_TEAMS.get(team, [])['Captain']) +
        sum(int(points_data.get(player, 0)) * .5 for player in D11_TEAMS.get(team, [])['Vice Captain'])+
        sum(int(points_data.get(player, 0)) for player in D11_TEAMS.get(team, [])['Team']),
        sum(int(points_data.get(player, 0)) * 1 for player in RESTRICTED_TEAMS.get(team, [])['Captain']) +
        sum(int(points_data.get(player, 0)) * .5 for player in RESTRICTED_TEAMS.get(team, [])['Vice Captain'])+
        sum(int(points_data.get(player, 0)) for player in RESTRICTED_TEAMS.get(team, [])["Team"])
    )
    for team, players in teams.items()
}
# Sort teams by total points
top_teams = sorted(team_scores.items(), key=lambda x: x[1], reverse=True)

st.title("🏏 Fantasy IPL Team Leaderboards")

with open("completed_matches.txt", "r") as f:
    lines = f.readlines()
    if lines:
        # Extract match number and teams from the URL
        def extract_match_details(url):
            match = re.search(r'([a-z]+)-vs-([a-z]+)-(\d+)', url)
            if match:
                match_number = match.group(3)
                team1 = match.group(1).upper()
                team2 = match.group(2).upper()
                return match_number, team1, team2
            return None, None, None

        # Example usage
        last_match_url = lines[-1].strip()
        match_number, team1, team2 = extract_match_details(last_match_url)

        st.markdown(f"### Last Match Updated:")
        st.markdown(f"Match {match_number}: **{team1}** vs **{team2}**")

for team, total_points in top_teams:
    st.markdown(f"<h2 style='font-size:24px'>Team {team} - Total Points: {total_points}</h2>", unsafe_allow_html=True)
    with st.expander(f"{team} Full Squad Leaderboard"):
        team_players = {player: points_data.get(player, 0) for player in teams[team] if player in points_data}
        sorted_team_players = sorted(team_players.items(), key=lambda x: int(x[1]), reverse=True)
        
        for i, (player, points) in enumerate(sorted_team_players, 1):
            st.markdown(
                f"<div style= 'padding: 5px;  border-radius: 10px;'>"
                f"<b>{i}. {player}</b> : {points} Points</div>",
                unsafe_allow_html=True,
            )
    with st.expander(f"{team} D11 Leaderboard"):
        d11_players = {player: points_data.get(player, 0) for player in D11_TEAMS[team]['Team'] if player in points_data}
        sorted_d11_players = sorted(d11_players.items(), key=lambda x: int(x[1]), reverse=True)
        
        for i, (player, points) in enumerate(sorted_d11_players, 1):
            multiplier = 2 if player in D11_TEAMS[team]['Captain'] else 1.5 if player in D11_TEAMS[team]['Vice Captain'] else 1
            adjusted_points = points * multiplier
            role = " (Captain)" if player in D11_TEAMS[team]['Captain'] else " (Vice Captain)" if player in D11_TEAMS[team]['Vice Captain'] else ""
            st.markdown(
                f"<div style= 'padding: 5px;  border-radius: 10px;'>"
                f"<b>{i}. {player}{role}</b> : {adjusted_points} Points</div>",
                unsafe_allow_html=True,
            )
    with st.expander(f"{team} Restricted Players Leaderboard"):
        restricted_players = {player: points_data.get(player, 0) for player in RESTRICTED_TEAMS[team]['Team'] if player in points_data}
        sorted_restricted_players = sorted(restricted_players.items(), key=lambda x: int(x[1]), reverse=True)
        
        for i, (player, points) in enumerate(sorted_restricted_players, 1):
            multiplier = 2 if player in RESTRICTED_TEAMS[team]['Captain'] else 1.5 if player in RESTRICTED_TEAMS[team]['Vice Captain'] else 1
            adjusted_points = points * multiplier
            role = " (Captain)" if player in RESTRICTED_TEAMS[team]['Captain'] else " (Vice Captain)" if player in RESTRICTED_TEAMS[team]['Vice Captain'] else ""
            st.markdown(
                f"<div style= 'padding: 5px;  border-radius: 10px;'>"
                f"<b>{i}. {player}{role}</b> : {adjusted_points} Points</div>",
                unsafe_allow_html=True,
            )
