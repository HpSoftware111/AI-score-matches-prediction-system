# Quick Start Guide

## Initial Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Migrations** (already done):
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **Create Superuser**:
   ```bash
   python manage.py createsuperuser
   ```
   Follow the prompts to create an admin user.

4. **Run Development Server**:
   ```bash
   python manage.py runserver
   ```

5. **Access the Application**:
   - Home: http://127.0.0.1:8000/
   - Admin: http://127.0.0.1:8000/admin/
   - Weekly Predictions: http://127.0.0.1:8000/predictions/weekly/
   - Analytics: http://127.0.0.1:8000/analytics/

## Adding Your First Match

1. Log into the admin panel (http://127.0.0.1:8000/admin/)
2. Navigate to **Matches** → **Add Match**
3. Fill in:
   - Team A (select or create new team)
   - Team B (select or create new team)
   - Match Date
   - Probabilities (Team A, Team B, Draw) - as decimals (e.g., 0.29 for 29%)
   - Odds (Team A, Team B)
4. Click **Save**

## Generating Predictions

### Option 1: Via Admin Panel
1. Go to **Predictions** in admin
2. Select matches without predictions
3. Use the action: **"Regenerate rule-based predictions"**
4. Or use: **"Generate AI predictions (DeepSeek)"** for AI-powered predictions

### Option 2: Via Web Interface
1. Navigate to a match detail page
2. Click **"Generate Predictions"** for rule-based
3. Or click **"Generate with AI"** for DeepSeek AI predictions

## CSV Import/Export

### Export Matches
1. Go to **Matches** in admin
2. Select matches you want to export
3. Choose action: **"Export selected matches as CSV"**
4. Download the CSV file

### Import Matches (Manual)
Use the exported CSV format:
```csv
team_a,team_b,date,prob_a,prob_b,odds_a,odds_b,draw_prob,actual_result
Everton,Bournemouth,2024-01-15T15:00:00,0.29,0.46,3.45,2.17,0.25,
Arsenal,Liverpool,2024-01-20T17:30:00,0.45,0.35,2.22,2.86,0.20,
```

Create matches manually using the admin panel following this format.

## Prediction Types Explained

1. **Baseline**: Simple probability-based prediction
   - Higher probability team wins
   - If close (≤15% difference) → Draw

2. **Profitable**: Value-based prediction
   - Compares actual probability vs implied probability from odds
   - Identifies undervalued teams

3. **Balanced**: Combined approach
   - Merges probability and odds alignment
   - Only picks a team if both factors align

## Viewing Analytics

1. Navigate to **Analytics Dashboard**: http://127.0.0.1:8000/analytics/
2. View:
   - Overall accuracy for each prediction type
   - Weekly accuracy trends
   - Prediction distribution charts
   - Comparison table of predictions vs actual results

## Troubleshooting

### DeepSeek API Errors
- Check that `DEEPSEEK_API_KEY` is set correctly in `settings.py`
- Verify API key is valid
- Check internet connection

### Migration Issues
If you encounter migration issues:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Static Files Warning
If you see a static files warning, create the static directory:
```bash
mkdir static
```

## Next Steps

- Add matches for your prediction period
- Generate predictions (rule-based or AI)
- Enter actual match results to track accuracy
- View analytics to compare prediction strategies

