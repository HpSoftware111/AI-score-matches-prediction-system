"""
Text parser for importing match data from formatted text
"""
import re
from datetime import datetime
from dateutil import parser as date_parser
from .models import Team, Match


def american_to_decimal(american_odds):
    """
    Convert American odds to decimal odds
    +600 -> 7.00 (6:1 + 1)
    -190 -> 1.526 (100/190 + 1)
    """
    try:
        american_odds = str(american_odds).strip()
        if american_odds.startswith('+'):
            # Positive odds: +600 means bet $100 to win $600
            # Decimal = (american_odds / 100) + 1
            return round((int(american_odds[1:]) / 100) + 1, 3)
        elif american_odds.startswith('-'):
            # Negative odds: -190 means bet $190 to win $100
            # Decimal = (100 / |american_odds|) + 1
            return round((100 / abs(int(american_odds[1:]))) + 1, 3)
        else:
            # Try to parse as decimal if no +/- sign
            return float(american_odds)
    except (ValueError, AttributeError, TypeError):
        return None


def parse_match_text_ligue1_format(text):
    """
    Parse Ligue 1 format (tab-separated):
    Ligue 1	Metz	Metz	34%
    34%34%
    Fri, 28 Nov 20:45	Draw	28%
    28%28%
    Stade Saint-Symphorien	Rennes	Rennes	38%
    38%38%
    Forecast:	Could go either way
    """
    matches_data = []
    lines = text.strip().split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        
        # Skip header lines
        if line.startswith('INFO') or line.startswith('TEAMS') or line.startswith('FORECAST'):
            i += 1
            continue
        
        # Split by tabs first (most common separator in this format)
        if '\t' in line:
            parts = line.split('\t')
        else:
            # Fall back to multiple spaces
            parts = re.split(r'\s{2,}', line)
        parts = [p.strip() for p in parts if p.strip()]
        
        if not parts:
            i += 1
            continue
        
        # Look for league name pattern at start (including "Prem" abbreviation)
        league_pattern = r'(Ligue 1|EPL|PL|Prem|Premier League|La Liga|Serie A|Bundesliga|League 1|League One|Champ\.|Championship)'
        league_match = None
        game_title = None
        country = None
        
        # Check first few parts for league name
        for part in parts[:3]:
            league_match = re.search(league_pattern, part, re.IGNORECASE)
            if league_match:
                game_title = league_match.group(1)
                # Normalize "Prem" to "Premier League"
                if game_title.lower() == 'prem':
                    game_title = 'Premier League'
                if 'Ligue 1' in game_title:
                    country = 'France'
                elif 'EPL' in game_title or 'Premier League' in game_title or 'Prem' in game_title:
                    country = 'England'
                    if game_title.lower() == 'prem':
                        game_title = 'Premier League'
                elif 'League 1' in game_title or 'League One' in game_title:
                    country = 'England'
                    game_title = 'League One'
                elif 'Champ' in game_title or 'Championship' in game_title:
                    country = 'England'
                    game_title = 'Championship'
                elif 'La Liga' in game_title:
                    country = 'Spain'
                elif 'Serie A' in game_title:
                    country = 'Italy'
                elif 'Bundesliga' in game_title:
                    country = 'Germany'
                break
        
        # Also check the raw line
        if not league_match:
            league_match = re.search(league_pattern, line, re.IGNORECASE)
            if league_match:
                game_title = league_match.group(1)
                # Normalize "Prem" to "Premier League"
                if game_title.lower() == 'prem':
                    game_title = 'Premier League'
                if 'Ligue 1' in game_title:
                    country = 'France'
                elif 'EPL' in game_title or 'Premier League' in game_title or 'Prem' in game_title:
                    country = 'England'
                    if game_title.lower() == 'prem':
                        game_title = 'Premier League'
        
        if league_match and game_title:
            team_a_data = {'name': '', 'prob': None}
            team_b_data = {'name': '', 'prob': None}
            draw_prob = None
            match_date = None
            
            # Extract Team A from first line: League TeamA TeamA Prob%
            # Format: Prem | Premier League | Bournemouth | Bournemouth | 45%
            # Or: Premier League | Bournemouth | Bournemouth | 45%
            prob_matches = re.findall(r'(\d+)%', line)
            if prob_matches and len(parts) >= 3:
                # Find all league-related parts (Prem, Premier League, etc.)
                league_indices = []
                for idx, part in enumerate(parts):
                    if re.search(league_pattern, part, re.IGNORECASE):
                        league_indices.append(idx)
                
                # Find the percentage index
                prob_idx = None
                for j, part in enumerate(parts):
                    if re.search(r'\d+%', part):
                        prob_idx = j
                        break
                
                if prob_idx is not None and prob_idx > 0:
                    # Team name should be after all league parts, before percentage
                    # Skip all league-related parts
                    start_idx = max(league_indices) + 1 if league_indices else 0
                    
                    # Look for team name between start_idx and prob_idx
                    # In format "Prem | Premier League | Team | Team | Prob%", team is first non-league part
                    team_name = None
                    for k in range(start_idx, prob_idx):
                        part_clean = parts[k].strip()
                        if (part_clean and 
                            not re.search(r'%|\d', part_clean) and 
                            len(part_clean) > 1 and
                            part_clean.lower() not in ['draw', 'forecast', 'could', 'go', 'either', 'way', 
                                                       'leaning', 'backing'] and
                            not re.search(league_pattern, part_clean, re.IGNORECASE)):
                            # Found potential team name (first occurrence)
                            if team_name is None:
                                team_name = part_clean
                            # If duplicate, use first one
                            elif team_name.lower() == part_clean.lower():
                                break
                    
                    if team_name:
                        team_a_data['name'] = team_name
                        team_a_data['prob'] = int(prob_matches[0]) / 100
            
            # Read next lines for date, draw prob, and team B
            i += 1
            found_date = False
            found_draw = False
            
            while i < len(lines):
                current_line = lines[i].strip()
                if not current_line:
                    i += 1
                    continue
                
                # Skip lines with only percentages (including duplicates like "45%45%" or "45%	45%")
                # Match lines that contain only digits, %, spaces, and tabs
                if re.match(r'^[\d%\s\t]+\s*$', current_line) and re.search(r'\d+%', current_line):
                    # Check if it's just percentage duplicates (no other meaningful text)
                    clean_line = current_line.replace('\t', ' ').strip()
                    if re.match(r'^[\d%\s]+$', clean_line):
                        i += 1
                        continue
                
                # Skip forecast lines and TV channel lines
                # Forecast lines may start with "Forecast:" prefix or directly with forecast text
                if (current_line.lower().startswith('forecast:') or 
                    'Sky Sports' in current_line or 
                    'Disney+' in current_line or
                    'Hotstar' in current_line or
                    'SuperSport' in current_line or
                    'MultiSports' in current_line or
                    'VOYO' in current_line or
                    'TNT Sports' in current_line or
                    'V Sport' in current_line or
                    'Arena Sport' in current_line or
                    'Universo' in current_line or
                    'Stöð 2 Sport' in current_line or
                    current_line.lower().startswith('leaning') or
                    current_line.lower().startswith('backing') or
                    'could go either way' in current_line.lower()):
                    i += 1
                    continue
                
                current_parts = current_line.split('\t') if '\t' in current_line else re.split(r'\s{2,}', current_line)
                current_parts = [p.strip() for p in current_parts if p.strip()]
                
                # Look for date pattern: "Fri, 28 Nov 20:45"
                date_pattern = r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s+(\d{1,2})\s+([A-Z][a-z]{2})\s+(\d{1,2}):(\d{2})'
                date_match = re.search(date_pattern, current_line)
                
                if date_match and not found_date:
                    try:
                        day_name, day, month, hour, minute = date_match.groups()
                        month_map = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                                   'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
                        current_year = datetime.now().year
                        # Handle year rollover if month is in the past
                        if month_map.get(month, 11) < datetime.now().month:
                            current_year += 1
                        match_date = datetime(current_year, month_map.get(month, 11), int(day), int(hour), int(minute))
                        found_date = True
                    except Exception as e:
                        pass
                
                # Look for "Draw" and percentage
                if ('Draw' in current_line or 'draw' in current_line.lower()) and not found_draw:
                    draw_prob_match = re.search(r'(\d+)%', current_line)
                    if draw_prob_match:
                        draw_prob = int(draw_prob_match.group(1)) / 100
                        found_draw = True
                
                # Look for second team (usually after stadium name)
                # Stadium indicators (French and English)
                stadium_indicators = ['Stade', 'Stadium', 'Orange', 'Velodrome', 'Groupama', 'Raymond', 'Kopa', 
                                    'Jean-Bouin', 'du Moustoir', 'de la Meinau', 'Louis II', 'Oceane',
                                    'Vitality', 'Craven', 'Cottage', 'St James', 'Park', 'American Express',
                                    'Turf Moor', 'Emirates', 'Molineux', 'Elland Road', 'Anfield', 'Old Trafford',
                                    'Stamford Bridge', 'Etihad', 'White Hart Lane', 'Goodison', 'Villa Park',
                                    'Tottenham Hotspur', 'Community Stadium', 'Stadium of Light', 'Hill Dickinson',
                                    'Selhurst', 'City Ground', 'London Stadium', 'Brentford Community']
                is_stadium = any(ind in current_line for ind in stadium_indicators)
                
                if len(current_parts) >= 2 and not team_b_data['name']:
                    # Look for team name and percentage
                    # Format: Stadium | Team | Team | Prob%  or  Team | Team | Prob%
                    prob_matches = re.findall(r'(\d+)%', current_line)
                    if prob_matches:
                        # Find percentage index
                        prob_idx = None
                        for j, part in enumerate(current_parts):
                            if re.search(r'\d+%', part):
                                prob_idx = j
                                break
                        
                        if prob_idx is not None and prob_idx > 0:
                            # Find team name before percentage
                            # Skip stadium if present (usually first part)
                            start_idx = 0
                            if is_stadium and len(current_parts) > 1:
                                start_idx = 1
                            
                            # Look for team name between start_idx and prob_idx
                            # In format "Stadium Team Team Prob%", team is at start_idx+1
                            # In format "Team Team Prob%", team is at start_idx
                            team_name = None
                            for k in range(start_idx, prob_idx):
                                part_clean = current_parts[k].strip()
                                if (part_clean and 
                                    not re.search(r'%|\d', part_clean) and 
                                    len(part_clean) > 1 and
                                    part_clean.lower() not in ['draw', 'forecast', 'could', 'go', 'either', 'way', 
                                                               'leaning', 'backing'] and
                                    not any(ind.lower() in part_clean.lower() for ind in stadium_indicators)):
                                    # Found potential team name
                                    if team_name is None:
                                        team_name = part_clean
                                    # If we find a duplicate, use the first one
                                    elif team_name.lower() == part_clean.lower():
                                        break  # Same team, use first occurrence
                            
                            if team_name and team_name.lower() != team_a_data['name'].lower():
                                team_b_data['name'] = team_name
                                team_b_data['prob'] = int(prob_matches[0]) / 100
                
                # Check if we have all data or hit next match
                if team_a_data['name'] and team_b_data['name'] and team_a_data['prob'] and team_b_data['prob'] and match_date:
                    # Calculate draw probability if not found
                    if draw_prob is None:
                        draw_prob = max(0, 1 - team_a_data['prob'] - team_b_data['prob'])
                    
                    # Calculate week number
                    week_number = match_date.isocalendar()[1]
                    
                    # Create match data
                    matches_data.append({
                        'team_a': team_a_data['name'],
                        'team_b': team_b_data['name'],
                        'date': match_date,
                        'prob_a': team_a_data['prob'],
                        'prob_b': team_b_data['prob'],
                        'odds_a': 2.0,  # Default odds (not provided in this format)
                        'odds_b': 2.0,  # Default odds (not provided in this format)
                        'draw_prob': draw_prob,
                        'week_number': week_number,
                        'country': country,
                        'game_title': game_title,
                    })
                    # Match completed - advance past forecast/TV line and break from inner loop
                    # Skip the forecast/TV line that comes after team B line
                    i += 1
                    # Skip any additional forecast/TV lines and percentage-only lines
                    while i < len(lines):
                        forecast_line = lines[i].strip()
                        if not forecast_line:
                            i += 1
                            continue
                        # Skip forecast/TV lines
                        if (forecast_line.lower().startswith('forecast:') or 
                             'Sky Sports' in forecast_line or 
                             'Disney+' in forecast_line or
                             'Hotstar' in forecast_line or
                             'SuperSport' in forecast_line or
                             'MultiSports' in forecast_line or
                             'VOYO' in forecast_line or
                             'TNT Sports' in forecast_line or
                             'V Sport' in forecast_line or
                             'Arena Sport' in forecast_line or
                             'Universo' in forecast_line or
                             'Stöð 2 Sport' in forecast_line or
                             forecast_line.lower().startswith('leaning') or
                             forecast_line.lower().startswith('backing') or
                             'could go either way' in forecast_line.lower()):
                            i += 1
                            continue
                        # Skip percentage-only lines
                        if re.match(r'^[\d%\s\t]+\s*$', forecast_line) and re.search(r'\d+%', forecast_line):
                            clean_line = forecast_line.replace('\t', ' ').strip()
                            if re.match(r'^[\d%\s]+$', clean_line):
                                i += 1
                                continue
                        # Stop when we hit a non-skippable line (could be next match or header)
                        break
                    # Now break to let outer loop continue from the correct position
                    break
                
                # Check if next line starts a new match (before we've completed current match)
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    # Skip header lines when checking for next match
                    if next_line and not (next_line.startswith('INFO') or next_line.startswith('TEAMS') or next_line.startswith('FORECAST')):
                        if re.search(league_pattern, next_line, re.IGNORECASE):
                            # Found next match, break to process it in next iteration
                            break
                
                i += 1
            
            # After breaking from inner loop, explicitly continue outer loop
            # This ensures we process the next line/match
            continue
        else:
            i += 1
    
    return matches_data


def parse_match_text(text):
    """
    Parse text input and extract match information
    Supports multiple formats:
    1. Original format: Date -> Team A (duplicate) -> Prob A -> Odds A -> Team B (duplicate) -> Prob B -> Odds B
    2. Ligue 1 format: League Team Team Prob% -> Date Draw Prob% -> Stadium Team Team Prob%
    Returns list of dictionaries with match data
    """
    # Try Ligue 1 format first
    ligue1_data = parse_match_text_ligue1_format(text)
    if ligue1_data:
        return ligue1_data
    
    # Fall back to original format
    matches_data = []
    lines = text.strip().split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for date pattern: "Nov 29, 10:00 AM ET" or "Nov 23, 9:00 AM ET"
        date_pattern = r'([A-Z][a-z]{2}\s+\d{1,2},\s+\d{1,2}:\d{2}\s+[AP]M\s+ET)'
        date_match = re.search(date_pattern, line)
        
        if date_match:
            date_str = date_match.group(1)
            try:
                # Parse date: "Nov 29, 10:00 AM ET" -> datetime
                current_year = datetime.now().year
                date_str_clean = date_str.replace(' ET', '')
                try:
                    match_date = date_parser.parse(f"{date_str_clean}, {current_year}")
                except:
                    match_date = date_parser.parse(date_str_clean, fuzzy=True)
            except Exception as e:
                i += 1
                continue
            
            # Skip to next lines to find teams
            i += 1
            team_a_data = {'name': '', 'prob': None, 'odds': None}
            team_b_data = {'name': '', 'prob': None, 'odds': None}
            
            # Track game title and country
            game_title = None
            country = None
            
            # Common league abbreviations
            league_abbrevs = ['EPL', 'PL', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1', 'MLS', 
                             'Champions League', 'Europa League', 'FA Cup', 'EFL', 'Championship',
                             'League One', 'League Two', 'Premier League', 'Primera Division']
            
            # Sportsbook names to skip
            sportsbooks = ['BetRivers', 'BetMGM', 'DraftKings', 'FanDuel', 'Rivers', 'MGM', 'Kings', 'Draft', 'Fan', 'Bet']
            
            # State machine: 'looking_for_team_a', 'team_a_data', 'looking_for_team_b', 'team_b_data', 'complete'
            state = 'looking_for_team_a'
            last_seen_team_name = None
            
            # Collect lines until we hit next date or end
            while i < len(lines) and not re.search(date_pattern, lines[i]):
                current_line = lines[i].strip()
                
                # Extract game title (league name) - common abbreviations
                if not game_title:
                    for abbrev in league_abbrevs:
                        if abbrev.upper() == current_line.upper():
                            game_title = current_line
                            if state == 'complete':
                                break  # Found everything, can exit
                            break
                
                # Skip empty lines and non-relevant lines
                if (not current_line or 
                    current_line.startswith('See') or 
                    current_line == 'FINAL' or
                    current_line in ['Upcoming', '2025'] or
                    current_line.isdigit()):
                    i += 1
                    continue
                
                # Skip if it's a sportsbook name
                is_sportsbook = any(sb.lower() in current_line.lower() for sb in sportsbooks)
                if is_sportsbook:
                    i += 1
                    continue
                
                # Check if this looks like a team name (not a percentage, not odds, not sportsbook)
                is_team_name = (not re.search(r'%|\+|\-', current_line) and 
                               len(current_line) > 1 and 
                               not current_line.isdigit() and
                               not any(sb.lower() in current_line.lower() for sb in sportsbooks))
                
                # State machine logic
                if state == 'looking_for_team_a':
                    if is_team_name:
                        # First team name found
                        team_a_data['name'] = current_line
                        last_seen_team_name = current_line.lower()
                        state = 'team_a_data'
                elif state == 'team_a_data':
                    # Skip duplicate team name (e.g., "Everton" appears again) - ignore it
                    if is_team_name and current_line.lower() == last_seen_team_name:
                        # This is a duplicate, skip this line
                        i += 1
                        continue
                    
                    # Looking for team A's percentage and odds
                    prob_match = re.search(r'(\d+)%', current_line)
                    if prob_match and team_a_data['prob'] is None:
                        team_a_data['prob'] = int(prob_match.group(1)) / 100
                    
                    odds_match = re.search(r'([+-]\d+)', current_line)
                    if odds_match and team_a_data['odds'] is None:
                        team_a_data['odds'] = american_to_decimal(odds_match.group(1))
                    
                    # If we have both prob and odds for team A, move to looking for team B
                    if team_a_data['prob'] is not None and team_a_data['odds'] is not None:
                        state = 'looking_for_team_b'
                elif state == 'looking_for_team_b':
                    if is_team_name:
                        # Check it's not a duplicate of team A or last seen team
                        if (current_line.lower() != team_a_data['name'].lower() and 
                            current_line.lower() != last_seen_team_name):
                            # This is team B (new, different team)
                            team_b_data['name'] = current_line
                            last_seen_team_name = current_line.lower()
                            state = 'team_b_data'
                elif state == 'team_b_data':
                    # Skip duplicate team name - ignore it
                    if is_team_name and current_line.lower() == last_seen_team_name:
                        # This is a duplicate, skip this line
                        i += 1
                        continue
                    
                    # Looking for team B's percentage and odds
                    prob_match = re.search(r'(\d+)%', current_line)
                    if prob_match and team_b_data['prob'] is None:
                        team_b_data['prob'] = int(prob_match.group(1)) / 100
                    
                    odds_match = re.search(r'([+-]\d+)', current_line)
                    if odds_match and team_b_data['odds'] is None:
                        team_b_data['odds'] = american_to_decimal(odds_match.group(1))
                    
                    # If we have both prob and odds for team B, we're complete
                    if team_b_data['prob'] is not None and team_b_data['odds'] is not None:
                        state = 'complete'
                
                # If complete and found game title, we can exit
                if state == 'complete' and game_title:
                    break
                
                i += 1
            
            # Create match data if we have all required fields
            if (team_a_data['name'] and team_b_data['name'] and 
                team_a_data['prob'] is not None and team_b_data['prob'] is not None):
                
                # Skip if both teams are the same
                if team_a_data['name'].strip().lower() == team_b_data['name'].strip().lower():
                    i += 1
                    continue
                
                # Calculate draw probability (remainder to 100%)
                draw_prob = max(0, 1 - team_a_data['prob'] - team_b_data['prob'])
                
                # Infer country from game_title if not set
                if not country and game_title:
                    country_map = {
                        'EPL': 'England', 'PL': 'England', 'Premier League': 'England',
                        'La Liga': 'Spain', 'Primera Division': 'Spain',
                        'Serie A': 'Italy',
                        'Bundesliga': 'Germany',
                        'Ligue 1': 'France',
                        'MLS': 'USA',
                        'Champions League': 'Europe', 'Europa League': 'Europe',
                        'FA Cup': 'England', 'EFL': 'England', 'Championship': 'England',
                        'League One': 'England', 'League Two': 'England'
                    }
                    country = country_map.get(game_title, None)
                
                # Calculate week number from date
                week_number = match_date.isocalendar()[1] if match_date else None
                
                matches_data.append({
                    'team_a': team_a_data['name'],
                    'team_b': team_b_data['name'],
                    'date': match_date,
                    'prob_a': team_a_data['prob'],
                    'prob_b': team_b_data['prob'],
                    'odds_a': team_a_data['odds'] or 2.0,  # Default if not found
                    'odds_b': team_b_data['odds'] or 2.0,  # Default if not found
                    'draw_prob': draw_prob,
                    'week_number': week_number,
                    'country': country,
                    'game_title': game_title,
                })
        else:
            i += 1
    
    return matches_data


def import_matches_from_text(text, skip_duplicates=True):
    """
    Import matches from parsed text
    Returns (created_count, errors, warnings)
    """
    matches_data = parse_match_text(text)
    created_count = 0
    errors = []
    warnings = []
    
    for match_data in matches_data:
        try:
            # Validate teams are different
            if match_data['team_a'].strip().lower() == match_data['team_b'].strip().lower():
                errors.append(f"Invalid match: {match_data['team_a']} vs {match_data['team_b']} - teams cannot be the same")
                continue
            
            # Get or create teams
            team_a, _ = Team.objects.get_or_create(name=match_data['team_a'])
            team_b, _ = Team.objects.get_or_create(name=match_data['team_b'])
            
            # Double-check they're different (in case of case-insensitive matching)
            if team_a.id == team_b.id:
                errors.append(f"Invalid match: {match_data['team_a']} vs {match_data['team_b']} - teams cannot be the same")
                continue
            
            # Check for duplicates
            if skip_duplicates:
                existing = Match.objects.filter(
                    team_a=team_a,
                    team_b=team_b,
                    date__date=match_data['date'].date()
                ).exists()
                
                if existing:
                    warnings.append(f"Duplicate skipped: {match_data['team_a']} vs {match_data['team_b']} on {match_data['date'].date()}")
                    continue
            
            # Create match
            Match.objects.create(
                team_a=team_a,
                team_b=team_b,
                date=match_data['date'],
                prob_a=match_data['prob_a'],
                prob_b=match_data['prob_b'],
                odds_a=match_data['odds_a'],
                odds_b=match_data['odds_b'],
                draw_prob=match_data['draw_prob'],
                week_number=match_data.get('week_number'),
                country=match_data.get('country'),
                game_title=match_data.get('game_title'),
            )
            created_count += 1
            
        except Exception as e:
            errors.append(f"Error creating {match_data.get('team_a', '?')} vs {match_data.get('team_b', '?')}: {str(e)}")
    
    return created_count, errors, warnings

