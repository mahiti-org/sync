from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import json
import os
from pathlib import Path
from ...config import SyncConfig, get_config_summary


class Command(BaseCommand):
    help = 'Manage sb-sync configuration settings'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            type=str,
            choices=['show', 'export', 'import', 'validate', 'summary', 'reset'],
            help='Action to perform'
        )
        parser.add_argument(
            '--file',
            type=str,
            help='File path for export/import operations'
        )
        parser.add_argument(
            '--section',
            type=str,
            choices=['core', 'advanced', 'error', 'performance', 'security', 'all'],
            default='all',
            help='Configuration section to work with'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'yaml', 'env'],
            default='json',
            help='Output format'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force operation without confirmation'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        file_path = options['file']
        section = options['section']
        output_format = options['format']
        force = options['force']
        
        if action == 'show':
            self.show_config(section, output_format)
        elif action == 'export':
            self.export_config(file_path, section, output_format, force)
        elif action == 'import':
            self.import_config(file_path, force)
        elif action == 'validate':
            self.validate_config()
        elif action == 'summary':
            self.show_summary()
        elif action == 'reset':
            self.reset_config(force)
    
    def show_config(self, section, output_format):
        """Show current configuration"""
        self.stdout.write(f"Showing {section} configuration...")
        
        if section == 'all':
            config = SyncConfig.export_config()
        elif section == 'core':
            config = SyncConfig.CORE
        elif section == 'advanced':
            config = SyncConfig.ADVANCED
        elif section == 'error':
            config = SyncConfig.ERROR
        elif section == 'performance':
            config = SyncConfig.PERFORMANCE
        elif section == 'security':
            config = SyncConfig.SECURITY
        
        if output_format == 'json':
            self.stdout.write(json.dumps(config, indent=2))
        elif output_format == 'yaml':
            import yaml
            self.stdout.write(yaml.dump(config, default_flow_style=False))
        elif output_format == 'env':
            for key, value in config.items():
                if isinstance(value, (list, dict)):
                    value = json.dumps(value)
                self.stdout.write(f"{key}={value}")
    
    def export_config(self, file_path, section, output_format, force):
        """Export configuration to file"""
        if not file_path:
            file_path = f"sb_sync_config_{section}.{output_format}"
        
        if os.path.exists(file_path) and not force:
            if not self.confirm(f"File {file_path} already exists. Overwrite?"):
                return
        
        self.stdout.write(f"Exporting {section} configuration to {file_path}...")
        
        if section == 'all':
            config = {
                            'core_settings': SyncConfig.CORE,
            'advanced_settings': SyncConfig.ADVANCED,
            'error_config': SyncConfig.ERROR,
            'performance_config': SyncConfig.PERFORMANCE,
            'security_config': SyncConfig.SECURITY,
            }
        elif section == 'core':
            config = SyncConfig.CORE
        elif section == 'advanced':
            config = SyncConfig.ADVANCED
        elif section == 'error':
            config = SyncConfig.ERROR
        elif section == 'performance':
            config = SyncConfig.PERFORMANCE
        elif section == 'security':
            config = SyncConfig.SECURITY
        
        try:
            with open(file_path, 'w') as f:
                if output_format == 'json':
                    json.dump(config, f, indent=2)
                elif output_format == 'yaml':
                    import yaml
                    yaml.dump(config, f, default_flow_style=False)
                elif output_format == 'env':
                    for key, value in config.items():
                        if isinstance(value, (list, dict)):
                            value = json.dumps(value)
                        f.write(f"{key}={value}\n")
            
            self.stdout.write(
                self.style.SUCCESS(f"Configuration exported to {file_path}")
            )
        except Exception as e:
            raise CommandError(f"Failed to export configuration: {str(e)}")
    
    def import_config(self, file_path, force):
        """Import configuration from file"""
        if not file_path:
            raise CommandError("File path is required for import operation")
        
        if not os.path.exists(file_path):
            raise CommandError(f"File {file_path} does not exist")
        
        if not force:
            if not self.confirm(f"Import configuration from {file_path}?"):
                return
        
        self.stdout.write(f"Importing configuration from {file_path}...")
        
        try:
            with open(file_path, 'r') as f:
                if file_path.endswith('.json'):
                    config = json.load(f)
                elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
                    import yaml
                    config = yaml.safe_load(f)
                elif file_path.endswith('.env'):
                    config = {}
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            config[key] = value
                else:
                    config = json.load(f)
            
            # Update Django settings (simplified approach)
            updated_count = 0
            for key, value in config.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
                    updated_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f"Configuration imported. Updated {updated_count} settings.")
            )
        except Exception as e:
            raise CommandError(f"Failed to import configuration: {str(e)}")
    
    def validate_config(self):
        """Validate current configuration"""
        self.stdout.write("Validating configuration...")
        
        issues = SyncConfig.validate_config()
        
        if issues:
            self.stdout.write(self.style.WARNING("Configuration issues found:"))
            for issue in issues:
                self.stdout.write(f"  - {issue}")
        else:
            self.stdout.write(self.style.SUCCESS("Configuration is valid!"))
    
    def show_summary(self):
        """Show configuration summary"""
        summary = get_config_summary()
        
        self.stdout.write("Configuration Summary:")
        self.stdout.write("=" * 50)
        self.stdout.write(f"Core settings: {summary['core_settings_count']}")
        self.stdout.write(f"Advanced settings: {summary['advanced_settings_count']}")
        self.stdout.write(f"Performance monitoring: {'Enabled' if summary['performance_enabled'] else 'Disabled'}")
        self.stdout.write(f"Caching: {'Enabled' if summary['caching_enabled'] else 'Disabled'}")
        self.stdout.write(f"Background tasks: {'Enabled' if summary['background_tasks_enabled'] else 'Disabled'}")
        self.stdout.write(f"Authentication required: {'Yes' if summary['authentication_required'] else 'No'}")
        self.stdout.write(f"Rate limiting: {'Enabled' if summary['rate_limiting_enabled'] else 'Disabled'}")
        
        if summary['validation_issues']:
            self.stdout.write(self.style.WARNING(f"Validation issues: {len(summary['validation_issues'])}"))
        else:
            self.stdout.write(self.style.SUCCESS("No validation issues"))
    
    def reset_config(self, force):
        """Reset configuration to defaults"""
        if not force:
            if not self.confirm("Reset configuration to defaults? This will clear all custom settings."):
                return
        
        self.stdout.write("Resetting configuration to defaults...")
        
        # This is a simplified reset - in practice, you'd want to be more careful
        # about which settings to reset
        try:
            # Reset to default configuration
            SyncConfig.reset_to_defaults()
            
            self.stdout.write(self.style.SUCCESS("Configuration reset to defaults"))
        except Exception as e:
            raise CommandError(f"Failed to reset configuration: {str(e)}")
    
    def confirm(self, message):
        """Ask for user confirmation"""
        while True:
            response = input(f"{message} (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                self.stdout.write("Please enter 'y' or 'n'") 