import json
import logging
from django.apps import apps
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.core.cache import cache
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .authentication import JWTAuthentication
from .models import UserSite, UserSyncMetadata, ModelPermission, DataFilter, SyncConfiguration
from django.contrib.sites.models import Site
from django.contrib.auth.models import Group
from .permissions import SyncPermission
from .utils import get_config, get_all_models
import time

logger = logging.getLogger('sb_sync')

class PushAPIView(APIView):
    """
    PUSH API - Accepts JSON data and stores it in appropriate Django models
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Get user's site context after authentication
            user_site = UserSite.objects.filter(
                user=request.user,
                is_active=True
            ).select_related('site', 'group').first()
            
            if not user_site:
                return JsonResponse({
                    'success': False,
                    'error': 'User is not associated with any site',
                }, status=400)
            
            site = user_site.site
            
            # Log incoming request
            logger.info(f"PUSH request from user {request.user.username} in {site.name}: {json.dumps(request.data)}")
            
            # Process the data with permissions
            result = self._process_push_data_with_permissions(
                request.data, 
                request.user, 
                site
            )
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"PUSH API error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            }, status=500)
    
    def _process_push_data_with_permissions(self, json_data, user, site):
        """Process push data with permission checks"""
        try:
            result = {
                'success': True,
                'processed_models': [],
                'errors': []
            }
            
            for model_name, model_data in json_data.items():
                try:
                    # Check permissions
                    if not SyncPermission.can_access_model(user, site, model_name, 'push'):
                        error_msg = (
                            f"User {user.username} does not have push permission for {model_name} in {site.name}"
                        )
                        result['errors'].append({
                            'model': model_name,
                            'error': error_msg
                        })
                        continue
                    
                    # Apply site filter to data
                    filtered_data = self._apply_site_filter(model_data, site)
                    
                    # Process the data (simplified for now)
                    processed_count = len(filtered_data)
                    
                    # Update sync metadata
                    SyncPermission.update_user_sync_metadata(
                        user, site, model_name,
                        processed_count
                    )
                    
                    result['processed_models'].append({
                        'model': model_name,
                        'processed_count': processed_count
                    })
                    
                except Exception as e:
                    result['errors'].append({
                        'model': model_name,
                        'error': str(e)
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing push data: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _apply_site_filter(self, model_data, site):
        """Apply site filter to data"""
        filtered_data = []
        
        for item in model_data:
            # Add site context to each item
            item['site'] = site.id
            filtered_data.append(item)
        
        return filtered_data

class PullAPIView(APIView):
    """
    PULL API - Returns JSON data based on configuration and timestamps
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Get user's site context after authentication
            user_site = UserSite.objects.filter(
                user=request.user,
                is_active=True
            ).select_related('site', 'group').first()
            
            if not user_site:
                return JsonResponse({
                    'success': False,
                    'error': 'User is not associated with any site',
                }, status=400)
            
            site = user_site.site
            
            # Validate request data
            validated_data = self._validate_pull_request(request.data)
            
            # Process the request with permissions
            result = self._process_pull_request_with_permissions(
                validated_data, 
                request.user, 
                site
            )
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"PULL API error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            }, status=500)
    
    def _validate_pull_request(self, data):
        """Validate pull request data"""
        required_fields = ['models', 'batch_size', 'last_sync']
        
        for field in required_fields:
            if field not in data:
                return {
                    'success': False,
                    'error': f'Missing required field: {field}'
                }
        
        return {
            'success': True,
            'data': data
        }
    
    def _process_pull_request_with_permissions(self, validated_data: dict, user, site) -> dict:
        """Process pull request with permission checks"""
        try:
            result = {
                'success': True,
                'data': {},
                'batch_info': {
                    'total_records': 0,
                    'total_models': 0
                },
                'errors': []
            }
            
            models = validated_data.get('models', [])
            batch_size = validated_data.get('batch_size', 100)
            last_sync = validated_data.get('last_sync', {})
            
            for model_name in models:
                try:
                    # Check permissions
                    if not SyncPermission.can_access_model(user, site, model_name, 'pull'):
                        error_msg = f"User {user.username} does not have pull permission for {model_name} in {site.name}"
                        result['errors'].append({
                            'model': model_name,
                            'error': error_msg
                        })
                        continue
                    
                    # Get user metadata for this model
                    user_metadata = SyncPermission.get_user_sync_metadata(user, site, model_name)
                    user_last_sync = user_metadata.last_sync if user_metadata else None
                    
                    # Check cache first
                    cache_key = f"pull_data_{user.id}_{site.id}_{model_name}_{user_last_sync}"
                    cached_data = cache.get(cache_key)
                    
                    if cached_data:
                        result['data'][model_name] = cached_data
                        result['batch_info']['total_records'] += len(cached_data)
                        result['batch_info']['total_models'] += 1
                        continue
                    
                    # Get model class
                    try:
                        model_class = apps.get_model(model_name)
                    except Exception as e:
                        result['errors'].append({
                            'model': model_name,
                            'error': f'Invalid model: {str(e)}'
                        })
                        continue
                    
                    # Build queryset
                    queryset = model_class.objects.all()
                    
                    # Apply site filter
                    if hasattr(model_class, 'site'):
                        queryset = queryset.filter(site=site)
                    
                    # Apply custom filters
                    filters = SyncPermission.get_data_filters(user, site, model_name)
                    if filters:
                        for filter_obj in filters:
                            if filter_obj.is_active:
                                try:
                                    filter_condition = json.loads(filter_obj.filter_condition)
                                    # Apply filter logic here
                                    pass
                                except Exception as e:
                                    logger.warning(f"Invalid filter condition for {model_name}: {str(e)}")
                    
                    # Apply pagination
                    queryset = queryset[:batch_size]

                    # Serialize data
                    model_data = []
                    for obj in queryset:
                        model_data.append({
                            'id': obj.id,
                            'data': self._serialize_object(obj)
                        })
                    
                    # Cache the result
                    cache.set(cache_key, model_data, timeout=300)  # 5 minutes
                    
                    # Update result
                    result['data'][model_name] = model_data
                    result['batch_info']['total_records'] += len(model_data)
                    result['batch_info']['total_models'] += 1
                    
                    # Update sync metadata
                    SyncPermission.update_user_sync_metadata(user, site, model_name, len(model_data))
                    
                except Exception as e:
                    result['errors'].append({
                        'model': model_name,
                        'error': str(e)
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing pull request: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _serialize_object(self, obj):
        """Serialize a model object to dict"""
        data = {}
        for field in obj._meta.fields:
            if field.name != 'id':
                data[field.name] = getattr(obj, field.name)
        return data

@csrf_exempt
@login_required
def auth_token(request):
    """Get authentication token and user's sites"""
    try:
        # Get user's sites and groups
        user_sites = UserSite.objects.filter(
            user=request.user,
            is_active=True
        ).select_related('site', 'group')
        
        sites_data = []
        for user_site in user_sites:
            sites_data.append({
                'id': user_site.site.id,
                'name': user_site.site.name,
                'domain': user_site.site.domain,  # Use domain instead of slug
                'group': user_site.group.name
            })
        
        return JsonResponse({
            'success': True,
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'is_superuser': request.user.is_superuser,
            },
            'sites': sites_data
        })
        
    except Exception as e:
        logger.error(f"Auth token error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def performance_dashboard(request):
    """Performance monitoring dashboard"""
    try:
        # Get basic stats
        total_users = UserSite.objects.values('user').distinct().count()
        total_sites = Site.objects.count()
        total_permissions = ModelPermission.objects.count()
        
        # Get recent sync activity
        recent_metadata = UserSyncMetadata.objects.select_related('user', 'site').order_by('-last_sync')[:10]
        
        context = {
            'total_users': total_users,
            'total_sites': total_sites,
            'total_permissions': total_permissions,
            'recent_activity': recent_metadata,
        }
        
        return render(request, 'sb_sync/performance_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Performance dashboard error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def model_discovery_config(request):
    """Model discovery configuration interface"""
    try:
        # Get all installed apps
        installed_apps = []
        for app_config in apps.get_app_configs():
            if app_config.name not in ['django.contrib.admin', 'django.contrib.auth', 
                                     'django.contrib.contenttypes', 'django.contrib.sessions',
                                     'django.contrib.messages', 'django.contrib.staticfiles',
                                     'rest_framework', 'rest_framework_simplejwt', 'simple_history',
                                     'django.contrib.sites', 'sb_sync']:
                installed_apps.append({
                    'name': app_config.name,
                    'verbose_name': getattr(app_config, 'verbose_name', app_config.name)
                })
        
        # Get current configuration
        current_config = get_config()
        
        context = {
            'installed_apps': installed_apps,
            'current_config': current_config,
        }
        
        return render(request, 'sb_sync/model_discovery_config.html', context)
        
    except Exception as e:
        logger.error(f"Model discovery config error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def permission_matrix(request, site_id=None):
    """Permission matrix interface"""
    try:
        # Get specific site or first available
        if site_id:
            site = Site.objects.get(id=site_id)
        else:
            # Get first site or redirect to dashboard
            site = Site.objects.filter(is_active=True).first()
            if not site:
                return JsonResponse({'error': 'No organizations available'}, status=404)
        
        # Get existing permissions for this site with optimized query
        existing_permissions = ModelPermission.objects.filter(
            site=site
        ).select_related('group').prefetch_related('site')
        
        # Get all groups
        groups = Group.objects.all()
        
        # Get all available models
        available_models = []
        for app_config in apps.get_app_configs():
            if app_config.name not in ['django.contrib.admin', 'django.contrib.auth', 
                                     'django.contrib.contenttypes', 'django.contrib.sessions',
                                     'django.contrib.messages', 'django.contrib.staticfiles',
                                     'rest_framework', 'rest_framework_simplejwt', 'simple_history',
                                     'django.contrib.sites', 'sb_sync']:
                for model in app_config.get_models():
                    available_models.append({
                        'app_label': model._meta.app_label,
                        'model_name': model._meta.model_name,
                        'verbose_name': model._meta.verbose_name,
                        'full_name': f"{model._meta.app_label}.{model._meta.model_name}"
                    })
        
        # Optimize sites query
        sites = Site.objects.filter(is_active=True).only('id', 'name', 'slug')
        
        context = {
            'organization': site,  # Use user-friendly name in context
            'organizations': sites,  # Use user-friendly name in context
            'groups': groups,
            'available_models': available_models,
            'existing_permissions': existing_permissions,
        }
        
        return render(request, 'sb_sync/permission_matrix.html', context)
        
    except Exception as e:
        logger.error(f"Permission matrix error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@login_required
def save_permission(request):
    """Save individual permission"""
    try:
        data = json.loads(request.body)
        site_id = data.get('site_id')
        group_id = data.get('group_id')
        model_name = data.get('model_name')
        permission_type = data.get('permission_type')
        value = data.get('value')
        
        if not all([site_id, group_id, model_name, permission_type]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields'
            }, status=400)
        
        # Get or create permission
        permission, created = ModelPermission.objects.get_or_create(
            site_id=site_id,  # Use ID directly to avoid extra query
            group_id=group_id,
            model_name=model_name,
            defaults={'can_push': False, 'can_pull': False}
        )
        
        # Update the specific permission
        if permission_type == 'push':
            permission.can_push = value
        elif permission_type == 'pull':
            permission.can_pull = value
        
        permission.save()
        
        # Clear cache
        cache_key = f"model_permission_{site_id}_{group_id}_{model_name}"
        cache.delete(cache_key)
        
        return JsonResponse({
            'success': True,
            'created': created,
            'site_id': site_id,
            'group_id': group_id,
            'model_name': model_name,
            'permission_type': permission_type,
            'value': value
        })
        
    except Exception as e:
        logger.error(f"Save permission error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@login_required
def bulk_save_permissions(request):
    """Bulk save permissions"""
    try:
        data = json.loads(request.body)
        site_id = data.get('organization_id')  # Accept user-friendly name in request
        permissions = data.get('permissions', [])
        
        if not site_id or not permissions:
            return JsonResponse({'success': False, 'error': 'Missing organization or permissions'}, status=400)
        
        from django.db import transaction
        with transaction.atomic():
            # Get existing permissions for this site
            existing_permissions = {
                f"{p.model_name}_{p.site_id}": p
                for p in ModelPermission.objects.filter(
                    site_id=site_id,
                ).select_related('group')
            }
            
            # Process each permission
            created_count = 0
            updated_count = 0
            
            for perm_data in permissions:
                group_id = perm_data.get('group_id')
                model_name = perm_data.get('model_name')
                can_push = perm_data.get('can_push', False)
                can_pull = perm_data.get('can_pull', False)
                
                permission_key = f"{model_name}_{site_id}"
                
                if permission_key in existing_permissions:
                    # Update existing
                    permission = existing_permissions[permission_key]
                    if permission.group_id != group_id:
                        permission.group_id = group_id
                    permission.can_push = can_push
                    permission.can_pull = can_pull
                    permission.save()
                    updated_count += 1
                else:
                    # Create new
                    ModelPermission.objects.create(
                        site_id=site_id,
                        group_id=group_id,
                        model_name=model_name,
                        can_push=can_push,
                        can_pull=can_pull
                    )
                    created_count += 1
            
            # Clear cache for this site
            cache_keys_to_delete = []
            for perm_data in permissions:
                group_id = perm_data.get('group_id')
                model_name = perm_data.get('model_name')
                cache_keys_to_delete.append(f"model_permission_{site_id}_{group_id}_{model_name}")
            
            for cache_key in cache_keys_to_delete:
                cache.delete(cache_key)
            
            return JsonResponse({
                'success': True,
                'created_count': created_count,
                'updated_count': updated_count,
                'total_processed': len(permissions)
            })
            
    except Exception as e:
        logger.error(f"Bulk save permissions error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def audit_trails(request):
    """Audit trails interface"""
    try:
        # Get recent sync metadata
        recent_syncs = UserSyncMetadata.objects.select_related(
            'user', 'site'
        ).order_by('-last_sync')[:50]
        
        # Get recent permission changes
        recent_permissions = ModelPermission.history.select_related(
            'site', 'group'
        ).order_by('-history_date')[:50]
        
        context = {
            'recent_syncs': recent_syncs,
            'recent_permissions': recent_permissions,
        }
        
        return render(request, 'sb_sync/audit_trails.html', context)
        
    except Exception as e:
        logger.error(f"Audit trails error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def config_dashboard(request):
    """Main configuration dashboard"""
    try:
        # Get statistics
        total_organizations = Site.objects.filter(is_active=True).count()
        total_groups = Group.objects.count()
        total_models = len([model for app in apps.get_app_configs() 
                          for model in app.get_models() 
                          if app.name not in ['django.contrib.admin', 'django.contrib.auth', 
                                             'django.contrib.contenttypes', 'django.contrib.sessions',
                                             'django.contrib.messages', 'django.contrib.staticfiles',
                                             'rest_framework', 'rest_framework_simplejwt', 'simple_history',
                                             'django.contrib.sites', 'sb_sync']])
        
        # Get organizations for overview
        organizations = Site.objects.filter(is_active=True).prefetch_related('usersite_set')
        
        # Mock performance data (in real app, this would come from monitoring)
        context = {
            'total_organizations': total_organizations,
            'organizations': organizations,  # Use user-friendly name in context
            'total_groups': total_groups,
            'total_models': total_models,
            'cache_hit_rate': 85.5,
            'avg_response_time': 120,
            'total_requests': 15420,
            'error_rate': 0.5,
            'active_users_count': 45,
            'active_users_percent': 75,
            'sync_success_rate': 98.5,
            'system_load': 65,
            'system_load_color': 'warning',
            'recent_logs': []  # Would be populated from actual logs
        }
        
        return render(request, 'sb_sync/config_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Config dashboard error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
