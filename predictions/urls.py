from django.urls import path
from . import views

app_name = 'predictions'

urlpatterns = [
    path('weekly/', views.weekly_predictions, name='weekly_predictions'),
    path('generate/<int:match_id>/', views.generate_predictions_view, name='generate_predictions'),
]

