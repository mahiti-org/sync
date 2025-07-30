import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
app = Celery('your_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Add to your_project/__init__.py:
from .celery import app as celery_app
__all__ = ('celery_app',)

# Start Celery worker:
celery -A your_project worker -l info

# Start Celery beat (for scheduled tasks):
celery -A your_project beat -l info