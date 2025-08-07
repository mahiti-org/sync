"""
Management command to configure advanced model discovery options
"""
from django.core.management.base import BaseCommand, CommandError
from django.apps import apps
from sb_sync.config import SyncConfig
import json


class Command(BaseCommand):
    help = 'Configure advanced model discovery options for sb-sync'

    def add_arguments(self, parser):
        parser.add_argument(
            '--list-current',
            action='store_true',
            help='List current model discovery configuration',
        )
        parser.add_argument(
            '--set-include-apps',
            nargs='+',
            help='Set apps to include for model discovery',
        )
        parser.add_argument(
            '--set-exclude-models',
            nargs='+',
            help='Set models to exclude from discovery',
        )
        parser.add_argument(
            '--set-exclude-patterns',
            nargs='+',
            help='Set regex patterns for models to exclude',
        )
        parser.add_argument(
            '--set-include-patterns',
            nargs='+',
            help='Set regex patterns for models to include',
        )
        parser.add_argument(
            '--set-exclude-fields',
            nargs='+',
            help='Set field names that will exclude models',
        )
        parser.add_argument(
            '--set-require-fields',
            nargs='+',
            help='Set field names that models must have',
        )
        parser.add_argument(
            '--set-model-types',
            nargs='+',
            choices=['concrete', 'abstract', 'proxy'],
            help='Set model types to include',
        )
        parser.add_argument(
            '--set-app-exclusions',
            type=json.loads,
            help='Set app-specific exclusions as JSON',
        )
        parser.add_argument(
            '--enable-caching',
            action='store_true',
            help='Enable discovery caching',
        )
        parser.add_argument(
            '--disable-caching',
            action='store_true',
            help='Disable discovery caching',
        )
        parser.add_argument(
            '--set-cache-timeout',
            type=int,
            help='Set discovery cache timeout in seconds',
        )
        parser.add_argument(
            '--set-max-models',
            type=int,
            help='Set maximum models per app',
        )
        parser.add_argument(
            '--test-discovery',
            action='store_true',
            help='Test model discovery with current settings',
        )
        parser.add_argument(
            '--reset-to-defaults',
            action='store_true',
            help='Reset model discovery to default settings',
        )

    def handle(self, *args, **options):
        if options['list_current']:
            self.list_current_config()
        elif options['set_include_apps'] is not None:
            self.set_include_apps(options['set_include_apps'])
        elif options['set_exclude_models'] is not None:
            self.set_exclude_models(options['set_exclude_models'])
        elif options['set_exclude_patterns'] is not None:
            self.set_exclude_patterns(options['set_exclude_patterns'])
        elif options['set_include_patterns'] is not None:
            self.set_include_patterns(options['set_include_patterns'])
        elif options['set_exclude_fields'] is not None:
            self.set_exclude_fields(options['set_exclude_fields'])
        elif options['set_require_fields'] is not None:
            self.set_require_fields(options['set_require_fields'])
        elif options['set_model_types'] is not None:
            self.set_model_types(options['set_model_types'])
        elif options['set_app_exclusions'] is not None:
            self.set_app_exclusions(options['set_app_exclusions'])
        elif options['enable_caching']:
            self.set_caching(True)
        elif options['disable_caching']:
            self.set_caching(False)
        elif options['set_cache_timeout'] is not None:
            self.set_cache_timeout(options['set_cache_timeout'])
        elif options['set_max_models'] is not None:
            self.set_max_models(options['set_max_models'])
        elif options['test_discovery']:
            self.test_discovery()
        elif options['reset_to_defaults']:
            self.reset_to_defaults()
        else:
            self.list_current_config()

    def list_current_config(self):
        """List current model discovery configuration"""
        self.stdout.write(self.style.SUCCESS('Current Model Discovery Configuration:'))
        self.stdout.write('=' * 50)
        
        config = SyncConfig.get_config('MODEL_DISCOVERY')
        
        self.stdout.write(f"Auto Discover Models: {config.get('AUTO_DISCOVER_MODELS', True)}")
        self.stdout.write(f"Include Apps: {config.get('INCLUDE_APPS', [])}")
        self.stdout.write(f"Exclude Models: {config.get('EXCLUDE_MODELS', [])}")
        self.stdout.write(f"Exclude Abstract Models: {config.get('EXCLUDE_ABSTRACT_MODELS', True)}")
        self.stdout.write(f"Exclude Proxy Models: {config.get('EXCLUDE_PROXY_MODELS', True)}")
        self.stdout.write(f"Exclude Historical Models: {config.get('EXCLUDE_HISTORICAL_MODELS', True)}")
        self.stdout.write(f"Include Model Patterns: {config.get('INCLUDE_MODEL_PATTERNS', [])}")
        self.stdout.write(f"Exclude Model Patterns: {config.get('EXCLUDE_MODEL_PATTERNS', [])}")
        self.stdout.write(f"Exclude Models With Fields: {config.get('EXCLUDE_MODELS_WITH_FIELDS', [])}")
        self.stdout.write(f"Require Models With Fields: {config.get('REQUIRE_MODELS_WITH_FIELDS', [])}")
        self.stdout.write(f"Include Model Types: {config.get('INCLUDE_MODEL_TYPES', ['concrete'])}")
        self.stdout.write(f"App Specific Exclusions: {config.get('APP_SPECIFIC_EXCLUSIONS', {})}")
        self.stdout.write(f"Enable Discovery Caching: {config.get('ENABLE_DISCOVERY_CACHING', True)}")
        self.stdout.write(f"Discovery Cache Timeout: {config.get('DISCOVERY_CACHE_TIMEOUT', 3600)}")
        self.stdout.write(f"Max Models Per App: {config.get('MAX_MODELS_PER_APP', 100)}")

    def set_include_apps(self, apps_list):
        """Set apps to include for model discovery"""
        SyncConfig.set_config('MODEL_DISCOVERY', 'INCLUDE_APPS', apps_list)
        self.stdout.write(
            self.style.SUCCESS(f'Set include apps to: {apps_list}')
        )

    def set_exclude_models(self, models_list):
        """Set models to exclude from discovery"""
        SyncConfig.set_config('MODEL_DISCOVERY', 'EXCLUDE_MODELS', models_list)
        self.stdout.write(
            self.style.SUCCESS(f'Set exclude models to: {models_list}')
        )

    def set_exclude_patterns(self, patterns_list):
        """Set regex patterns for models to exclude"""
        SyncConfig.set_config('MODEL_DISCOVERY', 'EXCLUDE_MODEL_PATTERNS', patterns_list)
        self.stdout.write(
            self.style.SUCCESS(f'Set exclude patterns to: {patterns_list}')
        )

    def set_include_patterns(self, patterns_list):
        """Set regex patterns for models to include"""
        SyncConfig.set_config('MODEL_DISCOVERY', 'INCLUDE_MODEL_PATTERNS', patterns_list)
        self.stdout.write(
            self.style.SUCCESS(f'Set include patterns to: {patterns_list}')
        )

    def set_exclude_fields(self, fields_list):
        """Set field names that will exclude models"""
        SyncConfig.set_config('MODEL_DISCOVERY', 'EXCLUDE_MODELS_WITH_FIELDS', fields_list)
        self.stdout.write(
            self.style.SUCCESS(f'Set exclude fields to: {fields_list}')
        )

    def set_require_fields(self, fields_list):
        """Set field names that models must have"""
        SyncConfig.set_config('MODEL_DISCOVERY', 'REQUIRE_MODELS_WITH_FIELDS', fields_list)
        self.stdout.write(
            self.style.SUCCESS(f'Set require fields to: {fields_list}')
        )

    def set_model_types(self, types_list):
        """Set model types to include"""
        SyncConfig.set_config('MODEL_DISCOVERY', 'INCLUDE_MODEL_TYPES', types_list)
        self.stdout.write(
            self.style.SUCCESS(f'Set model types to: {types_list}')
        )

    def set_app_exclusions(self, exclusions_dict):
        """Set app-specific exclusions"""
        SyncConfig.set_config('MODEL_DISCOVERY', 'APP_SPECIFIC_EXCLUSIONS', exclusions_dict)
        self.stdout.write(
            self.style.SUCCESS(f'Set app exclusions to: {exclusions_dict}')
        )

    def set_caching(self, enabled):
        """Enable or disable discovery caching"""
        SyncConfig.set_config('MODEL_DISCOVERY', 'ENABLE_DISCOVERY_CACHING', enabled)
        status = 'enabled' if enabled else 'disabled'
        self.stdout.write(
            self.style.SUCCESS(f'Discovery caching {status}')
        )

    def set_cache_timeout(self, timeout):
        """Set discovery cache timeout"""
        SyncConfig.set_config('MODEL_DISCOVERY', 'DISCOVERY_CACHE_TIMEOUT', timeout)
        self.stdout.write(
            self.style.SUCCESS(f'Set cache timeout to: {timeout} seconds')
        )

    def set_max_models(self, max_models):
        """Set maximum models per app"""
        SyncConfig.set_config('MODEL_DISCOVERY', 'MAX_MODELS_PER_APP', max_models)
        self.stdout.write(
            self.style.SUCCESS(f'Set max models per app to: {max_models}')
        )

    def test_discovery(self):
        """Test model discovery with current settings"""
        from sb_sync.config import get_all_models
        
        self.stdout.write(self.style.SUCCESS('Testing Model Discovery:'))
        self.stdout.write('=' * 30)
        
        try:
            models = get_all_models()
            self.stdout.write(f'Discovered {len(models)} models:')
            for model in models:
                self.stdout.write(f'  - {model}')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during discovery: {str(e)}')
            )

    def reset_to_defaults(self):
        """Reset model discovery to default settings"""
        # Reset to default configuration
        default_config = {
            'AUTO_DISCOVER_MODELS': True,
            'INCLUDE_APPS': [],
            'EXCLUDE_MODELS': [
                'sb_sync.SyncLog',
                'sb_sync.SyncMetadata',
                'sb_sync.PerformanceMetrics',
                'sb_sync.Organization',
                'sb_sync.UserOrganization',
                'sb_sync.ModelPermission',
                'sb_sync.UserSyncMetadata',
                'sb_sync.DataFilter',
            ],
            'EXCLUDE_ABSTRACT_MODELS': True,
            'EXCLUDE_PROXY_MODELS': True,
            'EXCLUDE_HISTORICAL_MODELS': True,
            'EXCLUDE_MANAGER_MODELS': True,
            'INCLUDE_MODEL_PATTERNS': [],
            'EXCLUDE_MODEL_PATTERNS': [
                r'^.*\.Historical.*$',
                r'^.*\.Log$',
                r'^.*\.Cache$',
                r'^.*\.Session$',
                r'^.*\.Permission$',
            ],
            'EXCLUDE_MODELS_WITH_FIELDS': ['created_at', 'updated_at', 'deleted_at'],
            'REQUIRE_MODELS_WITH_FIELDS': [],
            'APP_SPECIFIC_EXCLUSIONS': {
                'auth': ['Group', 'Permission'],
                'admin': ['LogEntry'],
            },
            'INCLUDE_MODEL_TYPES': ['concrete'],
            'ENABLE_DISCOVERY_CACHING': True,
            'DISCOVERY_CACHE_TIMEOUT': 3600,
            'MAX_MODELS_PER_APP': 100,
        }
        
        for key, value in default_config.items():
            SyncConfig.set_config('MODEL_DISCOVERY', key, value)
        
        self.stdout.write(
            self.style.SUCCESS('Reset model discovery to default settings')
        )
