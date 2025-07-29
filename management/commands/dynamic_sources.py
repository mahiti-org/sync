"""
Management command for dynamic data source configuration
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group
from sb_sync.models import Organization, ModelPermission, DataFilter
from sb_sync.utils import (
    DynamicDataSourceManager, RESTAPIAdapter, DatabaseAdapter, FileAdapter,
    data_source_manager
)
import json
import os


class Command(BaseCommand):
    help = 'Dynamic data source configuration for multi-tenant access'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['discover', 'register', 'generate', 'apply', 'export', 'validate', 'test'],
            required=True,
            help='Action to perform'
        )
        parser.add_argument(
            '--source-type',
            type=str,
            choices=['api', 'database', 'file'],
            help='Type of data source'
        )
        parser.add_argument(
            '--source-config',
            type=str,
            help='JSON configuration for data source'
        )
        parser.add_argument(
            '--org-slug',
            type=str,
            help='Organization slug'
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
            '--test-entity',
            type=str,
            help='Entity name to test with'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'discover':
            self.discover_sources(options)
        elif action == 'register':
            self.register_source(options)
        elif action == 'generate':
            self.generate_config(options)
        elif action == 'apply':
            self.apply_config(options)
        elif action == 'export':
            self.export_config(options)
        elif action == 'validate':
            self.validate_config(options)
        elif action == 'test':
            self.test_source(options)

    def discover_sources(self, options):
        """Discover entities from all registered data sources"""
        discovered = data_source_manager.discover_all_sources()
        
        if not discovered:
            self.stdout.write(
                self.style.WARNING('No data sources registered. Use --action register to add sources.')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS('Discovered entities from all sources:')
        )
        
        for source_type, entities in discovered.items():
            self.stdout.write(f'\n{source_type.upper()}:')
            for entity in entities:
                self.stdout.write(f'  - {entity}')
                
                # Show field information
                fields = data_source_manager.get_entity_fields(source_type, entity)
                if fields:
                    self.stdout.write(f'    Fields: {", ".join(fields.keys())}')

    def register_source(self, options):
        """Register a new data source"""
        source_type = options.get('source_type')
        source_config = options.get('source_config')
        
        if not source_type or not source_config:
            raise CommandError('--source-type and --source-config are required')
        
        try:
            config = json.loads(source_config)
        except json.JSONDecodeError:
            raise CommandError('Invalid JSON in source-config')
        
        try:
            if source_type == 'api':
                adapter = RESTAPIAdapter(
                    base_url=config['base_url'],
                    headers=config.get('headers', {}),
                    auth=tuple(config.get('auth', [])) if config.get('auth') else None
                )
            elif source_type == 'database':
                adapter = DatabaseAdapter(
                    connection_string=config['connection_string'],
                    db_type=config.get('db_type', 'postgresql')
                )
            elif source_type == 'file':
                adapter = FileAdapter(
                    file_path=config['file_path'],
                    file_type=config.get('file_type', 'csv')
                )
            else:
                raise CommandError(f'Unknown source type: {source_type}')
            
            # Register the adapter
            data_source_manager.register_adapter(source_type, adapter)
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully registered {source_type} data source')
            )
            
            # Discover entities from the new source
            entities = adapter.discover_entities()
            self.stdout.write(f'Discovered {len(entities)} entities: {", ".join(entities)}')
            
        except Exception as e:
            raise CommandError(f'Error registering {source_type} source: {str(e)}')

    def generate_config(self, options):
        """Generate permission configuration for data sources"""
        org_slug = options['org_slug']
        permission_template = options.get('permission_template', 'read_write')
        output_file = options.get('output_file')
        source_types = options.get('source_types', '').split(',') if options.get('source_types') else None
        
        if not org_slug:
            raise CommandError('--org-slug is required')
        
        try:
            organization = Organization.objects.get(slug=org_slug)
        except Organization.DoesNotExist:
            raise CommandError(f'Organization {org_slug} does not exist')
        
        # Generate configuration
        config = data_source_manager.generate_permission_config(
            organization=organization,
            source_types=source_types,
            template=permission_template
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
            self.style.SUCCESS(f'\nSummary: {len(config)} groups, {total_permissions} permissions')
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
        result = self._apply_data_source_config(organization, config)
        
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
        config = self._export_data_source_config(organization)
        
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
        validation_errors = self._validate_data_source_config(config)
        
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

    def test_source(self, options):
        """Test data source connectivity and operations"""
        source_type = options.get('source_type')
        test_entity = options.get('test_entity')
        
        if not source_type:
            raise CommandError('--source-type is required')
        
        if source_type not in data_source_manager.adapters:
            raise CommandError(f'Source type {source_type} not registered')
        
        adapter = data_source_manager.adapters[source_type]
        
        # Test discovery
        self.stdout.write(f'Testing {source_type} source discovery...')
        entities = adapter.discover_entities()
        self.stdout.write(f'Discovered entities: {entities}')
        
        if not entities:
            self.stdout.write(
                self.style.WARNING('No entities discovered')
            )
            return
        
        # Test field discovery
        test_entity = test_entity or entities[0]
        self.stdout.write(f'Testing field discovery for {test_entity}...')
        fields = adapter.get_entity_fields(test_entity)
        self.stdout.write(f'Fields: {fields}')
        
        # Test pull operation
        self.stdout.write(f'Testing pull operation for {test_entity}...')
        data = adapter.pull_data(test_entity, limit=5)
        self.stdout.write(f'Pulled {len(data)} records')
        
        if data:
            self.stdout.write(f'Sample data: {data[0]}')

    def _apply_data_source_config(self, organization, config):
        """Apply data source permission configuration"""
        permissions_created = 0
        permissions_updated = 0
        
        for group_name, entities in config.items():
            try:
                group = Group.objects.get(name=group_name)
            except Group.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Group {group_name} not found, skipping...')
                )
                continue
            
            for entity_key, permissions in entities.items():
                permission, created = ModelPermission.objects.get_or_create(
                    organization=organization,
                    group=group,
                    model_name=entity_key,
                    defaults=permissions
                )
                
                if created:
                    permissions_created += 1
                else:
                    # Update existing permission
                    for key, value in permissions.items():
                        setattr(permission, key, value)
                    permission.save()
                    permissions_updated += 1
        
        return {
            'created': permissions_created,
            'updated': permissions_updated,
            'total': permissions_created + permissions_updated
        }

    def _export_data_source_config(self, organization):
        """Export data source permission configuration"""
        config = {}
        permissions = ModelPermission.objects.filter(organization=organization)
        
        for permission in permissions:
            group_name = permission.group.name
            if group_name not in config:
                config[group_name] = {}
            
            config[group_name][permission.model_name] = {
                'can_push': permission.can_push,
                'can_pull': permission.can_pull,
                'can_create': permission.can_create,
                'can_update': permission.can_update,
                'can_delete': permission.can_delete,
                'can_read': permission.can_read
            }
        
        return config

    def _validate_data_source_config(self, config):
        """Validate data source configuration structure"""
        errors = []
        
        if not isinstance(config, dict):
            errors.append('Configuration must be a JSON object')
            return errors
        
        for group_name, entities in config.items():
            if not isinstance(entities, dict):
                errors.append(f'Group "{group_name}" must be an object')
                continue
            
            # Check if group exists
            try:
                Group.objects.get(name=group_name)
            except Group.DoesNotExist:
                errors.append(f'Group "{group_name}" does not exist')
            
            for entity_key, permissions in entities.items():
                if not isinstance(permissions, dict):
                    errors.append(f'Permissions for {group_name}.{entity_key} must be an object')
                    continue
                
                # Check required permission fields
                required_fields = ['can_push', 'can_pull', 'can_create', 'can_update', 'can_delete', 'can_read']
                for field in required_fields:
                    if field not in permissions:
                        errors.append(f'Missing "{field}" in {group_name}.{entity_key}')
                    elif not isinstance(permissions[field], bool):
                        errors.append(f'"{field}" in {group_name}.{entity_key} must be boolean')
                
                # Check if entity exists in registered sources
                if '.' in entity_key:
                    source_type, entity_name = entity_key.split('.', 1)
                    if source_type not in data_source_manager.adapters:
                        errors.append(f'Source type "{source_type}" not registered')
                    else:
                        entities = data_source_manager.adapters[source_type].discover_entities()
                        if entity_name not in entities:
                            errors.append(f'Entity "{entity_name}" not found in {source_type} source')
        
        return errors 