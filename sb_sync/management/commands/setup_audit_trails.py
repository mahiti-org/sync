"""
Management command to setup Django Simple History for audit trails
"""
from django.core.management.base import BaseCommand
from django.apps import apps
from django.conf import settings
from simple_history import register


class Command(BaseCommand):
    help = 'Setup Django Simple History for audit trails'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['setup', 'check', 'cleanup'],
            default='setup',
            help='Action to perform'
        )
        parser.add_argument(
            '--model',
            type=str,
            help='Specific model to setup (optional)'
        )

    def handle(self, *args, **options):
        action = options['action']
        model_name = options.get('model')

        if action == 'setup':
            self.setup_audit_trails(model_name)
        elif action == 'check':
            self.check_audit_trails(model_name)
        elif action == 'cleanup':
            self.cleanup_audit_trails(model_name)

    def setup_audit_trails(self, model_name=None):
        """Setup audit trails for sync models"""
        self.stdout.write(
            self.style.SUCCESS('🔍 Setting up audit trails...')
        )

        # Sync models that should have audit trails
        sync_models = [
            'sb_sync.SyncLog',
            'sb_sync.SyncMetadata',
            'sb_sync.PerformanceMetrics',
            'sb_sync.Organization',
            'sb_sync.UserOrganization',
            'sb_sync.ModelPermission',
            'sb_sync.UserSyncMetadata',
            'sb_sync.DataFilter',
        ]

        if model_name:
            sync_models = [model_name]

        for model_path in sync_models:
            try:
                app_label, model_name_short = model_path.split('.')
                model = apps.get_model(app_label, model_name_short)
                
                # Check if model already has history
                if hasattr(model, 'history'):
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  {model_path} already has audit trails')
                    )
                else:
                    # Register the model with Simple History
                    register(model)
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {model_path} audit trails enabled')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error setting up {model_path}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS('🎉 Audit trails setup complete!')
        )

    def check_audit_trails(self, model_name=None):
        """Check audit trails status"""
        self.stdout.write(
            self.style.SUCCESS('🔍 Checking audit trails status...')
        )

        sync_models = [
            'sb_sync.SyncLog',
            'sb_sync.SyncMetadata',
            'sb_sync.PerformanceMetrics',
            'sb_sync.Organization',
            'sb_sync.UserOrganization',
            'sb_sync.ModelPermission',
            'sb_sync.UserSyncMetadata',
            'sb_sync.DataFilter',
        ]

        if model_name:
            sync_models = [model_name]

        for model_path in sync_models:
            try:
                app_label, model_name_short = model_path.split('.')
                model = apps.get_model(app_label, model_name_short)
                
                if hasattr(model, 'history'):
                    history_count = model.history.count()
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {model_path}: {history_count} history records')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  {model_path}: No audit trails')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error checking {model_path}: {str(e)}')
                )

    def cleanup_audit_trails(self, model_name=None):
        """Cleanup old audit trail records"""
        self.stdout.write(
            self.style.SUCCESS('🧹 Cleaning up old audit trail records...')
        )

        sync_models = [
            'sb_sync.SyncLog',
            'sb_sync.SyncMetadata',
            'sb_sync.PerformanceMetrics',
            'sb_sync.Organization',
            'sb_sync.UserOrganization',
            'sb_sync.ModelPermission',
            'sb_sync.UserSyncMetadata',
            'sb_sync.DataFilter',
        ]

        if model_name:
            sync_models = [model_name]

        for model_path in sync_models:
            try:
                app_label, model_name_short = model_path.split('.')
                model = apps.get_model(app_label, model_name_short)
                
                if hasattr(model, 'history'):
                    # Keep only last 1000 history records per model
                    total_records = model.history.count()
                    if total_records > 1000:
                        records_to_delete = total_records - 1000
                        model.history.order_by('history_date')[:records_to_delete].delete()
                        self.stdout.write(
                            self.style.SUCCESS(f'✅ {model_path}: Cleaned up {records_to_delete} old records')
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(f'✅ {model_path}: No cleanup needed ({total_records} records)')
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  {model_path}: No audit trails to cleanup')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error cleaning up {model_path}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS('🎉 Audit trails cleanup complete!')
        ) 