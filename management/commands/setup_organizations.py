"""
Management command to set up organizations and permissions for multi-tenant access
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.apps import apps
from sb_sync.models import (
    Organization, UserOrganization, ModelPermission, DataFilter
)
import json


class Command(BaseCommand):
    help = 'Set up organizations and permissions for multi-tenant access'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['create_org', 'add_user', 'set_permissions', 'setup_healthcare'],
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
            '--role',
            type=str,
            choices=['ADMIN', 'DOCTOR', 'NURSE', 'LAB_TECH', 'PHARMACIST', 'READ_ONLY'],
            help='User role'
        )
        parser.add_argument(
            '--config-file',
            type=str,
            help='JSON configuration file for permissions'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'create_org':
            self.create_organization(options)
        elif action == 'add_user':
            self.add_user_to_organization(options)
        elif action == 'set_permissions':
            self.set_permissions(options)
        elif action == 'setup_healthcare':
            self.setup_healthcare_organizations(options)

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
        """Add a user to an organization with a role"""
        username = options['username']
        org_slug = options['org_slug']
        role = options['role']
        
        if not username or not org_slug or not role:
            raise CommandError('--username, --org-slug, and --role are required')
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User {username} does not exist')
        
        try:
            organization = Organization.objects.get(slug=org_slug)
        except Organization.DoesNotExist:
            raise CommandError(f'Organization {org_slug} does not exist')
        
        user_org, created = UserOrganization.objects.get_or_create(
            user=user,
            organization=organization,
            defaults={'role': role}
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully added {user.username} to {organization.name} with role {role}'
                )
            )
        else:
            user_org.role = role
            user_org.save()
            self.stdout.write(
                self.style.WARNING(
                    f'Updated {user.username} role to {role} in {organization.name}'
                )
            )

    def set_permissions(self, options):
        """Set model permissions for roles"""
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
        
        for role, models in permissions_config.items():
            for model_name, permissions in models.items():
                permission, created = ModelPermission.objects.get_or_create(
                    organization=organization,
                    role=role,
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
                        f'Set permissions for {role} on {model_name} in {organization.name}'
                    )
                )

    def setup_healthcare_organizations(self, options):
        """Set up example healthcare organizations with permissions"""
        # Create organizations
        organizations = [
            {
                'name': 'City General Hospital',
                'slug': 'city-general',
                'description': 'Primary healthcare facility in the city'
            },
            {
                'name': 'Riverside Medical Center',
                'slug': 'riverside-medical',
                'description': 'Specialized medical center'
            },
            {
                'name': 'Community Health Clinic',
                'slug': 'community-health',
                'description': 'Community-based healthcare clinic'
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
            
            # Set up permissions for healthcare models
            healthcare_models = [
                'healthcare.Patient',
                'healthcare.PatientVisit',
                'healthcare.PatientTreatment',
                'healthcare.MedicineDisbursed',
                'healthcare.LabInvestigation',
                'healthcare.PatientVisitFeedback'
            ]
            
            # Define role-based permissions
            role_permissions = {
                'ADMIN': {
                    'can_push': True,
                    'can_pull': True,
                    'can_create': True,
                    'can_update': True,
                    'can_delete': True,
                    'can_read': True
                },
                'DOCTOR': {
                    'can_push': True,
                    'can_pull': True,
                    'can_create': True,
                    'can_update': True,
                    'can_delete': False,
                    'can_read': True
                },
                'NURSE': {
                    'can_push': True,
                    'can_pull': True,
                    'can_create': True,
                    'can_update': True,
                    'can_delete': False,
                    'can_read': True
                },
                'LAB_TECH': {
                    'can_push': True,
                    'can_pull': True,
                    'can_create': True,
                    'can_update': True,
                    'can_delete': False,
                    'can_read': True
                },
                'PHARMACIST': {
                    'can_push': True,
                    'can_pull': True,
                    'can_create': True,
                    'can_update': True,
                    'can_delete': False,
                    'can_read': True
                },
                'READ_ONLY': {
                    'can_push': False,
                    'can_pull': True,
                    'can_create': False,
                    'can_update': False,
                    'can_delete': False,
                    'can_read': True
                }
            }
            
            # Create permissions for each role and model
            for role, permissions in role_permissions.items():
                for model_name in healthcare_models:
                    ModelPermission.objects.get_or_create(
                        organization=org,
                        role=role,
                        model_name=model_name,
                        defaults=permissions
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'Set up permissions for {org.name}')
            )
        
        # Create example data filters
        self.create_example_filters()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up healthcare organizations with permissions')
        )

    def create_example_filters(self):
        """Create example data filters for role-based access"""
        # Example: Doctors can only see patients in their department
        try:
            org = Organization.objects.get(slug='city-general')
            
            # Filter for doctors to see only their department's patients
            DataFilter.objects.get_or_create(
                organization=org,
                role='DOCTOR',
                model_name='healthcare.Patient',
                filter_name='department_filter',
                filter_condition={
                    'field': 'department',
                    'operator': 'exact',
                    'value': 'CARDIOLOGY'  # Example department
                }
            )
            
            # Filter for nurses to see only their assigned patients
            DataFilter.objects.get_or_create(
                organization=org,
                role='NURSE',
                model_name='healthcare.Patient',
                filter_name='assigned_patients',
                filter_condition={
                    'field': 'assigned_nurse_id',
                    'operator': 'exact',
                    'value': 1  # Example nurse ID
                }
            )
            
            self.stdout.write(
                self.style.SUCCESS('Created example data filters')
            )
            
        except Organization.DoesNotExist:
            self.stdout.write(
                self.style.WARNING('Organization not found for creating filters')
            ) 