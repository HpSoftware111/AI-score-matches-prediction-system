# Premier League Match Data Parsing Prompt

## Format Description

The Premier League match data follows a specific tab-separated format with duplicate entries. Each match spans multiple lines:

### Structure

```
[Prem]	[Premier League]	[Team A]	[Team A]	[Prob A%]
[Prob A%][Prob A%]
[Date]	Draw	[Draw Prob%]
[Draw Prob%][Draw Prob%]
[Stadium]	[Team B]	[Team B]	[Prob B%]
[Prob B%][Prob B%]
[TV Channels]	[Forecast Text]
```

**Note**: The first line contains both `Prem` (abbreviation) and `Premier League` (full name) before the team names.

### Example 1: Standard Format

```
Prem	Premier League	Bournemouth	Bournemouth	45%
45%45%
Tue, 2 Dec 19:30	Draw	28%
28%28%
Vitality Stadium	Everton	Everton	27%
27%27%
Sky Sports+Disney+ Hotstar	Leaning Bournemouth
```

### Example 2: With Team Name Abbreviations

```
Prem	Premier League	Wolves	Wolves	27%
27%27%
Wed, 3 Dec 19:30	Draw	27%
27%27%
Molineux Stadium	Nottingham Forest	Notts Forest	46%
46%46%
Sky Sports F1 HDVOYO	Leaning Nottingham Forest
```

### Example 3: With Forecast: Prefix

```
Prem	Premier League	Wolves	Wolves	23%
23%23%
Mon, 8 Dec 20:00	Draw	26%
26%26%
Molineux Stadium	Manchester United	Man Utd	51%
51%51%
Forecast:	Leaning Manchester United
```

## Parsing Rules

### 1. League Identification
- Look for: `Premier League`, `Prem`, `EPL`, or `PL` at the start of a line
- Normalize `Prem` to `Premier League`
- Set country to `England`

### 2. Team A Extraction (Line 1)
- Format: `Prem\tPremier League\t[Team A]\t[Team A]\t[Prob A%]`
- Contains both `Prem` (abbreviation) and `Premier League` (full name)
- Team name appears twice (duplicate)
- Extract the first occurrence of team name (after both league identifiers, before percentage)
- Extract percentage from the last column
- Example: `Prem	Premier League	Bournemouth	Bournemouth	45%`
  - League parts: `Prem`, `Premier League` (both should be recognized and skipped)
  - Team A: `Bournemouth` (first occurrence after league parts)
  - Prob A: `45%` (convert to 0.45)

### 3. Skip Duplicate Percentage Lines (Line 2)
- Lines containing only percentages (e.g., `45%45%`) should be skipped
- Pattern: `^[\d%\s]+\s*$` or `^[\d%]+\s*[\d%]+\s*$`

### 4. Date Extraction (Line 3)
- Format: `[Day], [Day] [Month] [Hour]:[Minute]`
- Example: `Tue, 2 Dec 19:30`
- Pattern: `(Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s+(\d{1,2})\s+([A-Z][a-z]{2})\s+(\d{1,2}):(\d{2})`
- Parse to datetime object
- Handle year: if month is in the past, use next year

### 5. Draw Probability (Line 3)
- Format: `[Date]\tDraw\t[Draw Prob%]`
- Extract percentage after "Draw"
- Example: `Tue, 2 Dec 19:30	Draw	28%`
  - Draw Prob: `28%` (convert to 0.28)

### 6. Skip Duplicate Draw Percentage (Line 4)
- Same as line 2 - skip duplicate percentage lines

### 7. Team B Extraction (Line 5)
- Format: `[Stadium]\t[Team B]\t[Team B]\t[Prob B%]`
- Stadium name appears first
- Team name appears twice (duplicate)
- Extract team name (after stadium, before percentage)
- Extract percentage from the last column
- Example: `Vitality Stadium	Everton	Everton	27%`
  - Stadium: `Vitality Stadium` (skip)
  - Team B: `Everton`
  - Prob B: `27%` (convert to 0.27)

### 8. Stadium Recognition
Common English stadium indicators:
- Generic: `Stadium`, `Park`, `Ground`, `Arena`, `Stadium of Light`, `Community Stadium`
- Specific stadium names:
  - `Vitality Stadium`
  - `Craven Cottage`
  - `St James Park` (also appears as `St James Park`)
  - `Emirates Stadium`
  - `Anfield`
  - `Old Trafford`
  - `Turf Moor`
  - `Molineux Stadium`
  - `Elland Road`
  - `American Express Stadium`
  - `Tottenham Hotspur Stadium`
  - `Stamford Bridge`
  - `Etihad Stadium`
  - `Villa Park`
  - `Hill Dickinson Stadium`
  - `Selhurst Park`
  - `City Ground`
  - `London Stadium`
  - `Brentford Community Stadium`
- Stadium name appears first in the line, followed by team B

### 9. Skip Duplicate Percentage Lines (Line 6)
- Same as line 2

### 10. Skip TV Channels and Forecast (Line 7)
- Skip lines containing TV channels or forecast text:
  - TV Channels: `Sky Sports`, `Disney+`, `Hotstar`, `SuperSport`, `MultiSports`, `VOYO`, `TNT Sports`, `V Sport`, `Arena Sport`, `Universo`, `Stöð 2 Sport`, etc.
  - Forecast patterns:
    - `Leaning [Team]` (e.g., "Leaning Nottingham Forest")
    - `Backing [Team]` (e.g., "Backing Liverpool")
    - `Could go either way`
    - `Forecast:	Leaning [Team]` (with "Forecast:" prefix)
    - `Forecast:	Backing [Team]` (with "Forecast:" prefix)
    - `Forecast:	Could go either way` (with "Forecast:" prefix)
- Note: Some forecast lines start with `Forecast:` followed by tab, then the forecast text

## Complete Example Parsing

### Example 1: Standard Format

**Input:**
```
Prem	Premier League	Bournemouth	Bournemouth	45%
45%45%
Tue, 2 Dec 19:30	Draw	28%
28%28%
Vitality Stadium	Everton	Everton	27%
27%27%
Sky Sports+Disney+ Hotstar	Leaning Bournemouth
```

**Output:**
```python
{
    'team_a': 'Bournemouth',
    'team_b': 'Everton',
    'date': datetime(2024, 12, 2, 19, 30),
    'prob_a': 0.45,
    'prob_b': 0.27,
    'draw_prob': 0.28,
    'odds_a': 2.0,  # Default (not provided)
    'odds_b': 2.0,  # Default (not provided)
    'week_number': 49,  # ISO week number
    'country': 'England',
    'game_title': 'Premier League'
}
```

### Example 2: With Team Abbreviations

**Input:**
```
Prem	Premier League	Wolves	Wolves	27%
27%27%
Wed, 3 Dec 19:30	Draw	27%
27%27%
Molineux Stadium	Nottingham Forest	Notts Forest	46%
46%46%
Sky Sports F1 HDVOYO	Leaning Nottingham Forest
```

**Output:**
```python
{
    'team_a': 'Wolves',
    'team_b': 'Notts Forest',  # Note: Uses abbreviation as it appears in data
    'date': datetime(2024, 12, 3, 19, 30),
    'prob_a': 0.27,
    'prob_b': 0.46,
    'draw_prob': 0.27,
    'odds_a': 2.0,
    'odds_b': 2.0,
    'week_number': 49,
    'country': 'England',
    'game_title': 'Premier League'
}
```

### Example 3: With Forecast: Prefix

**Input:**
```
Prem	Premier League	Wolves	Wolves	23%
23%23%
Mon, 8 Dec 20:00	Draw	26%
26%26%
Molineux Stadium	Manchester United	Man Utd	51%
51%51%
Forecast:	Leaning Manchester United
```

**Output:**
```python
{
    'team_a': 'Wolves',
    'team_b': 'Man Utd',  # Uses abbreviation
    'date': datetime(2024, 12, 8, 20, 0),
    'prob_a': 0.23,
    'prob_b': 0.51,
    'draw_prob': 0.26,
    'odds_a': 2.0,
    'odds_b': 2.0,
    'week_number': 50,
    'country': 'England',
    'game_title': 'Premier League'
}
```

### Example 4: Multiple Matches in Sequence

**Input:**
```
Prem	Premier League	Liverpool	Liverpool	68%
68%68%
Wed, 3 Dec 20:15	Draw	18%
18%18%
Anfield	Sunderland	Sunderland	13%
13%13%
Sky Sports FootballMultiSports 1 FR	Backing Liverpool
Prem	Premier League	Manchester United	Man Utd	55%
55%55%
Thu, 4 Dec 20:00	Draw	25%
25%25%
Old Trafford	West Ham	West Ham	20%
20%20%
Sky Sports Premier LeagueSky Sports Main Event	Leaning Manchester United
```

**Output:** (Two separate match objects)
```python
[
    {
        'team_a': 'Liverpool',
        'team_b': 'Sunderland',
        'date': datetime(2024, 12, 3, 20, 15),
        'prob_a': 0.68,
        'prob_b': 0.13,
        'draw_prob': 0.18,
        'odds_a': 2.0,
        'odds_b': 2.0,
        'week_number': 49,
        'country': 'England',
        'game_title': 'Premier League'
    },
    {
        'team_a': 'Manchester United',
        'team_b': 'West Ham',
        'date': datetime(2024, 12, 4, 20, 0),
        'prob_a': 0.55,
        'prob_b': 0.20,
        'draw_prob': 0.25,
        'odds_a': 2.0,
        'odds_b': 2.0,
        'week_number': 49,
        'country': 'England',
        'game_title': 'Premier League'
    }
]
```

## Edge Cases

1. **Multiple Matches**: Each match starts with a league identifier. When you see a new league identifier, start parsing a new match.

2. **Missing Data**: If draw probability is missing, calculate it as: `max(0, 1 - prob_a - prob_b)`

3. **Team Name Variations**: Team names may appear with different formats or abbreviations:
   - `Manchester City` vs `Man City`
   - `Nottingham Forest` vs `Notts Forest`
   - `Leeds United` vs `Leeds Utd`
   - `Crystal Palace` vs `Palace`
   - `Manchester United` vs `Man Utd`
   - **Important**: Handle these as separate teams (don't normalize). The system should create separate Team objects for each variation.
   - In the data, you may see both full name and abbreviation in the same match (e.g., "Nottingham Forest" and "Notts Forest" both appear)

4. **Header Lines**: Skip lines starting with:
   - `INFO`
   - `TEAMS`
   - `FORECAST`
   - `Table with`

5. **Tab vs Space Separation**: The format primarily uses tabs (`\t`), but may fall back to multiple spaces (`\s{2,}`)

## Validation Rules

1. Team A and Team B must be different
2. All probabilities should sum to approximately 100% (allow small rounding differences)
3. Date must be parseable
4. Team names must not be empty
5. Probabilities must be between 0 and 100%

## Implementation Notes

- Use tab-separated parsing first, fall back to space-separated
- Skip duplicate lines (same team name, same percentage)
- Extract first unique team name when duplicates appear
- Normalize league abbreviations to full names (`Prem` → `Premier League`)
- Calculate week number from date using ISO calendar
- Set default odds to 2.0 if not provided
- **Critical**: After completing a match, continue to the next line to look for the next match. Don't stop after the first match.
- When parsing team names, skip all league-related parts (`Prem`, `Premier League`) before extracting team name
- Handle team name abbreviations as-is (don't normalize "Man City" to "Manchester City")
- Stadium names can be multi-word (e.g., "Tottenham Hotspur Stadium", "Brentford Community Stadium")
- Forecast lines may start with "Forecast:" prefix followed by tab
- Multiple matches can appear in sequence - each starts with `Prem	Premier League`

## Common Stadium Names Reference

- `Vitality Stadium` (Bournemouth)
- `Craven Cottage` (Fulham)
- `St James Park` (Newcastle)
- `Emirates Stadium` (Arsenal)
- `Anfield` (Liverpool)
- `Old Trafford` (Manchester United)
- `Turf Moor` (Burnley)
- `Molineux Stadium` (Wolves)
- `Elland Road` (Leeds United)
- `American Express Stadium` (Brighton)
- `Tottenham Hotspur Stadium` (Tottenham)
- `Stamford Bridge` (Chelsea)
- `Etihad Stadium` (Manchester City)
- `Villa Park` (Aston Villa)
- `Hill Dickinson Stadium` (Everton)
- `Selhurst Park` (Crystal Palace)
- `City Ground` (Nottingham Forest)
- `London Stadium` (West Ham)
- `Brentford Community Stadium` (Brentford)
- `Stadium of Light` (Sunderland)

## Team Name Abbreviation Patterns

Common abbreviations found in data:
- `Manchester City` → `Man City`
- `Manchester United` → `Man Utd`
- `Nottingham Forest` → `Notts Forest`
- `Leeds United` → `Leeds Utd`
- `Crystal Palace` → `Palace`

**Important**: These are treated as separate team names in the system. The parser should extract them exactly as they appear in the data.

