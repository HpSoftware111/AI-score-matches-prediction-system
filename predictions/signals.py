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


@receiver(post_save, sender=Match)
def update_prediction_accuracy(sender, instance, **kwargs):
    """
    Update prediction accuracy when match result is set or updated
    """
    if instance.actual_result:
        predictions = Prediction.objects.filter(match=instance)
        for pred in predictions:
            pred.update_accuracy()
