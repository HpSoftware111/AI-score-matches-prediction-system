from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.http import JsonResponse
from .models import Match, Team
from .forms import MatchForm
from predictions.models import Prediction
from .text_parser import import_matches_from_text
from django.utils import timezone
from datetime import timedelta
import json


def home(request):
    """Home page with overview"""
    # Get recent matches
    recent_matches = Match.objects.all()[:10]
    
    # Get matches with predictions
    matches_with_predictions = Match.objects.filter(predictions__isnull=False).distinct()[:5]
    
    # Get upcoming matches this week
    today = timezone.now().date()
    week_end = today + timedelta(days=7)
    upcoming_matches = Match.objects.filter(
        date__gte=timezone.now(),
        date__lt=week_end
    )[:5]
    
    context = {
        'recent_matches': recent_matches,
        'matches_with_predictions': matches_with_predictions,
        'upcoming_matches': upcoming_matches,
        'title': 'Sport Prediction System'
    }
    return render(request, 'matches/home.html', context)


def match_list(request):
    """Display list of all matches"""
    matches = Match.objects.all()[:100]  # Limit to ~100 matches per page
    context = {
        'matches': matches,
        'title': 'Match Fixtures'
    }
    return render(request, 'matches/match_list.html', context)


def match_detail(request, pk):
    """Display detailed view of a single match"""
    match = get_object_or_404(Match, pk=pk)
    context = {
        'match': match,
        'title': str(match)
    }
    return render(request, 'matches/match_detail.html', context)


@login_required
def import_matches(request):
    """Import matches from text input"""
    if request.method == 'POST':
        text_data = request.POST.get('text_data', '')
        if text_data:
            created, errors, warnings = import_matches_from_text(text_data, skip_duplicates=True)
            
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'created': created,
                    'errors': errors[:50],  # Limit to 50 errors for display
                    'warnings': warnings[:50],  # Limit to 50 warnings for display
                    'message': f"Successfully imported {created} matches." if created > 0 else "No matches were imported."
                })
            
            # Regular form submission
            if created > 0:
                messages.success(request, f"Successfully imported {created} matches.")
            if warnings:
                for warning in warnings[:10]:  # Show first 10 warnings
                    messages.warning(request, warning)
            if errors:
                for error in errors[:10]:  # Show first 10 errors
                    messages.error(request, error)
            if created == 0 and not errors and not warnings:
                messages.info(request, "No matches were imported. Please check the text format.")
            return redirect('matches:import_matches')
    
    return render(request, 'matches/import_matches.html', {'title': 'Import Matches'})


@login_required
def match_create(request):
    """Create a new match"""
    if request.method == 'POST':
        form = MatchForm(request.POST)
        if form.is_valid():
            match = form.save()
            messages.success(request, f"Match '{match.team_a} vs {match.team_b}' created successfully!")
            return redirect('matches:match_detail', pk=match.pk)
    else:
        form = MatchForm()
    
    context = {
        'form': form,
        'title': 'Create New Match',
        'action': 'Create'
    }
    return render(request, 'matches/match_form.html', context)


@login_required
def match_update(request, pk):
    """Update an existing match"""
    match = get_object_or_404(Match, pk=pk)
    
    if request.method == 'POST':
        form = MatchForm(request.POST, instance=match)
        if form.is_valid():
            match = form.save()
            messages.success(request, f"Match '{match.team_a} vs {match.team_b}' updated successfully!")
            return redirect('matches:match_detail', pk=match.pk)
    else:
        form = MatchForm(instance=match)
    
    context = {
        'form': form,
        'match': match,
        'title': f'Edit Match: {match.team_a} vs {match.team_b}',
        'action': 'Update'
    }
    return render(request, 'matches/match_form.html', context)


@login_required
@require_http_methods(["POST"])
def match_delete(request, pk):
    """Delete a match"""
    match = get_object_or_404(Match, pk=pk)
    team_a = match.team_a
    team_b = match.team_b
    
    match.delete()
    messages.success(request, f"Match '{team_a} vs {team_b}' deleted successfully!")
    return redirect('matches:match_list')


@login_required
@require_http_methods(["POST"])
def match_bulk_delete(request):
    """Delete multiple matches"""
    match_ids = request.POST.getlist('match_ids')
    
    if not match_ids:
        messages.warning(request, "No matches selected for deletion.")
        return redirect('matches:match_list')
    
    try:
        matches_to_delete = Match.objects.filter(pk__in=match_ids)
        count = matches_to_delete.count()
        
        if count == 0:
            messages.warning(request, "No valid matches found to delete.")
            return redirect('matches:match_list')
        
        # Delete matches
        deleted_count = matches_to_delete.count()
        matches_to_delete.delete()
        
        messages.success(request, f"Successfully deleted {deleted_count} match(es).")
    except Exception as e:
        messages.error(request, f"Error deleting matches: {str(e)}")
    
    return redirect('matches:match_list')
