"""
Management command for automatic migration detection and execution.
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from sb_sync.migration_utils import AutoMigrator, MigrationDetector


class Command(BaseCommand):
    help = 'Automatically detect and execute migrations for sb-sync'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without executing',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force migration even if not needed',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed migration information',
        )

    def handle(self, *args, **options):
        detector = MigrationDetector()
        migrator = AutoMigrator()
        
        current_version = detector.detect_current_version()
        schema_changes = detector.detect_schema_changes()
        
        self.stdout.write(
            self.style.SUCCESS(f'Current version detected: {current_version}')
        )
        
        if options['verbose']:
            self.stdout.write(
                self.style.WARNING(f'Schema changes needed: {schema_changes}')
            )
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('DRY RUN - No changes will be made')
            )
            if migrator.needs_migration():
                self.stdout.write(
                    self.style.SUCCESS('Migration would be executed')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('No migration needed')
                )
            return
        
        if not migrator.needs_migration() and not options['force']:
            self.stdout.write(
                self.style.SUCCESS('No migration needed')
            )
            return
        
        self.stdout.write(
            self.style.WARNING('Starting automatic migration...')
        )
        
        try:
            success = migrator.auto_migrate()
            if success:
                self.stdout.write(
                    self.style.SUCCESS('Automatic migration completed successfully')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('Automatic migration failed')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Migration error: {e}')
            )
