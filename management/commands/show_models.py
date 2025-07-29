"""
Management command to show model discovery status and default models
"""
from django.core.management.base import BaseCommand
from django.apps import apps
from sb_sync.config import get_config, get_all_models, get_default_models, is_model_enabled, get_config_summary
from sb_sync.utils import ModelIntrospector


class Command(BaseCommand):
    help = 'Show model discovery status and default models for sync operations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['summary', 'all', 'enabled', 'disabled', 'default', 'details'],
            default='summary',
            help='Action to perform'
        )
        parser.add_argument(
            '--app-label',
            type=str,
            help='Show models from specific app only'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show verbose output'
        )

    def handle(self, *args, **options):
        action = options['action']
        app_label = options.get('app_label')
        verbose = options.get('verbose', False)
        
        if action == 'summary':
            self.show_summary()
        elif action == 'all':
            self.show_all_models(app_label, verbose)
        elif action == 'enabled':
            self.show_enabled_models(app_label, verbose)
        elif action == 'disabled':
            self.show_disabled_models(app_label, verbose)
        elif action == 'default':
            self.show_default_models(verbose)
        elif action == 'details':
            self.show_model_details(app_label, verbose)

    def show_summary(self):
        """Show configuration summary"""
        summary = get_config_summary()
        
        self.stdout.write(
            self.style.SUCCESS('📊 Model Discovery Summary')
        )
        self.stdout.write('=' * 50)
        
        self.stdout.write(f"🔍 Total Models Discovered: {summary['total_models_discovered']}")
        self.stdout.write(f"✅ Enabled Models: {summary['enabled_models']}")
        self.stdout.write(f"❌ Excluded Models: {summary['excluded_models']}")
        self.stdout.write(f"⚙️  Auto Discovery: {'Enabled' if summary['auto_discovery_enabled'] else 'Disabled'}")
        self.stdout.write(f"📦 Include Apps Count: {summary['include_apps_count']}")
        self.stdout.write(f"🚫 Exclude Models Count: {summary['exclude_models_count']}")

        self.stdout.write(f"🔐 Dynamic Permissions: {'Enabled' if summary['dynamic_permissions_enabled'] else 'Disabled'}")

    def show_all_models(self, app_label=None, verbose=False):
        """Show all discovered models"""
        all_models = get_all_models()
        
        if app_label:
            all_models = [model for model in all_models if model.startswith(f"{app_label}.")]
        
        self.stdout.write(
            self.style.SUCCESS(f'📋 All Discovered Models{f" (App: {app_label})" if app_label else ""}')
        )
        self.stdout.write('=' * 50)
        
        if not all_models:
            self.stdout.write(self.style.WARNING('No models discovered'))
            return
        
        for model_name in sorted(all_models):
            status = '✅' if is_model_enabled(model_name) else '❌'
            self.stdout.write(f"{status} {model_name}")
            
            if verbose:
                try:
                    model_class = apps.get_model(model_name)
                    field_count = len(model_class._meta.get_fields())
                    self.stdout.write(f"    Fields: {field_count}")
                except Exception as e:
                    self.stdout.write(f"    Error: {str(e)}")

    def show_enabled_models(self, app_label=None, verbose=False):
        """Show enabled models only"""
        all_models = get_all_models()
        enabled_models = [model for model in all_models if is_model_enabled(model)]
        
        if app_label:
            enabled_models = [model for model in enabled_models if model.startswith(f"{app_label}.")]
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Enabled Models{f" (App: {app_label})" if app_label else ""}')
        )
        self.stdout.write('=' * 50)
        
        if not enabled_models:
            self.stdout.write(self.style.WARNING('No enabled models found'))
            return
        
        for model_name in sorted(enabled_models):
            self.stdout.write(f"✅ {model_name}")
            
            if verbose:
                try:
                    model_class = apps.get_model(model_name)
                    field_count = len(model_class._meta.get_fields())
                    self.stdout.write(f"    Fields: {field_count}")
                except Exception as e:
                    self.stdout.write(f"    Error: {str(e)}")

    def show_disabled_models(self, app_label=None, verbose=False):
        """Show disabled/excluded models"""
        all_models = get_all_models()
        disabled_models = [model for model in all_models if not is_model_enabled(model)]
        
        if app_label:
            disabled_models = [model for model in disabled_models if model.startswith(f"{app_label}.")]
        
        self.stdout.write(
            self.style.WARNING(f'❌ Disabled/Excluded Models{f" (App: {app_label})" if app_label else ""}')
        )
        self.stdout.write('=' * 50)
        
        if not disabled_models:
            self.stdout.write(self.style.SUCCESS('No disabled models found'))
            return
        
        for model_name in sorted(disabled_models):
            self.stdout.write(f"❌ {model_name}")
            
            if verbose:
                # Show why it's disabled
                exclude_models = get_config('MODEL_DISCOVERY', 'EXCLUDE_MODELS')
                include_apps = get_config('MODEL_DISCOVERY', 'INCLUDE_APPS')
                
                if model_name in exclude_models:
                    self.stdout.write(f"    Reason: Explicitly excluded in configuration")
                elif include_apps and model_name.split('.')[0] not in include_apps:
                    self.stdout.write(f"    Reason: App not included in configuration")

    def show_default_models(self, verbose=False):
        """Show default models for push/pull operations"""
        default_models = get_default_models()
        
        self.stdout.write(
            self.style.SUCCESS('🎯 Default Models for Push/Pull Operations')
        )
        self.stdout.write('=' * 50)
        
        if not default_models:
            self.stdout.write(self.style.WARNING('No default models configured'))
            return
        
        for model_name in sorted(default_models):
            status = '✅' if is_model_enabled(model_name) else '❌'
            self.stdout.write(f"{status} {model_name}")
            
            if verbose:
                try:
                    model_class = apps.get_model(model_name)
                    field_count = len(model_class._meta.get_fields())
                    self.stdout.write(f"    Fields: {field_count}")
                    
                    # Show model configuration
                    model_config = get_config('MODEL_DISCOVERY')
                    self.stdout.write(f"    Push Enabled: {'Yes' if is_model_enabled(model_name) else 'No'}")
                    self.stdout.write(f"    Pull Enabled: {'Yes' if is_model_enabled(model_name) else 'No'}")
                    
                except Exception as e:
                    self.stdout.write(f"    Error: {str(e)}")

    def show_model_details(self, app_label=None, verbose=False):
        """Show detailed model information"""
        all_models = get_all_models()
        
        if app_label:
            all_models = [model for model in all_models if model.startswith(f"{app_label}.")]
        
        self.stdout.write(
            self.style.SUCCESS(f'🔍 Detailed Model Information{f" (App: {app_label})" if app_label else ""}')
        )
        self.stdout.write('=' * 50)
        
        if not all_models:
            self.stdout.write(self.style.WARNING('No models to show details for'))
            return
        
        for model_name in sorted(all_models):
            status = '✅' if is_model_enabled(model_name) else '❌'
            self.stdout.write(f"\n{status} {model_name}")
            
            try:
                model_class = apps.get_model(model_name)
                
                # Basic info
                self.stdout.write(f"    App: {model_class._meta.app_label}")
                self.stdout.write(f"    Table: {model_class._meta.db_table}")
                self.stdout.write(f"    Fields: {len(model_class._meta.get_fields())}")
                
                # Field details if verbose
                if verbose:
                    self.stdout.write("    Field Details:")
                    for field in model_class._meta.get_fields():
                        if hasattr(field, 'name'):
                            field_type = field.__class__.__name__
                            required = "Required" if not field.null and not field.blank else "Optional"
                            self.stdout.write(f"      - {field.name}: {field_type} ({required})")
                
                # Configuration info
                exclude_models = get_config('MODEL_DISCOVERY', 'EXCLUDE_MODELS')
                include_apps = get_config('MODEL_DISCOVERY', 'INCLUDE_APPS')
                
                if model_name in exclude_models:
                    self.stdout.write(f"    ⚠️  Explicitly excluded in configuration")
                elif include_apps and model_name.split('.')[0] not in include_apps:
                    self.stdout.write(f"    ⚠️  App not included in configuration")
                else:
                    self.stdout.write(f"    ✅ Available for sync operations")
                
            except Exception as e:
                self.stdout.write(f"    Error: {str(e)}")

    def show_configuration_info(self):
        """Show current configuration settings"""
        self.stdout.write(
            self.style.SUCCESS('⚙️  Model Discovery Configuration')
        )
        self.stdout.write('=' * 50)
        
        model_discovery_config = get_config('MODEL_DISCOVERY')
        
        self.stdout.write(f"Auto Discover Models: {model_discovery_config['AUTO_DISCOVER_MODELS']}")
        self.stdout.write(f"Include Custom Models: {model_discovery_config['INCLUDE_CUSTOM_MODELS']}")
        self.stdout.write(f"Model Prefix: '{model_discovery_config['MODEL_PREFIX']}'")
        self.stdout.write(f"Model Suffix: '{model_discovery_config['MODEL_SUFFIX']}'")
        self.stdout.write(f"Model Namespace: '{model_discovery_config['MODEL_NAMESPACE']}'")
        
        self.stdout.write(f"\nIncluded Apps ({len(model_discovery_config['INCLUDE_APPS'])}):")
        if model_discovery_config['INCLUDE_APPS']:
            for app in sorted(model_discovery_config['INCLUDE_APPS']):
                self.stdout.write(f"  - {app}")
        else:
            self.stdout.write("  (All apps included by default)")
        
        self.stdout.write(f"\nExcluded Models ({len(model_discovery_config['EXCLUDE_MODELS'])}):")
        for model in sorted(model_discovery_config['EXCLUDE_MODELS']):
            self.stdout.write(f"  - {model}") 