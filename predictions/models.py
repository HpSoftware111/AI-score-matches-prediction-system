from django.db import models
from matches.models import Match


class Prediction(models.Model):
    """Prediction model for storing AI-generated predictions"""
    match = models.ForeignKey(
        Match, 
        on_delete=models.CASCADE,
        related_name='predictions'
    )
    baseline = models.CharField(
        max_length=1,
        choices=[('1', 'Team A'), ('3', 'Team B'), ('0', 'Draw')],
        help_text="Baseline prediction: Higher probability wins"
    )
    profitable = models.CharField(
        max_length=1,
        choices=[('1', 'Team A'), ('3', 'Team B'), ('0', 'Draw')],
        help_text="Profitable prediction: Compare implied probability vs odds"
    )
    balanced = models.CharField(
        max_length=1,
        choices=[('1', 'Team A'), ('3', 'Team B'), ('0', 'Draw')],
        help_text="Balanced prediction: Combine probability + odds"
    )
    ai_baseline = models.CharField(
        max_length=1,
        blank=True,
        null=True,
        choices=[('1', 'Team A'), ('3', 'Team B'), ('0', 'Draw')],
        help_text="AI-generated baseline prediction"
    )
    ai_profitable = models.CharField(
        max_length=1,
        blank=True,
        null=True,
        choices=[('1', 'Team A'), ('3', 'Team B'), ('0', 'Draw')],
        help_text="AI-generated profitable prediction"
    )
    ai_balanced = models.CharField(
        max_length=1,
        blank=True,
        null=True,
        choices=[('1', 'Team A'), ('3', 'Team B'), ('0', 'Draw')],
        help_text="AI-generated balanced prediction"
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

