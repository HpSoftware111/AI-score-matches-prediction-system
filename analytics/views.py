from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, F
from predictions.models import Prediction
from matches.models import Match
from analytics.models import AnalyticsSnapshot
import json
from datetime import datetime, timedelta


@login_required
def analytics_dashboard(request):
    """Main analytics dashboard with charts and metrics"""
    
    # Get all predictions with actual results
    predictions = Prediction.objects.filter(
        match__actual_result__isnull=False
    ).select_related('match')
    
    total_with_results = predictions.count()
    
    # Calculate accuracies
    baseline_correct = sum(1 for p in predictions if p.baseline_correct)
    profitable_correct = sum(1 for p in predictions if p.profitable_correct)
    balanced_correct = sum(1 for p in predictions if p.balanced_correct)
    
    baseline_accuracy = (baseline_correct / total_with_results * 100) if total_with_results > 0 else 0
    profitable_accuracy = (profitable_correct / total_with_results * 100) if total_with_results > 0 else 0
    balanced_accuracy = (balanced_correct / total_with_results * 100) if total_with_results > 0 else 0
    
    # Weekly accuracy trends (last 8 weeks)
    weekly_data = []
    today = datetime.now().date()
    for week in range(8):
        week_start = today - timedelta(days=(today.weekday() + week * 7))
        week_end = week_start + timedelta(days=7)
        
        week_predictions = Prediction.objects.filter(
            match__date__gte=week_start,
            match__date__lt=week_end,
            match__actual_result__isnull=False
        )
        
        week_total = week_predictions.count()
        if week_total > 0:
            week_baseline = sum(1 for p in week_predictions if p.baseline_correct) / week_total * 100
            week_profitable = sum(1 for p in week_predictions if p.profitable_correct) / week_total * 100
            week_balanced = sum(1 for p in week_predictions if p.balanced_correct) / week_total * 100
            
            weekly_data.append({
                'week': week_start.strftime('%Y-%m-%d'),
                'baseline': round(week_baseline, 2),
                'profitable': round(week_profitable, 2),
                'balanced': round(week_balanced, 2)
            })
    
    # Prediction distribution
    baseline_dist = {
        '1': predictions.filter(baseline='1').count(),
        '3': predictions.filter(baseline='3').count(),
        '0': predictions.filter(baseline='0').count()
    }
    
    profitable_dist = {
        '1': predictions.filter(profitable='1').count(),
        '3': predictions.filter(profitable='3').count(),
        '0': predictions.filter(profitable='0').count()
    }
    
    balanced_dist = {
        '1': predictions.filter(balanced='1').count(),
        '3': predictions.filter(balanced='3').count(),
        '0': predictions.filter(balanced='0').count()
    }
    
    # Comparison table data
    comparison_data = []
    for pred in predictions[:50]:  # Limit to 50 for display
        comparison_data.append({
            'match': str(pred.match),
            'actual': pred.match.actual_result,
            'baseline': pred.baseline,
            'baseline_correct': pred.baseline_correct,
            'profitable': pred.profitable,
            'profitable_correct': pred.profitable_correct,
            'balanced': pred.balanced,
            'balanced_correct': pred.balanced_correct,
        })
    
    context = {
        'total_predictions': total_with_results,
        'baseline_accuracy': round(baseline_accuracy, 2),
        'profitable_accuracy': round(profitable_accuracy, 2),
        'balanced_accuracy': round(balanced_accuracy, 2),
        'baseline_wins': baseline_correct,
        'profitable_wins': profitable_correct,
        'balanced_wins': balanced_correct,
        'weekly_data': json.dumps(weekly_data),
        'baseline_dist': json.dumps(baseline_dist),
        'profitable_dist': json.dumps(profitable_dist),
        'balanced_dist': json.dumps(balanced_dist),
        'comparison_data': comparison_data,
        'title': 'Analytics Dashboard'
    }
    
    return render(request, 'analytics/dashboard.html', context)


@login_required
def accuracy_tracking(request):
    """Detailed accuracy tracking view"""
    predictions = Prediction.objects.filter(
        match__actual_result__isnull=False
    ).select_related('match').order_by('-match__date')
    
    context = {
        'predictions': predictions,
        'title': 'Accuracy Tracking'
    }
    
    return render(request, 'analytics/accuracy_tracking.html', context)

