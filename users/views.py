from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .models import User


@login_required
def profile(request):
    """User profile view"""
    context = {
        'user': request.user,
        'title': 'Profile'
    }
    return render(request, 'users/profile.html', context)

