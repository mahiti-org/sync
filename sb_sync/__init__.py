__version__ = '2.0.2'

# sb_sync/apps.py
from django.apps import AppConfig
import logging
from logging.handlers import TimedRotatingFileHandler
import os
from django.conf import settings

class SbSyncConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sb_sync'
    
    def ready(self):
        # Setup rotating log file
        log_dir = getattr(settings, 'SB_SYNC_LOG_DIR', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure sync logger
        sync_logger = logging.getLogger('sb_sync')
        sync_logger.setLevel(logging.INFO)
        
        # Daily rotating file handler
        handler = TimedRotatingFileHandler(
            os.path.join(log_dir, 'sb_sync.log'),
            when='midnight',
            interval=1,
            backupCount=30
        )
        handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        if not sync_logger.handlers:
            sync_logger.addHandler(handler)
