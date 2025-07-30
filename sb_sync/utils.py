"""
Utility functions for sb-sync package
"""
import json
import logging
from django.apps import apps
from django.db import models
from django.core.cache import cache
from django.conf import settings
from .models import ModelPermission, DataFilter
from django.contrib.auth.models import Group
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger('sb_sync')

class ModelIntrospector:
    """Introspect Django models for dynamic configuration"""
    
    @staticmethod
    def get_model_fields(model_name):
        """Get cached model fields"""
        cache_key = f"sb_sync_model_fields_{model_name}"
        fields = cache.get(cache_key)

        if fields is None:
            try:
                model_class = apps.get_model(model_name)
                fields = {}
                for field in model_class._meta.get_fields():
                    if not field.many_to_many and not field.one_to_many:
                        fields[field.name] = {
                            'type': field.__class__.__name__,
                            'required': not field.null and not field.blank,
                            'max_length': getattr(field, 'max_length', None)
                        }
                cache.set(cache_key, fields, timeout=3600)  # Cache for 1 hour
            except LookupError:
                fields = {}
        return fields

    @staticmethod
    def validate_json_against_model(json_data, model_name):
        """Validate JSON data against model structure"""
        model_fields = ModelIntrospector.get_model_fields(model_name)
        errors = []
        
        for field_name, value in json_data.items():
            if field_name not in model_fields:
                errors.append(f"Field '{field_name}' not found in model '{model_name}'")
                continue
            
            field_info = model_fields[field_name]
            if field_info['required'] and value is None:
                errors.append(f"Required field '{field_name}' cannot be null")
        
        return errors

    @staticmethod
    def discover_all_models(app_label=None, exclude_models=None):
        """Discover all Django models in the project"""
        discovered_models = []
        exclude_models = exclude_models or []
        
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
                logger.error(f'Error discovering models from app {app_label}: {e}')
        else:
            # Discover models from all apps
            for app_config in apps.get_app_configs():
                if app_config.models_module:
                    for model in app_config.models_module.__dict__.values():
                        if isinstance(model, type) and issubclass(model, models.Model) and model != models.Model:
                            model_name = f"{app_config.label}.{model.__name__}"
                            if model_name not in exclude_models:
                                discovered_models.append(model_name)
        
        return discovered_models

    @staticmethod
    def get_model_permission_templates():
        """Get predefined permission templates"""
        return {
            'full_access': {
                'can_push': True,
                'can_pull': True,
                'can_create': True,
                'can_update': True,
                'can_delete': True,
                'can_read': True
            },
            'read_write': {
                'can_push': True,
                'can_pull': True,
                'can_create': True,
                'can_update': True,
                'can_delete': False,
                'can_read': True
            },
            'read_only': {
                'can_push': False,
                'can_pull': True,
                'can_create': False,
                'can_update': False,
                'can_delete': False,
                'can_read': True
            },
            'write_only': {
                'can_push': True,
                'can_pull': False,
                'can_create': True,
                'can_update': True,
                'can_delete': False,
                'can_read': False
            },
            'custom': {
                'can_push': False,
                'can_pull': False,
                'can_create': False,
                'can_update': False,
                'can_delete': False,
                'can_read': False
            }
        }

class DynamicPermissionConfigurator:
    """Configure dynamic permissions for organizations"""
    
    @staticmethod
    def generate_permission_config(organization, models=None, groups=None, template='read_write'):
        """Generate permission configuration for organization"""
        if models is None:
            models = ModelIntrospector.discover_all_models()
        
        if groups is None:
            groups = Group.objects.all()
        
        templates = ModelIntrospector.get_model_permission_templates()
        template_config = templates.get(template, templates['read_write'])
        
        config = {}
        for group in groups:
            config[group.name] = {}
            for model_name in models:
                config[group.name][model_name] = template_config.copy()
        
        return config
    
    @staticmethod
    def apply_permission_config(organization, config):
        """Apply permission configuration to organization"""
        try:
            # Clear existing permissions
            ModelPermission.objects.filter(organization=organization).delete()
            
            # Create new permissions
            permissions_to_create = []
            for group_name, model_permissions in config.items():
                try:
                    group = Group.objects.get(name=group_name)
                except Group.DoesNotExist:
                    logger.warning(f"Group '{group_name}' not found, skipping")
                    continue
                
                for model_name, permissions in model_permissions.items():
                    permission = ModelPermission(
                        organization=organization,
                        group=group,
                        model_name=model_name,
                        can_push=permissions.get('can_push', False),
                        can_pull=permissions.get('can_pull', False),
                        can_create=permissions.get('can_create', False),
                        can_update=permissions.get('can_update', False),
                        can_delete=permissions.get('can_delete', False),
                        can_read=permissions.get('can_read', False)
                    )
                    permissions_to_create.append(permission)
            
            # Bulk create permissions
            if permissions_to_create:
                ModelPermission.objects.bulk_create(permissions_to_create)
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying permission config: {e}")
            return False
    
    @staticmethod
    def export_permission_config(organization):
        """Export current permission configuration"""
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
    
    @staticmethod
    def generate_data_filters(organization, models=None, groups=None):
        """Generate data filters for organization"""
        if models is None:
            models = ModelIntrospector.discover_all_models()
        
        if groups is None:
            groups = Group.objects.all()
        
        filters = {}
        for group in groups:
            filters[group.name] = {}
            for model_name in models:
                filters[group.name][model_name] = DynamicPermissionConfigurator._generate_example_filters(model_name, group.name)
        
        return filters
    
    @staticmethod
    def _generate_example_filters(model_name, group_name):
        """Generate example filters for a model and group"""
        # This is a simplified example - in practice, you'd have more sophisticated logic
        example_filters = {
            'status': 'active',
            'is_deleted': False
        }
        
        # Add role-specific filters
        if 'admin' in group_name.lower():
            return {}  # Admins see all data
        elif 'manager' in group_name.lower():
            example_filters['department'] = '{{user.department}}'
        elif 'staff' in group_name.lower():
            example_filters['assigned_to'] = '{{user.id}}'
        
        return example_filters

class DataProcessor:
    """Process data for sync operations"""
    
    @staticmethod
    def process_push_data(json_data, user):
        """Process push data and apply filters"""
        processed_data = []
        
        for item in json_data:
            if '_model' not in item:
                continue
            
            model_name = item['_model']
            
            # Validate data against model
            validation_errors = ModelIntrospector.validate_json_against_model(item, model_name)
            if validation_errors:
                logger.warning(f"Validation errors for {model_name}: {validation_errors}")
                continue
            
            # Apply data filters based on user's organization and groups
            if DataProcessor._apply_data_filters(item, user, model_name):
                processed_data.append(item)
        
        return processed_data
    
    @staticmethod
    def process_pull_data(model_name, filters=None):
        """Process pull data with filters"""
        try:
            model_class = apps.get_model(model_name)
            queryset = model_class.objects.all()
            
            if filters:
                queryset = queryset.filter(**filters)
            
            # Convert to list of dictionaries
            data = []
            for obj in queryset:
                obj_dict = {}
                for field in obj._meta.get_fields():
                    if not field.many_to_many and not field.one_to_many:
                        obj_dict[field.name] = getattr(obj, field.name)
                data.append(obj_dict)
            
            return data
            
        except Exception as e:
            logger.error(f"Error processing pull data for {model_name}: {e}")
            return []
    
    @staticmethod
    def sanitize_data(data):
        """Sanitize data for safe processing"""
        if isinstance(data, dict):
            return {k: DataProcessor.sanitize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [DataProcessor.sanitize_data(item) for item in data]
        elif isinstance(data, str):
            # Basic sanitization - in production, use proper sanitization libraries
            return data.strip()
        else:
            return data
    
    @staticmethod
    def batch_process_data(data, batch_size=1000):
        """Process data in batches"""
        for i in range(0, len(data), batch_size):
            yield data[i:i + batch_size]
    
    @staticmethod
    def _apply_data_filters(data, user, model_name):
        """Apply data filters based on user permissions"""
        try:
            # Get user's organization
            user_org = user.userorganization_set.first()
            if not user_org:
                return False
            
            # Get data filters for user's groups and model
            filters = DataFilter.objects.filter(
                organization=user_org.organization,
                model_name=model_name,
                group__in=user.groups.all()
            )
            
            for filter_obj in filters:
                filter_conditions = filter_obj.filter_conditions
                if isinstance(filter_conditions, dict):
                    # Check if data matches filter conditions
                    for field, value in filter_conditions.items():
                        if field in data and data[field] != value:
                            return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying data filters: {e}")
            return True  # Default to allowing data if filter fails

class CacheManager:
    """Manage cache operations"""
    
    @staticmethod
    def clear_model_cache(model_name):
        """Clear cache for a specific model"""
        cache_keys = [
            f"sb_sync_model_fields_{model_name}",
            f"sb_sync_model_permissions_{model_name}",
            f"sb_sync_model_filters_{model_name}"
        ]
        
        for key in cache_keys:
            cache.delete(key)
    
    @staticmethod
    def clear_organization_cache(organization_id):
        """Clear cache for a specific organization"""
        cache_keys = [
            f"sb_sync_org_permissions_{organization_id}",
            f"sb_sync_org_filters_{organization_id}",
            f"sb_sync_org_config_{organization_id}"
        ]
        
        for key in cache_keys:
            cache.delete(key)
    
    @staticmethod
    def clear_user_cache(user_id):
        """Clear cache for a specific user"""
        cache_keys = [
            f"sb_sync_user_permissions_{user_id}",
            f"sb_sync_user_filters_{user_id}",
            f"sb_sync_user_org_{user_id}"
        ]
        
        for key in cache_keys:
            cache.delete(key)
