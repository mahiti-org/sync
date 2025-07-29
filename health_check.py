from django.http import JsonResponse
from django.views import View
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
import time
import os

class HealthCheckView(View):
    """Health check endpoint for monitoring"""
    
    def get(self, request):
        health_status = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'checks': {}
        }
        
        # Database check
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_status['checks']['database'] = 'healthy'
        except Exception as e:
            health_status['checks']['database'] = f'error: {str(e)}'
            health_status['status'] = 'unhealthy'
        
        # Cache check
        try:
            cache.set('health_check', 'test', timeout=10)
            if cache.get('health_check') == 'test':
                health_status['checks']['cache'] = 'healthy'
            else:
                health_status['checks']['cache'] = 'error: cache not working'
                health_status['status'] = 'degraded'
        except Exception as e:
            health_status['checks']['cache'] = f'error: {str(e)}'
            health_status['status'] = 'degraded'
        
        # Log file check
        try:
            log_dir = getattr(settings, 'SB_SYNC_LOG_DIR', 'logs')
            if os.path.exists(log_dir) and os.access(log_dir, os.W_OK):
                health_status['checks']['logging'] = 'healthy'
            else:
                health_status['checks']['logging'] = 'error: log directory not writable'
                health_status['status'] = 'degraded'
        except Exception as e:
            health_status['checks']['logging'] = f'error: {str(e)}'
            health_status['status'] = 'degraded'
        
        return JsonResponse(health_status)
