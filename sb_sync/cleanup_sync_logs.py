from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from sb_sync.models import SyncLog

class Command(BaseCommand):
    help = 'Clean up old sync logs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days to keep logs (default: 90)'
        )

    def handle(self, *args, **options):
        cutoff_date = timezone.now() - timedelta(days=options['days'])
        deleted_count = SyncLog.objects.filter(timestamp__lt=cutoff_date).delete()[0]
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully deleted {deleted_count} old sync log entries'
            )
        )
