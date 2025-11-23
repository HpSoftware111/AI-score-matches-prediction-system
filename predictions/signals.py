"""
Signals to auto-generate predictions when matches are created/updated
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from matches.models import Match
from .models import Prediction
from .engine import PredictionEngine


@receiver(post_save, sender=Match)
def auto_generate_predictions(sender, instance, created, **kwargs):
    """
    Auto-generate predictions when a match is created
    Can be disabled in settings if needed
    """
    from django.conf import settings
    if getattr(settings, 'AUTO_GENERATE_PREDICTIONS', False):
        if created and not Prediction.objects.filter(match=instance).exists():
            engine = PredictionEngine(use_ai=False)
            predictions = engine.generate_prediction(instance, use_ai=False)
            Prediction.objects.create(match=instance, **predictions)

