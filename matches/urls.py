from django.urls import path
from . import views

app_name = 'matches'

urlpatterns = [
    path('', views.home, name='home'),
    path('matches/', views.match_list, name='match_list'),
    path('matches/create/', views.match_create, name='match_create'),
    path('matches/bulk-delete/', views.match_bulk_delete, name='match_bulk_delete'),
    path('matches/<int:pk>/', views.match_detail, name='match_detail'),
    path('matches/<int:pk>/edit/', views.match_update, name='match_update'),
    path('matches/<int:pk>/delete/', views.match_delete, name='match_delete'),
    path('import/', views.import_matches, name='import_matches'),
]

