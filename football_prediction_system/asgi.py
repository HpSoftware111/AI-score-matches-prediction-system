"""
ASGI config for football_prediction_system project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'football_prediction_system.settings')

application = get_asgi_application()

