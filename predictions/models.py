from django.db import models
from django.db.models import Count, Q, Avg, Case, When, IntegerField
from matches.models import Match
import json


class Prediction(models.Model):
    """Prediction model for storing AI-generated predictions"""
    match = models.ForeignKey(
        Match, 
        on_delete=models.CASCADE,
        related_name='predictions'
    )
    baseline = models.CharField(
        max_length=1,
        choices=[('3', 'Team A'), ('1', 'Draw'), ('0', 'Team B')],
        help_text="Baseline prediction: Higher probability wins"
    )
    profitable = models.CharField(
        max_length=1,
        choices=[('3', 'Team A'), ('1', 'Draw'), ('0', 'Team B')],
        help_text="Profitable prediction: Compare implied probability vs odds"
    )
    balanced = models.CharField(
        max_length=1,
        choices=[('3', 'Team A'), ('1', 'Draw'), ('0', 'Team B')],
        help_text="Balanced prediction: Combine probability + odds"
    )
    ai_baseline = models.CharField(
        max_length=1,
        blank=True,
        null=True,
        choices=[('3', 'Team A'), ('1', 'Draw'), ('0', 'Team B')],
        help_text="AI-generated baseline prediction"
    )
    ai_profitable = models.CharField(
        max_length=1,
        blank=True,
        null=True,
        choices=[('3', 'Team A'), ('1', 'Draw'), ('0', 'Team B')],
        help_text="AI-generated profitable prediction"
    )
    ai_balanced = models.CharField(
        max_length=1,
        blank=True,
        null=True,
        choices=[('3', 'Team A'), ('1', 'Draw'), ('0', 'Team B')],
        help_text="AI-generated balanced prediction"
    )
    # Store full API response data for analysis
    api_response_data = models.JSONField(
        blank=True,
        null=True,
        help_text="Full API response from DeepSeek for detailed analysis"
    )
    # Accuracy tracking
    is_correct = models.BooleanField(
        blank=True,
        null=True,
        help_text="Whether the prediction was correct (after match result is known)"
    )
    prediction_type_used = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Which prediction type was used (baseline, profitable, balanced)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['match']

    def __str__(self):
        return f"{self.match} - B:{self.baseline} P:{self.profitable} BL:{self.balanced}"

    @property
    def baseline_correct(self):
        """Check if baseline prediction was correct"""
        if self.match.actual_result:
            return self.baseline == self.match.actual_result
        return None

    @property
    def profitable_correct(self):
        """Check if profitable prediction was correct"""
        if self.match.actual_result:
            return self.profitable == self.match.actual_result
        return None

    @property
    def balanced_correct(self):
        """Check if balanced prediction was correct"""
        if self.match.actual_result:
            return self.balanced == self.match.actual_result
        return None
    
    def update_accuracy(self):
        """Update accuracy based on actual match result"""
        if self.match.actual_result:
            # Check which prediction type to use (prioritize AI if available)
            prediction_value = None
            prediction_type = None
            
            if self.ai_balanced:
                prediction_value = self.ai_balanced
                prediction_type = 'ai_balanced'
            elif self.ai_profitable:
                prediction_value = self.ai_profitable
                prediction_type = 'ai_profitable'
            elif self.ai_baseline:
                prediction_value = self.ai_baseline
                prediction_type = 'ai_baseline'
            elif self.balanced:
                prediction_value = self.balanced
                prediction_type = 'balanced'
            elif self.profitable:
                prediction_value = self.profitable
                prediction_type = 'profitable'
            elif self.baseline:
                prediction_value = self.baseline
                prediction_type = 'baseline'
            
            if prediction_value:
                self.is_correct = (prediction_value == self.match.actual_result)
                self.prediction_type_used = prediction_type
                self.save(update_fields=['is_correct', 'prediction_type_used'])
    
    @classmethod
    def get_accuracy_stats(cls):
        """Get overall accuracy statistics"""
        total = cls.objects.filter(is_correct__isnull=False).count()
        if total == 0:
            return {
                'total': 0,
                'correct': 0,
                'incorrect': 0,
                'accuracy_percent': 0.0,
                'by_type': {}
            }
        
        correct = cls.objects.filter(is_correct=True).count()
        incorrect = cls.objects.filter(is_correct=False).count()
        
        # Accuracy by prediction type
        by_type = {}
        for pred_type in ['baseline', 'profitable', 'balanced', 'ai_baseline', 'ai_profitable', 'ai_balanced']:
            type_total = cls.objects.filter(prediction_type_used=pred_type, is_correct__isnull=False).count()
            if type_total > 0:
                type_correct = cls.objects.filter(prediction_type_used=pred_type, is_correct=True).count()
                by_type[pred_type] = {
                    'total': type_total,
                    'correct': type_correct,
                    'accuracy_percent': round((type_correct / type_total) * 100, 2)
                }
        
        return {
            'total': total,
            'correct': correct,
            'incorrect': incorrect,
            'accuracy_percent': round((correct / total) * 100, 2),
            'by_type': by_type
        }

