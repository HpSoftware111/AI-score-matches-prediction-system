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


def parse_match_text(text):
    """
    Parse text input and extract match information
    Pattern: Date -> Team A (duplicate) -> Prob A -> Odds A -> Team B (duplicate) -> Prob B -> Odds B
    Returns list of dictionaries with match data
    """
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

