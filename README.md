# Sport Prediction System

A Django-based sport prediction system that uses rule-based algorithms and DeepSeek AI to generate predictions for sport matches.

## Features

- **Match Management**: Store fixtures with probabilities and odds
- **Prediction Engine**: Three prediction types:
  - **Baseline**: Higher probability wins
  - **Profitable**: Compare implied probability vs sportsbook odds
  - **Balanced**: Combine probability + odds alignment
- **AI Integration**: DeepSeek API integration for enhanced predictions
- **Analytics Dashboard**: Track accuracy, visualize trends, and compare predictions
- **Admin Dashboard**: Manage matches, teams, and predictions with CSV import/export

## Technology Stack

- **Backend**: Django 5.0+ (Python 3.11+)
- **Database**: SQLite (default, easy migration to PostgreSQL)
- **AI Engine**: DeepSeek API
- **Frontend**: Django Templates with Bootstrap 5 & Chart.js

## Installation

1. **Clone the repository**:
   ```bash
   cd "football prediction system"
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure DeepSeek API Key**:
   The API key is configured in `football_prediction_system/settings.py`. 
   You can also set it as an environment variable:
   ```bash
   export DEEPSEEK_API_KEY="your-api-key-here"
   ```

5. **Run migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a superuser**:
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

8. **Access the application**:
   - Main site: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## Usage

### Adding Matches

1. **Via Admin Panel**:
   - Go to `/admin/matches/match/`
   - Click "Add Match"
   - Fill in team names, date, probabilities, and odds
   - Save

2. **Via CSV Upload**:
   - Go to `/admin/matches/match/`
   - Select matches you want to export (or start fresh)
   - Use the "Export selected matches as CSV" action to see the format
   - Create a CSV with columns: `team_a, team_b, date, prob_a, prob_b, odds_a, odds_b, draw_prob`
   - Import manually by creating matches one by one (CSV import action can be added)

### Generating Predictions

1. **Rule-based Predictions**:
   - Navigate to a match detail page
   - Click "Generate Predictions"
   - System will calculate baseline, profitable, and balanced predictions

2. **AI Predictions** (DeepSeek):
   - Click "Generate with AI" on a match detail page
   - System will use DeepSeek API to generate enhanced predictions
   - AI predictions are stored separately and can be compared with rule-based ones

3. **Bulk Generation**:
   - Go to `/admin/predictions/prediction/`
   - Select matches without predictions
   - Use "Generate rule-based predictions" action

### Viewing Weekly Predictions

- Navigate to `/predictions/weekly/`
- View prediction strings for the current week
- See breakdown by match

### Analytics Dashboard

- Navigate to `/analytics/`
- View accuracy metrics for all prediction types
- See weekly trends and distribution charts
- Compare predictions in the comparison table

## Project Structure

```
football_prediction_system/
├── football_prediction_system/    # Main project settings
│   ├── settings.py                # Django settings
│   ├── urls.py                    # Root URL configuration
│   └── wsgi.py                    # WSGI configuration
├── matches/                       # Matches app
│   ├── models.py                 # Team, Match models
│   ├── admin.py                  # Admin configuration
│   └── views.py                  # Match views
├── predictions/                   # Predictions app
│   ├── models.py                 # Prediction model
│   ├── engine.py                 # Rule-based prediction logic
│   ├── deepseek_client.py        # DeepSeek API client
│   └── admin.py                  # Prediction admin
├── analytics/                     # Analytics app
│   ├── models.py                 # Analytics models
│   └── views.py                  # Analytics dashboard
├── users/                         # Users app
│   ├── models.py                 # Custom User model
│   └── admin.py                  # User admin
└── templates/                     # HTML templates
    ├── base.html                 # Base template
    ├── matches/                  # Match templates
    ├── predictions/              # Prediction templates
    ├── analytics/                # Analytics templates
    └── users/                    # User templates
```

## Database Schema

### Teams
- `id`: Primary key
- `name`: Team name (unique)
- `logo_url`: Optional logo URL

### Matches
- `id`: Primary key
- `team_a`: Foreign key to Team (home)
- `team_b`: Foreign key to Team (away)
- `date`: Match date/time
- `prob_a`: Team A probability (0.0-1.0)
- `prob_b`: Team B probability (0.0-1.0)
- `odds_a`: Team A odds
- `odds_b`: Team B odds
- `draw_prob`: Draw probability (0.0-1.0)
- `actual_result`: Actual match result ('1', '3', or '0')

### Predictions
- `id`: Primary key
- `match`: Foreign key to Match
- `baseline`: Baseline prediction ('1', '3', or '0')
- `profitable`: Profitable prediction
- `balanced`: Balanced prediction
- `ai_baseline`: AI-generated baseline (optional)
- `ai_profitable`: AI-generated profitable (optional)
- `ai_balanced`: AI-generated balanced (optional)
- `created_at`: Creation timestamp

## Configuration

### DeepSeek API

The system uses DeepSeek API for AI-powered predictions. Configure the API key in `settings.py`:

```python
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', 'your-default-key')
```

### Auto-generate Predictions

Set in `settings.py`:
```python
AUTO_GENERATE_PREDICTIONS = True  # Auto-generate when matches are created
```

## CSV Format

Example CSV for importing matches:

```csv
team_a,team_b,date,prob_a,prob_b,odds_a,odds_b,draw_prob
Everton,Bournemouth,2024-01-15 15:00:00,0.29,0.46,3.45,2.17,0.25
Arsenal,Liverpool,2024-01-20 17:30:00,0.45,0.35,2.22,2.86,0.20
```

## Migration to PostgreSQL

To migrate from SQLite to PostgreSQL:

1. Install PostgreSQL adapter:
   ```bash
   pip install psycopg2-binary
   ```

2. Update `settings.py`:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'football_predictions',
           'USER': 'your_user',
           'PASSWORD': 'your_password',
           'HOST': 'localhost',
           'PORT': '5432',
       }
   }
   ```

3. Run migrations:
   ```bash
   python manage.py migrate
   ```

## Development

### Running Tests

```bash
python manage.py test
```

### Creating Migrations

```bash
python manage.py makemigrations
```

### Collecting Static Files

```bash
python manage.py collectstatic
```

## License

This project is open source and available under the MIT License.

## Support

For issues or questions, please open an issue on the repository.

