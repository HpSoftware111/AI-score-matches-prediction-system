from django.db import models
from django.contrib.auth.models import User
from predictions.models import Prediction


class AnalyticsSnapshot(models.Model):
    """Store periodic analytics snapshots for historical tracking"""
    date = models.DateField(auto_now_add=True)
    total_predictions = models.IntegerField(default=0)
    baseline_accuracy = models.FloatField(default=0.0)
    profitable_accuracy = models.FloatField(default=0.0)
    balanced_accuracy = models.FloatField(default=0.0)
    baseline_wins = models.IntegerField(default=0)
    profitable_wins = models.IntegerField(default=0)
    balanced_wins = models.IntegerField(default=0)
    total_matches_with_results = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = "Analytics Snapshots"
    
    def __str__(self):
        return f"Analytics Snapshot - {self.date}"

