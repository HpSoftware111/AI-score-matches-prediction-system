from django.contrib import admin
from .models import Team, Match
from django import forms
import csv
from django.http import HttpResponse


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'logo_url']
    search_fields = ['name']
    list_per_page = 25


class MatchAdminForm(forms.ModelForm):
    """Form with validation for Match model"""
    
    class Meta:
        model = Match
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        team_a = cleaned_data.get('team_a')
        team_b = cleaned_data.get('team_b')
        
        if team_a and team_b and team_a.id == team_b.id:
            raise forms.ValidationError({
                'team_b': 'Team A and Team B must be different teams. A team cannot play against itself.'
            })
        
        return cleaned_data


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    form = MatchAdminForm
    list_display = ['__str__', 'date', 'country', 'game_title', 'week_number', 'prob_a_percent', 'prob_b_percent', 'odds_a', 'odds_b', 'actual_result']
    list_filter = ['date', 'team_a', 'team_b', 'country', 'game_title', 'week_number']
    search_fields = ['team_a__name', 'team_b__name', 'country', 'game_title']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at', 'week_number']
    fieldsets = (
        ('Match Information', {
            'fields': ('team_a', 'team_b', 'date', 'week_number')
        }),
        ('League Information', {
            'fields': ('country', 'game_title')
        }),
        ('Probabilities', {
            'fields': ('prob_a', 'prob_b', 'draw_prob')
        }),
        ('Odds', {
            'fields': ('odds_a', 'odds_b')
        }),
        ('Result', {
            'fields': ('actual_result',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['export_as_csv']

    def export_as_csv(self, request, queryset):
        """Export selected matches as CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="matches.csv"'
        writer = csv.writer(response)
        
        writer.writerow(['team_a', 'team_b', 'date', 'week_number', 'country', 'game_title', 'prob_a', 'prob_b', 'odds_a', 'odds_b', 'draw_prob', 'actual_result'])
        for match in queryset:
            writer.writerow([
                match.team_a.name,
                match.team_b.name,
                match.date.isoformat(),
                match.week_number or '',
                match.country or '',
                match.game_title or '',
                match.prob_a,
                match.prob_b,
                match.odds_a,
                match.odds_b,
                match.draw_prob,
                match.actual_result or ''
            ])
        return response
    export_as_csv.short_description = "Export selected matches as CSV"

