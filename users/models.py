from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Extended user model with roles"""
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('analyst', 'Analyst'),
        ('bettor', 'Bettor'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='bettor'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_admin_user(self):
        return self.role == 'admin' or self.is_superuser
    
    def is_analyst(self):
        return self.role == 'analyst' or self.is_admin_user()

