"""
Utility functions for sb-sync package
"""
import json
import logging
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.apps import apps
from django.db import transaction
from .models import UserSite, ModelPermission, DataFilter, SyncConfiguration

logger = logging.getLogger(__name__)

def get_model_permission_templates():
    """Get available permission templates"""
    return {
        'read_only': {
            'can_push': False,
            'can_pull': True,
        },
        'write_only': {
            'can_push': True,
            'can_pull': False,
        },
        'read_write': {
            'can_push': True,
            'can_pull': True,
        },
        'admin': {
            'can_push': True,
            'can_pull': True,
        }
    }

def get_default_models():
    """Get list of default models to include"""
    return [
        'auth.User',
        'auth.Group',
        'sites.Site',
    ]

def is_model_enabled(model_name, config=None):
    """Check if a model is enabled based on configuration"""
    if config is None:
        config = get_config()
    
    # Check include patterns
    include_patterns = config.get('include_patterns', [])
    for pattern in include_patterns:
        if pattern in model_name:
            return True
    
    # Check exclude patterns
    exclude_patterns = config.get('exclude_patterns', [])
    for pattern in exclude_patterns:
        if pattern in model_name:
            return False
    
    # Check include apps
    include_apps = config.get('include_apps', [])
    if include_apps:
        app_label = model_name.split('.')[0]
        if app_label not in include_apps:
            return False
    
    # Check exclude apps
    exclude_apps = config.get('exclude_apps', [])
    if exclude_apps:
        app_label = model_name.split('.')[0]
        if app_label in exclude_apps:
            return False
    
    return True

def get_all_models():
    """Get all available models"""
    models = []
    for app_config in apps.get_app_configs():
        if app_config.name not in ['django.contrib.admin', 'django.contrib.auth', 
                                 'django.contrib.contenttypes', 'django.contrib.sessions',
                                 'django.contrib.messages', 'django.contrib.staticfiles',
                                 'rest_framework', 'rest_framework_simplejwt', 'simple_history',
                                 'django.contrib.sites', 'sb_sync']:
            for model in app_config.get_models():
                model_name = f"{model._meta.app_label}.{model._meta.model_name}"
                if is_model_enabled(model_name):
                    models.append({
                        'app_label': model._meta.app_label,
                        'model_name': model._meta.model_name,
                        'verbose_name': model._meta.verbose_name,
                        'full_name': model_name
                    })
    return models

def get_config():
    """Get current configuration from database"""
    config = {}
    try:
        configs = SyncConfiguration.objects.all()
        for config_obj in configs:
            try:
                value = json.loads(config_obj.value)
            except (json.JSONDecodeError, TypeError):
                value = config_obj.value
            config[config_obj.key] = value
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
    
    return config

def set_config(key, value, description=""):
    """Set configuration value"""
    try:
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        elif not isinstance(value, str):
            value = str(value)
        
        config_obj, created = SyncConfiguration.objects.get_or_create(
            key=key,
            defaults={'value': value, 'description': description}
        )
        
        if not created:
            config_obj.value = value
            config_obj.description = description
            config_obj.save()
        
        return True
    except Exception as e:
        logger.error(f"Error setting configuration {key}: {str(e)}")
        return False

def reset_config():
    """Reset configuration to defaults"""
    try:
        SyncConfiguration.objects.all().delete()
        
        # Set default values
        defaults = {
            'include_apps': [],
            'exclude_apps': ['django.contrib.admin', 'django.contrib.auth', 
                           'django.contrib.contenttypes', 'django.contrib.sessions',
                           'django.contrib.messages', 'django.contrib.staticfiles',
                           'rest_framework', 'rest_framework_simplejwt', 'simple_history',
                           'django.contrib.sites', 'sb_sync'],
            'include_patterns': [],
            'exclude_patterns': [],
            'exclude_fields': ['id', 'created_at', 'updated_at'],
            'require_fields': [],
            'model_types': ['models.Model'],
            'enable_caching': True,
            'cache_timeout': 300,
            'max_models': 100,
            'batch_size': 100,
            'enable_multi_tenant': True,
            'enable_data_filtering': True,
            'default_filter_template': 'site',
        }
        
        for key, value in defaults.items():
            set_config(key, value)
        
        return True
    except Exception as e:
        logger.error(f"Error resetting configuration: {str(e)}")
        return False

def generate_permission_config(site, models=None, groups=None, template='read_write'):
    """Generate permission configuration for site"""
    if models is None:
        models = get_all_models()
        
    if groups is None:
        groups = Group.objects.all()
    
    templates = get_model_permission_templates()
    template_config = templates.get(template, templates['read_write'])
    
    config = {
        'site': site.id,
        'permissions': []
    }
    
    for model in models:
        model_name = model.get('full_name', f"{model['app_label']}.{model['model_name']}")
        for group in groups:
            config['permissions'].append({
                'group': group.id,
                'model_name': model_name,
                'can_push': template_config['can_push'],
                'can_pull': template_config['can_pull']
            })
    
    return config

def apply_permission_config(site, config):
    """Apply permission configuration to site"""
    try:
        with transaction.atomic():
            # Clear existing permissions for this site
            ModelPermission.objects.filter(site=site).delete()
            
            # Create new permissions
            permissions = []
            for perm_data in config.get('permissions', []):
                permission = ModelPermission(
                    site=site,
                    group_id=perm_data['group'],
                    model_name=perm_data['model_name'],
                    can_push=perm_data.get('can_push', False),
                    can_pull=perm_data.get('can_pull', False)
                )
                permissions.append(permission)
            
            if permissions:
                ModelPermission.objects.bulk_create(permissions)
            
            # Clear cache
            clear_site_cache(site.id)
            
            return True
    except Exception as e:
        logger.error(f"Error applying permission config: {str(e)}")
        return False

def export_permission_config(site):
    """Export permission configuration for site"""
    try:
        permissions = ModelPermission.objects.filter(site=site)
        
        config = {
            'site': site.id,
            'permissions': []
        }
        
        for permission in permissions:
            config['permissions'].append({
                'group': permission.group.id,
                'model_name': permission.model_name,
                'can_push': permission.can_push,
                'can_pull': permission.can_pull
            })
        
        return config
    except Exception as e:
        logger.error(f"Error exporting permission config: {str(e)}")
        return None

def generate_data_filters(site, models=None, groups=None):
    """Generate data filters for site"""
    if models is None:
        models = get_all_models()
        
    if groups is None:
        groups = Group.objects.all()
    
    filters = []
    
    for model in models:
        model_name = model.get('full_name', f"{model['app_label']}.{model['model_name']}")
        for group in groups:
            # Create basic filter
            filter_condition = {
                'field': 'site',
                'operator': 'exact',
                'value': site.id
            }
            
            filters.append({
                'site': site.id,
                'group': group.id,
                'model_name': model_name,
                'filter_name': f"{group.name}_filter",
                'filter_condition': json.dumps(filter_condition),
                'is_active': True
            })
    
    return filters

def apply_data_filters(site, filters):
    """Apply data filters to site"""
    try:
        with transaction.atomic():
            # Clear existing filters for this site
            DataFilter.objects.filter(site=site).delete()
            
            # Create new filters
            filter_objects = []
            for filter_data in filters:
                filter_obj = DataFilter(
                    site=site,
                    group_id=filter_data['group'],
                    model_name=filter_data['model_name'],
                    filter_name=filter_data['filter_name'],
                    filter_condition=filter_data['filter_condition'],
                    is_active=filter_data.get('is_active', True)
                )
                filter_objects.append(filter_obj)
            
            if filter_objects:
                DataFilter.objects.bulk_create(filter_objects)
            
            return True
    except Exception as e:
        logger.error(f"Error applying data filters: {str(e)}")
        return False

def get_user_context(user):
    """Get user's context including sites and groups"""
    try:
        user_sites = UserSite.objects.filter(
            user=user,
            is_active=True
        ).select_related('site', 'group')
        
        context = {
            'user': user,
            'sites': [],
            'groups': []
        }
        
        for user_site in user_sites:
            context['sites'].append(user_site.site)
            if user_site.group not in context['groups']:
                context['groups'].append(user_site.group)
        
        return context
    except Exception as e:
        logger.error(f"Error getting user context: {str(e)}")
        return None

def apply_data_filters_to_queryset(queryset, user, model_name):
    """Apply data filters based on user's site and groups"""
    try:
        user_context = get_user_context(user)
        if not user_context:
            return queryset
        
        # Get filters for user's groups
        filters = DataFilter.objects.filter(
            site__in=user_context['sites'],
            group__in=user_context['groups'],
            model_name=model_name,
            is_active=True
        )
        
        for filter_obj in filters:
            try:
                filter_condition = json.loads(filter_obj.filter_condition)
                # Apply filter logic here
                pass
            except Exception as e:
                logger.warning(f"Invalid filter condition: {str(e)}")
        
        return queryset
    except Exception as e:
        logger.error(f"Error applying data filters: {str(e)}")
        return queryset

def get_user_sync_context(user):
    """Get user's sync context"""
    try:
        # Get user's site
        user_site = user.usersite_set.first()
        if not user_site:
            return None
        
        context = {
            'user': user,
            'site': user_site.site,
            'group': user_site.group,
            'permissions': ModelPermission.objects.filter(
                site=user_site.site,
                group=user_site.group
            )
        }
        
        return context
    except Exception as e:
        logger.error(f"Error getting user sync context: {str(e)}")
        return None

def clear_site_cache(site_id):
    """Clear cache for a specific site"""
    cache_keys = [
        f"sb_sync_site_permissions_{site_id}",
        f"sb_sync_site_filters_{site_id}",
        f"sb_sync_site_config_{site_id}"
    ]
    
    for key in cache_keys:
        cache.delete(key)
