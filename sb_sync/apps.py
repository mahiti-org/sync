from django.apps import AppConfig
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from django.conf import settings


class SbSyncConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sb_sync'

    def ready(self):
        # Configure logging with daily rotation
        log_dir = os.path.join(settings.BASE_DIR, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'sb_sync.log')

        logger = logging.getLogger('sb_sync')
        logger.setLevel(logging.INFO)

        handler = TimedRotatingFileHandler(
            log_file,
            when='midnight',
            interval=1,
            backupCount=7
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Setup auto-migration on startup
        try:
            from .migration_utils import setup_auto_migration
            setup_auto_migration()
        except Exception as e:
            logger.error(f"Failed to setup auto-migration: {e}")
