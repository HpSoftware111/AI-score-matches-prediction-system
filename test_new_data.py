#!/usr/bin/env python
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'football_prediction_system.settings')
django.setup()

from matches.text_parser import parse_match_text_ligue1_format

test_data = """INFO	TEAMS	FORECAST
Prem	Premier League	Bournemouth	Bournemouth	45%
45%45%
Tue, 2 Dec 19:30	Draw	28%
28%28%
Vitality Stadium	Everton	Everton	27%
27%27%
Sky Sports+Disney+ Hotstar	Leaning Bournemouth
Prem	Premier League	Fulham	Fulham	20%
20%20%
Tue, 2 Dec 19:30	Draw	24%
24%24%
Craven Cottage	Manchester City	Man City	56%
56%56%
Sky Sports Main EventDisney+ Hotstar	Leaning Manchester City
League 1	League One	Wigan	Wigan	49%
49%49%
Tue, 2 Dec 19:45	Draw	27%
27%27%
The Brick Community Stadium	Burton	Burton	24%
24%24%
Forecast:	Leaning Wigan
Champ.	Championship	Blackburn	Blackburn	34%
34%34%
Tue, 2 Dec 19:45	Draw	29%
29%29%
Ewood Park	Ipswich Town	Ipswich	37%
37%37%
Sky Sports+	Could go either way
Prem	Premier League	Newcastle	Newcastle	58%
58%58%
Tue, 2 Dec 20:15	Draw	24%
24%24%
St James Park	Tottenham	Tottenham	18%
18%18%
Sky Sports+Sky Sports Premier League	Backing Newcastle
Prem	Premier League	Brighton	Brighton	38%
38%38%
Wed, 3 Dec 19:30	Draw	29%
29%29%
American Express Stadium	Aston Villa	Aston Villa	33%
33%33%
Sky Sports CricketDisney+ Hotstar	Could go either way
INFO	TEAMS	FORECAST
Prem	Premier League	Burnley	Burnley	33%
33%33%
Wed, 3 Dec 19:30	Draw	28%
28%28%
Turf Moor	Crystal Palace	Palace	39%
39%39%
Sky Sports+Disney+ Hotstar	Could go either way
Prem	Premier League	Arsenal	Arsenal	67%
67%67%
Wed, 3 Dec 19:30	Draw	19%
19%19%
Emirates Stadium	Brentford	Brentford	14%
14%14%
Sky Sports FootballSky Sports Main Event	Backing Arsenal
Prem	Premier League	Wolves	Wolves	27%
27%27%
Wed, 3 Dec 19:30	Draw	27%
27%27%
Molineux Stadium	Nottingham Forest	Notts Forest	46%
46%46%
Sky Sports F1 HDVOYO	Leaning Nottingham Forest
Prem	Premier League	Leeds United	Leeds Utd	26%
26%26%
Wed, 3 Dec 20:15	Draw	27%
27%27%
Elland Road	Chelsea	Chelsea	47%
47%47%
Sky Sports Premier LeagueSuperSport Variety 3	Leaning Chelsea"""

print("Testing parser with new data (Premier League, League One, Championship)...")
print("=" * 80)

result = parse_match_text_ligue1_format(test_data)
print(f'\nFound {len(result)} matches:\n')

for i, m in enumerate(result, 1):
    print(f'{i}. {m["team_a"]} vs {m["team_b"]} ({m["game_title"]}) on {m["date"]}')

print(f'\nExpected: 9 matches')
print(f'Actual: {len(result)} matches')
if len(result) == 9:
    print('Status: PASS')
else:
    print('Status: FAIL')

print("\nBreakdown by league:")
from collections import Counter
league_counts = Counter(m['game_title'] for m in result)
for league, count in sorted(league_counts.items()):
    print(f"  {league}: {count} matches")

