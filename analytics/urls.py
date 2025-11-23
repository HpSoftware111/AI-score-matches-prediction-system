from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.analytics_dashboard, name='dashboard'),
    path('accuracy/', views.accuracy_tracking, name='accuracy_tracking'),
]

