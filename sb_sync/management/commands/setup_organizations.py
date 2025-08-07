"""
Management command to set up organizations and permissions for multi-tenant access using Django Groups
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group
from django.apps import apps
from django.db import models
from sb_sync.models import (
    Organization, UserOrganization, ModelPermission, DataFilter
)
import json


class Command(BaseCommand):
    help = 'Set up organizations and permissions for multi-tenant access using Django Groups'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['create_org', 'add_user', 'set_permissions', 'setup_example', 'create_groups', 'discover_models', 'auto_setup'],
            required=True,
            help='Action to perform'
        )
        parser.add_argument(
            '--org-name',
            type=str,
            help='Organization name'
        )
        parser.add_argument(
            '--org-slug',
            type=str,
            help='Organization slug'
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Username'
        )
        parser.add_argument(
            '--group-name',
            type=str,
            help='Django Group name'
        )
        parser.add_argument(
            '--config-file',
            type=str,
            help='JSON configuration file for permissions'
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
            choices=['full_access', 'read_write', 'read_only', 'custom'],
            default='read_write',
            help='Permission template to apply'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'create_org':
            self.create_organization(options)
        elif action == 'add_user':
            self.add_user_to_organization(options)
        elif action == 'set_permissions':
            self.set_permissions(options)
        elif action == 'setup_example':
            self.setup_example_organizations(options)
        elif action == 'create_groups':
            self.create_groups(options)
        elif action == 'discover_models':
            self.discover_models(options)
        elif action == 'auto_setup':
            self.auto_setup_permissions(options)

    def create_organization(self, options):
        """Create a new organization"""
        org_name = options['org_name']
        org_slug = options['org_slug']
        
        if not org_name or not org_slug:
            raise CommandError('--org-name and --org-slug are required')
        
        org, created = Organization.objects.get_or_create(
            slug=org_slug,
            defaults={
                'name': org_name,
                'description': f'Organization: {org_name}'
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created organization: {org.name} ({org.slug})')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Organization already exists: {org.name} ({org.slug})')
            )

    def add_user_to_organization(self, options):
        """Add a user to an organization with a Django Group"""
        username = options['username']
        org_slug = options['org_slug']
        group_name = options['group_name']
        
        if not username or not org_slug or not group_name:
            raise CommandError('--username, --org-slug, and --group-name are required')
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User {username} does not exist')
        
        try:
            organization = Organization.objects.get(slug=org_slug)
        except Organization.DoesNotExist:
            raise CommandError(f'Organization {org_slug} does not exist')
        
        try:
            group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            raise CommandError(f'Group {group_name} does not exist. Create it first with --action create_groups')
        
        user_org, created = UserOrganization.objects.get_or_create(
            user=user,
            organization=organization,
            defaults={'group': group}
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully added {user.username} to {organization.name} with group {group.name}'
                )
            )
        else:
            user_org.group = group
            user_org.save()
            self.stdout.write(
                self.style.WARNING(
                    f'Updated {user.username} group to {group.name} in {organization.name}'
                )
            )

    def set_permissions(self, options):
        """Set model permissions for groups"""
        org_slug = options['org_slug']
        config_file = options['config_file']
        
        if not org_slug or not config_file:
            raise CommandError('--org-slug and --config-file are required')
        
        try:
            organization = Organization.objects.get(slug=org_slug)
        except Organization.DoesNotExist:
            raise CommandError(f'Organization {org_slug} does not exist')
        
        try:
            with open(config_file, 'r') as f:
                permissions_config = json.load(f)
        except FileNotFoundError:
            raise CommandError(f'Configuration file {config_file} not found')
        except json.JSONDecodeError:
            raise CommandError(f'Invalid JSON in configuration file {config_file}')
        
        for group_name, models in permissions_config.items():
            try:
                group = Group.objects.get(name=group_name)
            except Group.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Group {group_name} does not exist, skipping...')
                )
                continue
            
            for model_name, permissions in models.items():
                permission, created = ModelPermission.objects.get_or_create(
                    organization=organization,
                    group=group,
                    model_name=model_name,
                    defaults=permissions
                )
                
                if not created:
                    # Update existing permissions
                    for key, value in permissions.items():
                        setattr(permission, key, value)
                    permission.save()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Set permissions for {group.name} on {model_name} in {organization.name}'
                    )
                )

    def create_groups(self, options):
        """Create Django Groups for the application"""
        # Create common groups that can be used across different domains
        groups = [
            'Administrators',
            'Managers',
            'Users',
            'Analysts',
            'Sales',
            'Support',
            'Read Only',
        ]
        
        for group_name in groups:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created group: {group.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Group already exists: {group.name}')
                )

    def discover_models(self, options):
        """Discover all Django models in the project"""
        app_label = options.get('app_label')
        exclude_models = options.get('exclude_models', '').split(',') if options.get('exclude_models') else []
        
        discovered_models = []
        
        if app_label:
            # Discover models from specific app
            try:
                app_config = apps.get_app_config(app_label)
                models_module = app_config.models_module
                if models_module:
                    for model in models_module.__dict__.values():
                        if isinstance(model, type) and issubclass(model, models.Model) and model != models.Model:
                            model_name = f"{app_label}.{model.__name__}"
                            if model_name not in exclude_models:
                                discovered_models.append(model_name)
            except Exception as e:
                raise CommandError(f'Error discovering models from app {app_label}: {e}')
        else:
            # Discover models from all apps
            for app_config in apps.get_app_configs():
                if app_config.models_module:
                    for model in app_config.models_module.__dict__.values():
                        if isinstance(model, type) and issubclass(model, models.Model) and model != models.Model:
                            model_name = f"{app_config.label}.{model.__name__}"
                            if model_name not in exclude_models:
                                discovered_models.append(model_name)
        
        # Output discovered models
        self.stdout.write(
            self.style.SUCCESS(f'Discovered {len(discovered_models)} models:')
        )
        for model_name in discovered_models:
            self.stdout.write(f'  - {model_name}')
        
        return discovered_models

    def get_permission_template(self, template_name):
        """Get permission template based on name"""
        templates = {
            'full_access': {
                'can_push': True,
                'can_pull': True,
            },
            'read_write': {
                'can_push': True,
                'can_pull': True,
            },
            'read_only': {
                'can_push': False,
                'can_pull': True,
            },
            'custom': {
                'can_push': True,
                'can_pull': True,
            }
        }
        return templates.get(template_name, templates['read_write'])

    def auto_setup_permissions(self, options):
        """Automatically setup permissions for discovered models"""
        org_slug = options['org_slug']
        app_label = options.get('app_label')
        exclude_models = options.get('exclude_models', '').split(',') if options.get('exclude_models') else []
        permission_template = options.get('permission_template', 'read_write')
        
        if not org_slug:
            raise CommandError('--org-slug is required')
        
        try:
            organization = Organization.objects.get(slug=org_slug)
        except Organization.DoesNotExist:
            raise CommandError(f'Organization {org_slug} does not exist')
        
        # Discover models
        discovered_models = self.discover_models(options)
        
        if not discovered_models:
            self.stdout.write(
                self.style.WARNING('No models discovered. Check your app configuration.')
            )
            return
        
        # Get groups
        groups = Group.objects.all()
        if not groups:
            self.stdout.write(
                self.style.WARNING('No groups found. Create groups first with --action create_groups')
            )
            return
        
        # Get permission template
        template = self.get_permission_template(permission_template)
        
        # Setup permissions for each group and model
        permissions_created = 0
        for group in groups:
            for model_name in discovered_models:
                # Skip excluded models
                if model_name in exclude_models:
                    continue
                
                # Create permission
                permission, created = ModelPermission.objects.get_or_create(
                    organization=organization,
                    group=group,
                    model_name=model_name,
                    defaults=template
                )
                
                if created:
                    permissions_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created permission for {group.name} on {model_name}'
                        )
                    )
                else:
                    # Update existing permission with template
                    for key, value in template.items():
                        setattr(permission, key, value)
                    permission.save()
                    self.stdout.write(
                        self.style.WARNING(
                            f'Updated permission for {group.name} on {model_name}'
                        )
                    )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully setup {permissions_created} permissions for {len(discovered_models)} models')
        )

    def setup_example_organizations(self, options):
        """Set up example organizations with groups and permissions"""
        # Create organizations
        organizations = [
            {
                'name': 'Acme Corporation',
                'slug': 'acme-corp',
                'description': 'Technology company'
            },
            {
                'name': 'Global Retail',
                'slug': 'global-retail',
                'description': 'Retail chain'
            },
            {
                'name': 'City University',
                'slug': 'city-university',
                'description': 'Educational institution'
            }
        ]
        
        for org_data in organizations:
            org, created = Organization.objects.get_or_create(
                slug=org_data['slug'],
                defaults=org_data
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created organization: {org.name}')
                )
            
            # Set up permissions for common models
            common_models = [
                'auth.User',
                'auth.Group',
                'contenttypes.ContentType',
                'sessions.Session',
            ]
            
            # Define group-based permissions
            group_permissions = {
                'Administrators': {
                    'can_push': True,
                    'can_pull': True,
                },
                'Managers': {
                    'can_push': True,
                    'can_pull': True,
                },
                'Users': {
                    'can_push': True,
                    'can_pull': True,
                },
                'Analysts': {
                    'can_push': False,
                    'can_pull': True,
                },
                'Sales': {
                    'can_push': True,
                    'can_pull': True,
                },
                'Support': {
                    'can_push': True,
                    'can_pull': True,
                },
                'Read Only': {
                    'can_push': False,
                    'can_pull': True,
                }
            }
            
            # Create permissions for each group and model
            for group_name, permissions in group_permissions.items():
                try:
                    group = Group.objects.get(name=group_name)
                except Group.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'Group {group_name} not found, skipping...')
                    )
                    continue
                
                for model_name in common_models:
                    ModelPermission.objects.get_or_create(
                        organization=org,
                        group=group,
                        model_name=model_name,
                        defaults=permissions
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'Set up permissions for {org.name}')
            )
        
        # Create example data filters
        self.create_example_filters()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up example organizations with groups and permissions')
        )

    def create_example_filters(self):
        """Create example data filters for group-based access"""
        # Example: Managers can only see their department's data
        try:
            org = Organization.objects.get(slug='acme-corp')
            managers_group = Group.objects.get(name='Managers')
            
            # Filter for managers to see only their department's data
            DataFilter.objects.get_or_create(
                organization=org,
                group=managers_group,
                model_name='auth.User',
                filter_name='department_filter',
                filter_condition={
                    'field': 'department',
                    'operator': 'exact',
                    'value': 'TECHNOLOGY'  # Example department
                }
            )
            
            # Filter for sales to see only their assigned customers
            sales_group = Group.objects.get(name='Sales')
            DataFilter.objects.get_or_create(
                organization=org,
                group=sales_group,
                model_name='auth.User',
                filter_name='assigned_customers',
                filter_condition={
                    'field': 'assigned_sales_id',
                    'operator': 'exact',
                    'value': 1  # Example sales ID
                }
            )
            
            self.stdout.write(
                self.style.SUCCESS('Created example data filters')
            )
            
        except (Organization.DoesNotExist, Group.DoesNotExist) as e:
            self.stdout.write(
                self.style.WARNING(f'Organization or Group not found for creating filters: {e}')
            ) 