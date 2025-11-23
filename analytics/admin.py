from django.contrib import admin
from .models import AnalyticsSnapshot


@admin.register(AnalyticsSnapshot)
class AnalyticsSnapshotAdmin(admin.ModelAdmin):
    list_display = [
        'date',
        'total_predictions',
        'baseline_accuracy',
        'profitable_accuracy',
        'balanced_accuracy',
        'total_matches_with_results'
    ]
    readonly_fields = ['date']
    list_filter = ['date']
    date_hierarchy = 'date'

