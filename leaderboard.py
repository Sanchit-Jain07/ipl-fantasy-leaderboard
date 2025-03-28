import requests, bs4
from util import NAME_MAP_3 as NAME_MAP
from regex import *
import json

BASE_URL = 'https://www.cricbuzz.com'
URL = 'https://www.cricbuzz.com/cricket-series/9237/indian-premier-league-2025/matches'
PLAYER_POINTS = {
    player: 0 for player in NAME_MAP
}

def standardize_name(name, mapping):
    name = remove_captain_and_wk.sub(r'\1', name)
    name = name.strip()
    for standard_name, variations in mapping.items():
        if name.lower() in [v.lower() for v in variations] or name.lower() == standard_name.lower():
            return standard_name
    return name  # If no match found, return as is

def check_finished(match):
    if match.find('a', class_ = 'cb-text-complete'):
        return True
    return False

def get_matches():
    res = requests.get(URL)
    soup = bs4.BeautifulSoup(res.text, 'html.parser')
    matches = soup.find_all('div', class_ = 'cb-series-matches')
    return matches

def get_full_name(player):
    res = requests.get(BASE_URL + player['href'])
    soup = bs4.BeautifulSoup(res.text, 'html.parser')
    full_name = soup.find('h1', class_ = 'cb-font-40').text
    return full_name

def get_filtered_matches(matches):
    return list(filter(check_finished, matches))

def get_scorecard_link(match):
    link = match.find('a', class_ = 'cb-text-complete')['href'].split('/')
    return f'{BASE_URL}/live-cricket-scorecard/' + '/'.join(link[2:])

def get_scorecard(match):
    res = requests.get(get_scorecard_link(match))
    soup = bs4.BeautifulSoup(res.text, 'html.parser')
    scorecard = soup.find_all('div', class_ = 'cb-col cb-col-100 cb-ltst-wgt-hdr')
    return scorecard

def calculate_batting_points(player, duck):
    points = 0
    runs = int(player['runs'])
    fours = int(player['fours'])
    sixes = int(player['sixes'])
    strike_rate = float(player['strike_rate'])
    balls = int(player['balls'])

    points += (runs * 1 + fours * 4 + sixes * 6)

    # Run Bonus
    if runs >= 25:
        points += 4
    if runs >= 50:
        points += 8
    if runs >= 75:
        points += 12
    if runs >= 100:
        points += 16

    if duck:
        points -= 2

    # Strike Rate Bonus
    if balls>= 10:
        if strike_rate >= 170:
            points += 6
        elif strike_rate >= 150:
            points += 4
        elif strike_rate >= 130:
            points += 2
        
        if strike_rate < 50:
            points -= 6
        elif strike_rate < 60:
            points -= 4
        elif strike_rate <= 70:
            points -= 2

    return points

def fielding_and_wicket_points(wickets):
    catch_count = {}

    for wicket in wickets:
        if bowled.match(wicket):
            bowler = bowled.match(wicket).group(1)
            bowler = standardize_name(bowler, NAME_MAP)
            if bowler not in PLAYER_POINTS:
                continue
            PLAYER_POINTS[bowler] += 8 # Bonus for bowled
    
        elif caught.match(wicket):
            fielder = caught.match(wicket).group(1)
            bowler = caught.match(wicket).group(2)
            fielder = standardize_name(fielder, NAME_MAP)
            bowler = standardize_name(bowler, NAME_MAP)
            
            if fielder in PLAYER_POINTS:
                PLAYER_POINTS[fielder] += 8
            # Track catches for the fielder
            if fielder not in catch_count:
                catch_count[fielder] = 0
            catch_count[fielder] += 1

        elif lbw.match(wicket):
            bowler = lbw.match(wicket).group(1)
            bowler = standardize_name(bowler, NAME_MAP)
            if bowler not in PLAYER_POINTS:
                continue
            PLAYER_POINTS[bowler] += 8 # Bonus for lbw

        elif st.match(wicket):
            fielder = st.match(wicket).group(1)
            bowler = st.match(wicket).group(2)
            fielder = standardize_name(fielder, NAME_MAP)
            bowler = standardize_name(bowler, NAME_MAP)
            if fielder in PLAYER_POINTS:
                PLAYER_POINTS[fielder] += 12 # 12 for stumping
    
        elif caught_and_bowled.match(wicket):
            bowler = caught_and_bowled.match(wicket).group(1)
            bowler = standardize_name(bowler, NAME_MAP)
            if bowler not in PLAYER_POINTS:
                continue
            PLAYER_POINTS[bowler] += 8
            
        elif run_out.match(wicket):
            fielder = run_out.match(wicket).group(1)
            fielder = standardize_name(fielder, NAME_MAP)
            if fielder in PLAYER_POINTS:
                PLAYER_POINTS[fielder] += 6 # atleast 6 points for run out
            if run_out.match(wicket).group(2):
                fielder = run_out.match(wicket).group(2)
                fielder = standardize_name(fielder, NAME_MAP)
                if fielder in PLAYER_POINTS:
                    PLAYER_POINTS[fielder] += 6
            else:
                if fielder in PLAYER_POINTS:
                    PLAYER_POINTS[fielder] += 6 # additional 6 points for direct hit

    # Add 3 catch bonus
    for fielder, count in catch_count.items():
        if count >= 3:
            if fielder in PLAYER_POINTS:
                PLAYER_POINTS[fielder] += 4 # Bonus for 3 or more catches

def calculate_bowling_points(player):
    
    points = 0
    overs = float(player['overs'])
    wickets = int(player['wickets'])
    economy = float(player['economy'])
    maidens = int(player['maidens'])
    name = player['name']
    points += wickets * 25

    if wickets >= 3:
        points += 4
    if wickets >= 4:
        points += 8
    if wickets >= 5:
        points += 12
    
    if overs >= 2:
        if economy <= 5:
            points += 6
        elif economy <= 6:
            points += 4
        elif economy <= 7:
            points += 2

        if economy > 12:
            points -= 6
        elif economy > 11:
            points -= 4
        elif economy > 10:
            points -= 2
    
    points += maidens * 12

    return points


def batting_points(scorecards):
    scorecards = [scorecards[0], scorecards[3]]
    for scorecard in scorecards:
        entry = scorecard.find_all('div', class_ = 'cb-col cb-col-100 cb-scrd-itms')
        player = {
            'name': None,
            'runs': None,
            'balls': None,
            'fours': None,
            'sixes': None,
            'strike_rate': None
        }
        for i in entry:
            name = i.find_all('a', class_ = 'cb-text-link') or [None]
            runs = i.find('div', class_ = 'cb-col cb-col-8 text-right text-bold')
            runs = runs.text if runs else None
            balls = i.find('div', class_ = 'cb-col cb-col-8 text-right')
            balls = balls.text if balls else None
            fours = i.find_all('div', class_ = 'cb-col cb-col-8 text-right')[1].text if len(i.find_all('div', class_ = 'cb-col cb-col-8 text-right')) > 1 else None
            sixes = i.find_all('div', class_ = 'cb-col cb-col-8 text-right')[2].text if len(i.find_all('div', class_ = 'cb-col cb-col-8 text-right')) > 2 else None
            strike_rate = i.find_all('div', class_ = 'cb-col cb-col-8 text-right')[3].text if len(i.find_all('div', class_ = 'cb-col cb-col-8 text-right')) > 3 else None
            if not all([name, runs, balls, fours, sixes, strike_rate]):
                continue
            not_out = i.find('span', class_ = 'text-gray').text if i.find('span', class_ = 'text-gray') else None
            duck = False
            player['name'] = standardize_name(name[0].text.strip(), NAME_MAP)
            player['runs'] = runs
            player['balls'] = balls
            player['fours'] = fours
            player['sixes'] = sixes
            player['strike_rate'] = strike_rate

            if(runs == '0' and not_out != 'not out'):
                duck = True

            if player['name'] in PLAYER_POINTS:
                PLAYER_POINTS[player['name']] += calculate_batting_points(player, duck)

def bowling_points(scorecards):
    scorecards = [scorecards[1], scorecards[4]]
    for scorecard in scorecards:
        entry = scorecard.find_all('div', class_ = 'cb-col cb-col-100 cb-scrd-itms')
        player = {
            'name': None,
            'overs': None,
            'maidens': None,
            'runs': None,
            'wickets': None,
            'economy': None
        }
        for i in entry:
            name = i.find_all('a', class_ = 'cb-text-link') or [None]
            overs = i.find('div', class_ = 'cb-col cb-col-8 text-right')
            overs = overs.text if overs else None
            maidens = i.find_all('div', class_ = 'cb-col cb-col-8 text-right')[1].text if len(i.find_all('div', class_ = 'cb-col cb-col-8 text-right')) > 1 else None
            runs = i.find_all('div', class_ = 'cb-col cb-col-10 text-right')[0].text if len(i.find_all('div', class_ = 'cb-col cb-col-10 text-right')) > 0 else None
            wickets = i.find_all('div', class_ = 'cb-col cb-col-8 text-right text-bold')[0].text if len(i.find_all('div', class_ = 'cb-col cb-col-8 text-right text-bold')) > 0 else None
            economy = i.find_all('div', class_ = 'cb-col cb-col-10 text-right')[1].text if len(i.find_all('div', class_ = 'cb-col cb-col-10 text-right')) > 1 else None
            if not all([name, overs, maidens, runs, wickets, economy]):
                continue
            
            player['name'] = standardize_name(name[0].text.strip(), NAME_MAP)
            player['overs'] = overs
            player['maidens'] = maidens
            player['runs'] = runs
            player['wickets'] = wickets
            player['economy'] = economy

            if player['name'] in PLAYER_POINTS:
                PLAYER_POINTS[player['name']] += calculate_bowling_points(player)
    
def fielding_points(scorecards):
    scorecards = [scorecards[0], scorecards[3]]
    for scorecard in scorecards:
        entry = scorecard.find_all('div', class_ = 'cb-col cb-col-100 cb-scrd-itms')
        wickets = []
        for i in entry:
            wicket = i.find('span', class_ = 'text-gray')
            if not wicket:
                continue
            wicket = wicket.text
            if wicket == 'not out':
                continue
            wickets.append(wicket)
        fielding_and_wicket_points(wickets)

def get_playing_players(match):
    scorecard_page = get_scorecard_link(match)
    res = requests.get(scorecard_page)
    soup = bs4.BeautifulSoup(res.text, 'html.parser')
    divs = soup.find_all('div', class_ = 'cb-col cb-col-100 cb-minfo-tm-nm')
    all_players = []
    for div in divs:
        child = div.find('div', class_ = 'cb-col cb-col-27', string = 'Playing') or div.find('div', class_ = 'cb-col cb-col-27', string = 'Bench')
        if not child:
            continue
        team = div.find_all('a', class_ = 'margin0 text-black text-hvr-underline')
        team = [NAME_MAP.get(i.text, i.text) for i in team]
        all_players.extend(team)
    return all_players

def update_leaderboard():
    matches = get_matches()
    finished_matches = get_filtered_matches(matches)
    COMPLETED_MATCHES = []
    with open('completed_matches.txt', 'r') as f:
        for line in f:
            COMPLETED_MATCHES.append(line.strip())

    for match in finished_matches:
        link = get_scorecard_link(match)
        if link in COMPLETED_MATCHES:
            continue
        scorecard = get_scorecard(match)
        batting_points(scorecard)
        bowling_points(scorecard)
        fielding_points(scorecard)
        COMPLETED_MATCHES.append(link)

    with open('completed_matches.txt', 'w') as f:
        for match in COMPLETED_MATCHES:
            f.write(match + '\n')

    with open('points.json', 'w') as f:
        json.dump(PLAYER_POINTS, f)
