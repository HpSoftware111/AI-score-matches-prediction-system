from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Count
from django.db.models.functions import TruncWeek
from datetime import timedelta, datetime
from .models import Prediction
from matches.models import Match
from .engine import PredictionEngine
from .deepseek_client import DeepSeekClient
import json


@login_required
def weekly_predictions(request):
    """Display weekly prediction string with filtering"""
    # Get filter parameters from request
    filter_week = request.GET.get('week')
    filter_country = request.GET.get('country')
    filter_game_title = request.GET.get('game_title')
    
    now = timezone.now()
    today = now.date()
    
    # Determine week range based on filter
    if filter_week:
        try:
            # Parse week number (format: YYYY-WW)
            if '-' in filter_week:
                year, week_num = map(int, filter_week.split('-'))
            else:
                week_num = int(filter_week)
                year = today.year
            # Calculate week start and end dates from week number
            from datetime import date
            week_start_date = date.fromisocalendar(year, week_num, 1)
            week_end_date = week_start_date + timedelta(days=7)
            week_start = week_start_date
            week_end = week_end_date
        except (ValueError, AttributeError):
            # Invalid week format, use current week
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=7)
    else:
        # Default to current week
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=7)
    
    # Convert dates to datetime for comparison with DateTimeField
    week_start_dt = datetime.combine(week_start, datetime.min.time())
    week_end_dt = datetime.combine(week_end, datetime.min.time())
    
    # Make timezone-aware
    if timezone.is_naive(week_start_dt):
        week_start_dt = timezone.make_aware(week_start_dt)
    if timezone.is_naive(week_end_dt):
        week_end_dt = timezone.make_aware(week_end_dt)
    
    # Start with base query for matches in the week range
    matches = Match.objects.filter(
        date__gte=week_start_dt,
        date__lt=week_end_dt
    )
    
    # Apply filters
    if filter_week:
        # Filter by week_number if available
        try:
            week_num = int(filter_week.split('-')[1]) if '-' in filter_week else int(filter_week)
            matches = matches.filter(week_number=week_num)
        except (ValueError, IndexError):
            pass
    
    if filter_country:
        matches = matches.filter(country__icontains=filter_country)
    
    if filter_game_title:
        matches = matches.filter(game_title__icontains=filter_game_title)
    
    matches = matches.order_by('date')
    
    # If no matches found, show upcoming matches (next 7 days) without filters
    if not matches.exists() and not (filter_week or filter_country or filter_game_title):
        future_start = now
        future_end = now + timedelta(days=7)
        matches = Match.objects.filter(
            date__gte=future_start,
            date__lt=future_end
        ).order_by('date')[:10]  # Limit to 10 matches
    
    # Auto-generate predictions for matches without them
    engine_rule = PredictionEngine(use_ai=False)  # Rule-based for baseline
    engine_ai = PredictionEngine(use_ai=True)  # AI-based for profitable and balanced
    predictions_list = []
    
    for match in matches:
        pred = Prediction.objects.filter(match=match).first()
        needs_update = False
        
        # If no prediction exists, generate one
        if not pred:
            try:
                # Generate baseline with rule-based
                baseline_predictions = engine_rule.generate_prediction(match, use_ai=False)
                
                # Generate profitable and balanced with AI (with fallback to rule-based)
                try:
                    ai_predictions = engine_ai.generate_prediction(match, use_ai=True)
                    # Use AI predictions if available, otherwise use rule-based
                    profitable = ai_predictions.get('ai_profitable') or ai_predictions.get('profitable') or baseline_predictions.get('profitable')
                    balanced = ai_predictions.get('ai_balanced') or ai_predictions.get('balanced') or baseline_predictions.get('balanced')
                except Exception:
                    # If AI fails, use rule-based as fallback
                    profitable = baseline_predictions.get('profitable')
                    balanced = baseline_predictions.get('balanced')
                    ai_predictions = {'ai_profitable': None, 'ai_balanced': None}
                
                pred, created = Prediction.objects.get_or_create(match=match)
                pred.baseline = baseline_predictions['baseline']
                pred.profitable = profitable
                pred.balanced = balanced
                
                # Save AI predictions if available
                if ai_predictions.get('ai_profitable'):
                    pred.ai_profitable = ai_predictions['ai_profitable']
                if ai_predictions.get('ai_balanced'):
                    pred.ai_balanced = ai_predictions['ai_balanced']
                
                pred.save()
            except Exception as e:
                # Skip if generation fails
                continue
        else:
            # Update profitable and balanced with AI if they don't have AI predictions or are using rule-based
            if not pred.ai_profitable or not pred.ai_balanced:
                try:
                    ai_predictions = engine_ai.generate_prediction(match, use_ai=True)
                    if ai_predictions.get('ai_profitable'):
                        pred.profitable = ai_predictions['ai_profitable']
                        pred.ai_profitable = ai_predictions['ai_profitable']
                        needs_update = True
                    if ai_predictions.get('ai_balanced'):
                        pred.balanced = ai_predictions['ai_balanced']
                        pred.ai_balanced = ai_predictions['ai_balanced']
                        needs_update = True
                    if needs_update:
                        pred.save()
                except Exception as e:
                    # If AI fails, keep existing predictions
                    pass
        
        # Add to list if prediction exists
        if pred:
            predictions_list.append({
                'match': match,
                'baseline': pred.baseline,
                'profitable': pred.profitable,
                'balanced': pred.balanced
            })
    
    # Generate prediction strings
    baseline_string = ''.join([p['baseline'] for p in predictions_list]) if predictions_list else ''
    profitable_string = ''.join([p['profitable'] for p in predictions_list]) if predictions_list else ''
    balanced_string = ''.join([p['balanced'] for p in predictions_list]) if predictions_list else ''
    
    # Get distinct values for filter dropdowns
    distinct_countries = sorted(set(Match.objects.exclude(country__isnull=True).exclude(country='').values_list('country', flat=True)))
    distinct_game_titles = sorted(set(Match.objects.exclude(game_title__isnull=True).exclude(game_title='').values_list('game_title', flat=True)))
    
    # Get available weeks (format: YYYY-WW)
    available_weeks = []
    week_data = Match.objects.exclude(week_number__isnull=True).values_list('date', 'week_number').distinct()
    for match_date, week_num in week_data:
        if match_date and week_num:
            try:
                year = match_date.year if hasattr(match_date, 'year') else int(str(match_date)[:4])
                week_key = f"{year}-{week_num:02d}"
                if week_key not in available_weeks:
                    available_weeks.append(week_key)
            except (AttributeError, ValueError, TypeError):
                continue
    available_weeks = sorted(set(available_weeks), reverse=True)
    
    context = {
        'predictions': predictions_list,
        'baseline_string': baseline_string,
        'profitable_string': profitable_string,
        'balanced_string': balanced_string,
        'week_start': week_start,
        'week_end': week_end,
        'title': 'Weekly Predictions',
        'filter_week': filter_week or '',
        'filter_country': filter_country or '',
        'filter_game_title': filter_game_title or '',
        'available_weeks': available_weeks,
        'distinct_countries': distinct_countries,
        'distinct_game_titles': distinct_game_titles,
    }
    
    return render(request, 'predictions/weekly_predictions.html', context)


@login_required
def generate_predictions_view(request, match_id):
    """Generate predictions for a specific match"""
    match = get_object_or_404(Match, pk=match_id)
    use_ai = request.GET.get('use_ai', 'false').lower() == 'true'
    engine = PredictionEngine(use_ai=use_ai)
    client = DeepSeekClient() if use_ai else None
    
    predictions = engine.generate_prediction(match, use_ai=use_ai)
    
    # Get full API response data if using AI
    api_responses = {}
    if use_ai and client:
        try:
            api_responses = {
                'baseline': client.get_full_prediction_response(match, 'baseline'),
                'profitable': client.get_full_prediction_response(match, 'profitable'),
                'balanced': client.get_full_prediction_response(match, 'balanced')
            }
        except Exception as e:
            pass  # Continue even if API response fails
    
    # Save or update prediction
    pred, created = Prediction.objects.get_or_create(match=match)
    pred.baseline = predictions['baseline']
    pred.profitable = predictions['profitable']
    pred.balanced = predictions['balanced']
    
    if predictions['ai_baseline']:
        pred.ai_baseline = predictions['ai_baseline']
    if predictions['ai_profitable']:
        pred.ai_profitable = predictions['ai_profitable']
    if predictions['ai_balanced']:
        pred.ai_balanced = predictions['ai_balanced']
    
    if api_responses:
        pred.api_response_data = api_responses
    
    pred.save()
    
    # Update accuracy if match has result
    if match.actual_result:
        pred.update_accuracy()
    
    messages.success(request, f"Predictions generated successfully for {match.team_a} vs {match.team_b}")
    
    context = {
        'match': match,
        'prediction': pred,
        'created': created,
        'api_responses': api_responses,
        'title': 'Prediction Generated'
    }
    
    return render(request, 'predictions/prediction_detail.html', context)


@login_required
def prediction_detail_with_analysis(request, match_id):
    """Display detailed prediction analysis with DeepSeek API response data"""
    match = get_object_or_404(Match, pk=match_id)
    prediction = Prediction.objects.filter(match=match).first()
    
    # Get full API response data if available
    api_responses = {}
    analysis_data = {}
    
    if prediction and prediction.api_response_data:
        api_responses = prediction.api_response_data
    
    # Generate fresh analysis if requested
    if request.GET.get('refresh') == 'true':
        client = DeepSeekClient()
        engine = PredictionEngine(use_ai=True)
        
        try:
            # Get full responses for all prediction types
            baseline_response = client.get_full_prediction_response(match, 'baseline')
            profitable_response = client.get_full_prediction_response(match, 'profitable')
            balanced_response = client.get_full_prediction_response(match, 'balanced')
            
            api_responses = {
                'baseline': baseline_response,
                'profitable': profitable_response,
                'balanced': balanced_response
            }
            
            # Store in prediction
            if not prediction:
                prediction = Prediction.objects.create(match=match)
            
            prediction.api_response_data = api_responses
            prediction.save()
            
            # Generate predictions
            predictions = engine.generate_prediction(match, use_ai=True)
            prediction.baseline = predictions['baseline']
            prediction.profitable = predictions['profitable']
            prediction.balanced = predictions['balanced']
            if predictions['ai_baseline']:
                prediction.ai_baseline = predictions['ai_baseline']
            if predictions['ai_profitable']:
                prediction.ai_profitable = predictions['ai_profitable']
            if predictions['ai_balanced']:
                prediction.ai_balanced = predictions['ai_balanced']
            prediction.save()
            
            messages.success(request, "Predictions refreshed with detailed analysis!")
        except Exception as e:
            messages.error(request, f"Error generating analysis: {str(e)}")
    
    # Calculate analysis metrics
    if api_responses:
        for pred_type, response in api_responses.items():
            if response and response.get('success'):
                usage = response.get('response', {}).get('usage', {})
                analysis_data[pred_type] = {
                    'tokens_used': usage.get('total_tokens', 0),
                    'prompt_tokens': usage.get('prompt_tokens', 0),
                    'completion_tokens': usage.get('completion_tokens', 0),
                    'cache_hit_tokens': usage.get('prompt_cache_hit_tokens', 0),
                    'cache_miss_tokens': usage.get('prompt_cache_miss_tokens', 0),
                    'raw_content': response.get('raw_content', ''),
                    'model': response.get('request', {}).get('model', ''),
                }
    
    # Update accuracy if match has result
    if prediction and match.actual_result:
        prediction.update_accuracy()
    
    # Convert API responses to JSON strings for template
    api_responses_json = {}
    if api_responses:
        for key, value in api_responses.items():
            api_responses_json[key] = json.dumps(value, default=str)
    
    context = {
        'match': match,
        'prediction': prediction,
        'api_responses': api_responses,
        'api_responses_json': api_responses_json,
        'analysis_data': analysis_data,
        'title': f'Prediction Analysis: {match.team_a} vs {match.team_b}'
    }
    
    return render(request, 'predictions/prediction_analysis.html', context)


@login_required
def batch_predictions(request):
    """Generate predictions for multiple matches in batch"""
    if request.method == 'POST':
        match_ids = request.POST.getlist('match_ids')
        use_ai = request.POST.get('use_ai', 'true').lower() == 'true'
        
        if not match_ids:
            messages.warning(request, "No matches selected.")
            return redirect('predictions:weekly_predictions')
        
        matches = Match.objects.filter(pk__in=match_ids)
        engine = PredictionEngine(use_ai=use_ai)
        client = DeepSeekClient() if use_ai else None
        
        results = {
            'total': len(matches),
            'success': 0,
            'failed': 0,
            'predictions': []
        }
        
        for match in matches:
            try:
                # Generate predictions
                predictions = engine.generate_prediction(match, use_ai=use_ai)
                
                # Get full API response if using AI
                api_responses = {}
                if use_ai and client:
                    try:
                        api_responses = {
                            'baseline': client.get_full_prediction_response(match, 'baseline'),
                            'profitable': client.get_full_prediction_response(match, 'profitable'),
                            'balanced': client.get_full_prediction_response(match, 'balanced')
                        }
                    except Exception as e:
                        pass  # Continue even if API response fails
                
                # Save prediction
                pred, created = Prediction.objects.get_or_create(match=match)
                pred.baseline = predictions['baseline']
                pred.profitable = predictions['profitable']
                pred.balanced = predictions['balanced']
                
                if predictions['ai_baseline']:
                    pred.ai_baseline = predictions['ai_baseline']
                if predictions['ai_profitable']:
                    pred.ai_profitable = predictions['ai_profitable']
                if predictions['ai_balanced']:
                    pred.ai_balanced = predictions['ai_balanced']
                
                if api_responses:
                    pred.api_response_data = api_responses
                
                pred.save()
                
                results['success'] += 1
                results['predictions'].append({
                    'match': match,
                    'prediction': pred,
                    'created': created
                })
            except Exception as e:
                results['failed'] += 1
                results['predictions'].append({
                    'match': match,
                    'error': str(e)
                })
        
        messages.success(
            request, 
            f"Batch prediction complete: {results['success']} successful, {results['failed']} failed"
        )
        
        context = {
            'results': results,
            'title': 'Batch Prediction Results'
        }
        
        return render(request, 'predictions/batch_results.html', context)
    
    # GET request - show form to select matches
    week = request.GET.get('week')
    country = request.GET.get('country')
    game_title = request.GET.get('game_title')
    
    matches = Match.objects.all()
    
    if week:
        try:
            week_num = int(week.split('-')[1]) if '-' in week else int(week)
            matches = matches.filter(week_number=week_num)
        except (ValueError, IndexError):
            pass
    
    if country:
        matches = matches.filter(country__icontains=country)
    
    if game_title:
        matches = matches.filter(game_title__icontains=game_title)
    
    # Show upcoming matches without predictions
    matches = matches.filter(date__gte=timezone.now()).order_by('date')[:50]
    
    context = {
        'matches': matches,
        'title': 'Batch Predictions'
    }
    
    return render(request, 'predictions/batch_predictions.html', context)


@login_required
def accuracy_stats(request):
    """Display prediction accuracy statistics"""
    stats = Prediction.get_accuracy_stats()
    
    # Get recent predictions with results
    recent_predictions = Prediction.objects.filter(
        match__actual_result__isnull=False
    ).select_related('match').order_by('-match__date')[:50]
    
    # Calculate accuracy over time (by week)
    weekly_stats = []
    if recent_predictions.exists():
        from django.db.models.functions import TruncWeek
        weekly_data = Prediction.objects.filter(
            match__actual_result__isnull=False,
            is_correct__isnull=False
        ).annotate(
            week=TruncWeek('match__date')
        ).values('week', 'prediction_type_used').annotate(
            total=Count('id'),
            correct=Count('id', filter=Q(is_correct=True))
        ).order_by('-week')[:20]
        
        for week_data in weekly_data:
            if week_data['total'] > 0:
                weekly_stats.append({
                    'week': week_data['week'],
                    'type': week_data['prediction_type_used'] or 'unknown',
                    'total': week_data['total'],
                    'correct': week_data['correct'],
                    'accuracy': round((week_data['correct'] / week_data['total']) * 100, 2)
                })
    
    context = {
        'stats': stats,
        'recent_predictions': recent_predictions,
        'weekly_stats': weekly_stats,
        'title': 'Prediction Accuracy Statistics'
    }
    
    return render(request, 'predictions/accuracy_stats.html', context)

