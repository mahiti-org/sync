"""
Management command for dynamic permission configuration
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group
from sb_sync.models import Organization, ModelPermission, DataFilter
from sb_sync.utils import DynamicPermissionConfigurator, ModelIntrospector
import json
import os


class Command(BaseCommand):
    help = 'Dynamic permission configuration for multi-tenant access'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['discover', 'generate', 'apply', 'export', 'import', 'validate', 'template'],
            required=True,
            help='Action to perform'
        )
        parser.add_argument(
            '--org-slug',
            type=str,
            help='Organization slug'
        )
        parser.add_argument(
            '--app-label',
            type=str,
            help='Django app label to discover models from'
        )
        parser.add_argument(
            '--exclude-models',
            type=str,
            help='Comma-separated list of models to exclude'
        )
        parser.add_argument(
            '--permission-template',
            type=str,
            choices=['full_access', 'read_write', 'read_only', 'write_only', 'custom'],
            default='read_write',
            help='Permission template to apply'
        )
        parser.add_argument(
            '--config-file',
            type=str,
            help='JSON configuration file for permissions'
        )
        parser.add_argument(
            '--output-file',
            type=str,
            help='Output file for generated configuration'
        )
        parser.add_argument(
            '--groups',
            type=str,
            help='Comma-separated list of groups to include'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'discover':
            self.discover_models(options)
        elif action == 'generate':
            self.generate_config(options)
        elif action == 'apply':
            self.apply_config(options)
        elif action == 'export':
            self.export_config(options)
        elif action == 'import':
            self.import_config(options)
        elif action == 'validate':
            self.validate_config(options)
        elif action == 'template':
            self.show_templates(options)

    def discover_models(self, options):
        """Discover all Django models"""
        app_label = options.get('app_label')
        exclude_models = options.get('exclude_models', '').split(',') if options.get('exclude_models') else []
        
        models = ModelIntrospector.discover_all_models(app_label, exclude_models)
        
        self.stdout.write(
            self.style.SUCCESS(f'Discovered {len(models)} models:')
        )
        for model_name in models:
            self.stdout.write(f'  - {model_name}')
        
        # Show model details
        if models:
            self.stdout.write('\nModel Details:')
            for model_name in models[:5]:  # Show first 5 models
                fields = ModelIntrospector.get_model_fields(model_name)
                self.stdout.write(f'\n{model_name}:')
                for field_name, field_info in list(fields.items())[:3]:  # Show first 3 fields
                    self.stdout.write(f'  - {field_name}: {field_info["type"]}')

    def generate_config(self, options):
        """Generate permission configuration"""
        org_slug = options['org_slug']
        app_label = options.get('app_label')
        exclude_models = options.get('exclude_models', '').split(',') if options.get('exclude_models') else []
        permission_template = options.get('permission_template', 'read_write')
        output_file = options.get('output_file')
        groups_filter = options.get('groups', '').split(',') if options.get('groups') else []
        
        if not org_slug:
            raise CommandError('--org-slug is required')
        
        try:
            organization = Organization.objects.get(slug=org_slug)
        except Organization.DoesNotExist:
            raise CommandError(f'Organization {org_slug} does not exist')
        
        # Get models
        models = ModelIntrospector.discover_all_models(app_label, exclude_models)
        
        # Get groups
        if groups_filter:
            groups = Group.objects.filter(name__in=groups_filter)
        else:
            groups = Group.objects.all()
        
        # Generate configuration
        config = DynamicPermissionConfigurator.generate_permission_config(
            organization, models, groups, permission_template
        )
        
        # Output configuration
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(config, f, indent=2)
            self.stdout.write(
                self.style.SUCCESS(f'Configuration saved to {output_file}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Generated Configuration:')
            )
            self.stdout.write(json.dumps(config, indent=2))
        
        # Show summary
        total_permissions = sum(len(models) for models in config.values())
        self.stdout.write(
            self.style.SUCCESS(f'\nSummary: {len(config)} groups, {len(models)} models, {total_permissions} permissions')
        )

    def apply_config(self, options):
        """Apply permission configuration"""
        org_slug = options['org_slug']
        config_file = options.get('config_file')
        
        if not org_slug:
            raise CommandError('--org-slug is required')
        
        if not config_file:
            raise CommandError('--config-file is required')
        
        try:
            organization = Organization.objects.get(slug=org_slug)
        except Organization.DoesNotExist:
            raise CommandError(f'Organization {org_slug} does not exist')
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            raise CommandError(f'Configuration file {config_file} not found')
        except json.JSONDecodeError:
            raise CommandError(f'Invalid JSON in configuration file {config_file}')
        
        # Apply configuration
        result = DynamicPermissionConfigurator.apply_permission_config(organization, config)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Applied configuration: {result["created"]} created, {result["updated"]} updated'
            )
        )

    def export_config(self, options):
        """Export current permission configuration"""
        org_slug = options['org_slug']
        output_file = options.get('output_file')
        
        if not org_slug:
            raise CommandError('--org-slug is required')
        
        try:
            organization = Organization.objects.get(slug=org_slug)
        except Organization.DoesNotExist:
            raise CommandError(f'Organization {org_slug} does not exist')
        
        # Export configuration
        config = DynamicPermissionConfigurator.export_permission_config(organization)
        
        # Output configuration
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(config, f, indent=2)
            self.stdout.write(
                self.style.SUCCESS(f'Configuration exported to {output_file}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Current Configuration:')
            )
            self.stdout.write(json.dumps(config, indent=2))
        
        # Show summary
        total_permissions = sum(len(models) for models in config.values())
        self.stdout.write(
            self.style.SUCCESS(f'\nSummary: {len(config)} groups, {total_permissions} permissions')
        )

    def import_config(self, options):
        """Import permission configuration"""
        org_slug = options['org_slug']
        config_file = options.get('config_file')
        
        if not org_slug:
            raise CommandError('--org-slug is required')
        
        if not config_file:
            raise CommandError('--config-file is required')
        
        try:
            organization = Organization.objects.get(slug=org_slug)
        except Organization.DoesNotExist:
            raise CommandError(f'Organization {org_slug} does not exist')
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            raise CommandError(f'Configuration file {config_file} not found')
        except json.JSONDecodeError:
            raise CommandError(f'Invalid JSON in configuration file {config_file}')
        
        # Validate configuration
        validation_errors = self._validate_config(config)
        if validation_errors:
            self.stdout.write(
                self.style.ERROR('Configuration validation failed:')
            )
            for error in validation_errors:
                self.stdout.write(f'  - {error}')
            return
        
        # Apply configuration
        result = DynamicPermissionConfigurator.apply_permission_config(organization, config)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Imported configuration: {result["created"]} created, {result["updated"]} updated'
            )
        )

    def validate_config(self, options):
        """Validate permission configuration"""
        config_file = options.get('config_file')
        
        if not config_file:
            raise CommandError('--config-file is required')
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            raise CommandError(f'Configuration file {config_file} not found')
        except json.JSONDecodeError:
            raise CommandError(f'Invalid JSON in configuration file {config_file}')
        
        # Validate configuration
        validation_errors = self._validate_config(config)
        
        if validation_errors:
            self.stdout.write(
                self.style.ERROR('Configuration validation failed:')
            )
            for error in validation_errors:
                self.stdout.write(f'  - {error}')
        else:
            self.stdout.write(
                self.style.SUCCESS('Configuration is valid!')
            )
            
            # Show summary
            total_permissions = sum(len(models) for models in config.values())
            self.stdout.write(
                f'Summary: {len(config)} groups, {total_permissions} permissions'
            )

    def show_templates(self, options):
        """Show available permission templates"""
        templates = ModelIntrospector.get_model_permission_templates()
        
        self.stdout.write(
            self.style.SUCCESS('Available Permission Templates:')
        )
        
        for template_name, template_config in templates.items():
            self.stdout.write(f'\n{template_name.upper()}:')
            for permission, value in template_config.items():
                status = '✅' if value else '❌'
                self.stdout.write(f'  {status} {permission}')

    def _validate_config(self, config):
        """Validate configuration structure"""
        errors = []
        
        if not isinstance(config, dict):
            errors.append('Configuration must be a JSON object')
            return errors
        
        for group_name, models in config.items():
            if not isinstance(models, dict):
                errors.append(f'Group "{group_name}" must be an object')
                continue
            
            # Check if group exists
            try:
                Group.objects.get(name=group_name)
            except Group.DoesNotExist:
                errors.append(f'Group "{group_name}" does not exist')
            
            for model_name, permissions in models.items():
                if not isinstance(permissions, dict):
                    errors.append(f'Permissions for {group_name}.{model_name} must be an object')
                    continue
                
                # Check required permission fields
                required_fields = ['can_push', 'can_pull']
                for field in required_fields:
                    if field not in permissions:
                        errors.append(f'Missing "{field}" in {group_name}.{model_name}')
                    elif not isinstance(permissions[field], bool):
                        errors.append(f'"{field}" in {group_name}.{model_name} must be boolean')
                
                # Check if model exists
                try:
                    from django.apps import apps
                    apps.get_model(model_name)
                except LookupError:
                    errors.append(f'Model "{model_name}" does not exist')
        
        return errors 