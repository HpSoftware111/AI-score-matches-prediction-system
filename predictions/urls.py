from django.urls import path
from . import views

app_name = 'predictions'

urlpatterns = [
    path('weekly/', views.weekly_predictions, name='weekly_predictions'),
    path('generate/<int:match_id>/', views.generate_predictions_view, name='generate_predictions'),
    path('analysis/<int:match_id>/', views.prediction_detail_with_analysis, name='prediction_analysis'),
    path('batch/', views.batch_predictions, name='batch_predictions'),
    path('accuracy/', views.accuracy_stats, name='accuracy_stats'),
]

