from django import forms
from .models import Match, Team


class MatchForm(forms.ModelForm):
    """Form for creating and editing matches"""
    
    class Meta:
        model = Match
        fields = [
            'team_a', 'team_b', 'date', 'prob_a', 'prob_b', 'draw_prob',
            'odds_a', 'odds_b', 'week_number', 'country', 'game_title', 'actual_result'
        ]
        widgets = {
            'date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control',
            }),
            'team_a': forms.Select(attrs={'class': 'form-select'}),
            'team_b': forms.Select(attrs={'class': 'form-select'}),
            'prob_a': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '1',
            }),
            'prob_b': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '1',
            }),
            'draw_prob': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '1',
            }),
            'odds_a': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
            }),
            'odds_b': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
            }),
            'week_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '53',
            }),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'game_title': forms.TextInput(attrs={'class': 'form-control'}),
            'actual_result': forms.Select(attrs={'class': 'form-select'}),
        }
        help_texts = {
            'prob_a': 'Probability for Team A winning (e.g., 0.29 = 29%)',
            'prob_b': 'Probability for Team B winning (e.g., 0.46 = 46%)',
            'draw_prob': 'Probability of a draw (e.g., 0.25 = 25%)',
            'week_number': 'Will be auto-calculated from date if left empty',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make week_number read-only in edit mode if it exists
        if self.instance and self.instance.pk and self.instance.week_number:
            self.fields['week_number'].widget.attrs['readonly'] = True
            self.fields['week_number'].help_text = 'Auto-calculated from date. Change the date to update.'
    
    def clean(self):
        cleaned_data = super().clean()
        team_a = cleaned_data.get('team_a')
        team_b = cleaned_data.get('team_b')
        
        # Ensure teams are different
        if team_a and team_b and team_a.id == team_b.id:
            raise forms.ValidationError({
                'team_b': 'Team A and Team B must be different teams. A team cannot play against itself.'
            })
        
        # Validate probabilities sum to reasonable value (within 95-105%)
        prob_a = cleaned_data.get('prob_a', 0)
        prob_b = cleaned_data.get('prob_b', 0)
        draw_prob = cleaned_data.get('draw_prob', 0)
        total_prob = prob_a + prob_b + draw_prob
        
        if total_prob < 0.95 or total_prob > 1.05:
            raise forms.ValidationError(
                f'Probabilities should sum to approximately 1.0 (100%). Current sum: {total_prob * 100:.1f}%'
            )
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Auto-calculate week_number from date if not set
        if instance.date and not instance.week_number:
            instance.week_number = instance.date.isocalendar()[1]
        elif instance.date and instance.week_number:
            # Recalculate if date changed
            new_week = instance.date.isocalendar()[1]
            if not self.instance.pk or (self.instance.pk and self.instance.date != instance.date):
                instance.week_number = new_week
        
        if commit:
            instance.save()
        return instance

