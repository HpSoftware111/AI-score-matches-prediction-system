from django.contrib import admin
from .models import Prediction
from .engine import PredictionEngine
from django.utils.html import format_html


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = [
        'match_display', 
        'baseline', 
        'profitable', 
        'balanced',
        'accuracy_display',
        'created_at'
    ]
    list_filter = ['created_at', 'baseline', 'profitable', 'balanced']
    search_fields = ['match__team_a__name', 'match__team_b__name']
    readonly_fields = ['created_at', 'updated_at', 'ai_baseline', 'ai_profitable', 'ai_balanced']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Match', {
            'fields': ('match',)
        }),
        ('Rule-based Predictions', {
            'fields': ('baseline', 'profitable', 'balanced')
        }),
        ('AI Predictions', {
            'fields': ('ai_baseline', 'ai_profitable', 'ai_balanced'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['generate_predictions', 'generate_ai_predictions']
    
    def match_display(self, obj):
        return str(obj.match)
    match_display.short_description = 'Match'
    
    def accuracy_display(self, obj):
        if obj.match.actual_result:
            baseline = '✓' if obj.baseline_correct else '✗'
            profitable = '✓' if obj.profitable_correct else '✗'
            balanced = '✓' if obj.balanced_correct else '✗'
            return format_html(
                'B:{} P:{} BL:{}',
                baseline, profitable, balanced
            )
        return '-'
    accuracy_display.short_description = 'Accuracy'
    
    def generate_predictions(self, request, queryset):
        """Generate rule-based predictions for selected predictions"""
        engine = PredictionEngine(use_ai=False)
        count = 0
        
        for pred in queryset:
            predictions = engine.generate_prediction(pred.match, use_ai=False)
            pred.baseline = predictions['baseline']
            pred.profitable = predictions['profitable']
            pred.balanced = predictions['balanced']
            pred.save()
            count += 1
        
        self.message_user(request, f"Generated {count} predictions.")
    generate_predictions.short_description = "Regenerate rule-based predictions"
    
    def generate_ai_predictions(self, request, queryset):
        """Generate AI predictions for selected predictions"""
        engine = PredictionEngine(use_ai=True)
        count = 0
        
        for pred in queryset:
            predictions = engine.generate_prediction(pred.match, use_ai=True)
            pred.ai_baseline = predictions['ai_baseline']
            pred.ai_profitable = predictions['ai_profitable']
            pred.ai_balanced = predictions['ai_balanced']
            pred.save()
            count += 1
        
        self.message_user(request, f"Generated AI predictions for {count} predictions.")
    generate_ai_predictions.short_description = "Generate AI predictions (DeepSeek)"

