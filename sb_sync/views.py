import json
import logging
from django.apps import apps
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.core.cache import cache
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .authentication import JWTAuthentication
from .serializers import PushDataSerializer, PullRequestSerializer
from .models import SyncLog, SyncMetadata, Organization, UserOrganization, UserSyncMetadata, ModelPermission, Group
from .permissions import MultiTenantPermission, SyncPermission, MultiTenantMixin
from .utils import DataProcessor, ModelIntrospector
from .config import get_config, get_default_models, is_model_enabled, get_all_models
from .optimizations import (
    QueryOptimizer, BulkOperations, MemoryOptimizer, 
    CacheOptimizer, PerformanceMonitor, AsyncProcessor
)
from .error_handling import (
    handle_errors, retry_on_error, with_recovery,
    SyncError, ValidationError, AuthenticationError, DatabaseError,
    error_handler, partial_success_handler, retry_handler
)
import time

logger = logging.getLogger('sb_sync')

class PushAPIView(APIView, MultiTenantMixin):
    """
    PUSH API - Accepts JSON data and stores it in appropriate Django models
    Now with multi-tenant and role-based access control
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, MultiTenantPermission]
    
    @handle_errors
    @retry_on_error
    @with_recovery
    @QueryOptimizer.count_queries
    @MemoryOptimizer.monitor_memory
    def post(self, request):
        start_time = time.time()
        
        # Get user's organization context
        organization = getattr(request, 'organization', None)
        if not organization:
            raise ValidationError(
                'User is not associated with any organization',
                context={'user_id': request.user.id}
            )
        
        # Log incoming request
        logger.info(f"PUSH request from user {request.user.username} in {organization.name}: {json.dumps(request.data)}")
        
        # Validate request data
        serializer = PushDataSerializer(data=request.data)
        if not serializer.is_valid():
            raise ValidationError(
                f"Invalid request data: {serializer.errors}",
                context={'serializer_errors': serializer.errors}
            )
        
        # Process the data with multi-tenant permissions
        results = retry_handler.retry(
            self._process_push_data_with_permissions,
            serializer.validated_data['data'], 
            request.user,
            organization
        )
        
        # Handle partial success
        total_items = len(serializer.validated_data['data'])
        response_data = partial_success_handler.handle_partial_success(results, total_items)
        
        # Add processing time
        processing_time = time.time() - start_time
        response_data['processing_time'] = processing_time
        
        # Track performance metrics
        PerformanceMonitor.track_performance(
            operation_type='PUSH',
            model_name='multiple',
            batch_size=total_items,
            processing_time=processing_time,
            query_count=results.get('query_count', 0)
        )
        
        # Log the operation
        self.log_sync_operation(
            user=request.user,
            operation='PUSH',
            status=response_data['status'].upper(),
            object_count=response_data['success_count'],
            error_message='; '.join(results.get('errors', [])) if results.get('errors') else '',
            request_data=request.data,
            processing_time=response_data['processing_time']
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    def _process_push_data_with_permissions(self, json_data, user, organization):
        """Process push data with multi-tenant permissions"""
        start_time = time.time()
        results = {
            'success_count': 0,
            'error_count': 0,
            'errors': [],
            'processed_models': {},
            'query_count': 0
        }
        
        # Group data by model for bulk operations
        model_groups = {}
        for item_data in json_data:
            model_name = item_data.get('_model')
            if model_name:
                # Check if model is enabled in configuration
                if not is_model_enabled(model_name):
                    results['errors'].append(f"Model {model_name} is not enabled for sync operations")
                    results['error_count'] += 1
                    continue
                
                if model_name not in model_groups:
                    model_groups[model_name] = []
                model_groups[model_name].append(item_data)
        
        # Process each model group with permissions
        for model_name, model_data in model_groups.items():
            try:
                # Check if user has push permission for this model
                if not SyncPermission.can_access_model(user, organization, model_name, 'push'):
                    results['errors'].append(
                        f"User {user.username} does not have push permission for {model_name} in {organization.name}"
                    )
                    results['error_count'] += len(model_data)
                    continue
                
                model_class = apps.get_model(model_name)
                
                # Apply organization filter to data
                filtered_data = self._apply_organization_filter(model_data, organization)
                
                # Use bulk operations for better performance
                bulk_results = BulkOperations.bulk_create_or_update(
                    model_class, filtered_data, batch_size=1000
                )
                
                results['success_count'] += bulk_results['created'] + bulk_results['updated']
                results['processed_models'][model_name] = bulk_results
                
                # Update user sync metadata
                SyncPermission.update_user_sync_metadata(
                    user, organization, model_name, 
                    bulk_results['created'] + bulk_results['updated']
                )
                
            except Exception as e:
                results['errors'].append(f"Error processing model {model_name}: {str(e)}")
                results['error_count'] += len(model_data)
        
        results['processing_time'] = time.time() - start_time
        return results
    
    def _apply_organization_filter(self, model_data, organization):
        """Apply organization filter to data"""
        filtered_data = []
        
        for item in model_data:
            # Add organization context to each item
            item['organization'] = organization.id
            filtered_data.append(item)
        
        return filtered_data
    
    def log_sync_operation(self, **kwargs):
        """Log sync operation to database"""
        try:
            SyncLog.objects.create(**kwargs)
        except Exception as e:
            logger.error(f"Failed to log sync operation: {str(e)}")

class PullAPIView(APIView, MultiTenantMixin):
    """
    PULL API - Returns JSON data based on configuration and timestamps
    Now with multi-tenant and role-based access control
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, MultiTenantPermission]
    
    @handle_errors
    @retry_on_error
    @with_recovery
    @QueryOptimizer.count_queries
    @MemoryOptimizer.monitor_memory
    def post(self, request):
        start_time = time.time()
        
        # Get user's organization context
        organization = getattr(request, 'organization', None)
        if not organization:
            raise ValidationError(
                'User is not associated with any organization',
                context={'user_id': request.user.id}
            )
        
        # Validate request data
        serializer = PullRequestSerializer(data=request.data)
        if not serializer.is_valid():
            raise ValidationError(
                f"Invalid request data: {serializer.errors}",
                context={'serializer_errors': serializer.errors}
            )
        
        # Process request with multi-tenant permissions
        response_data = retry_handler.retry(
            self._process_pull_request_with_permissions,
            serializer.validated_data,
            request.user,
            organization
        )
        
        # Track performance metrics
        processing_time = time.time() - start_time
        PerformanceMonitor.track_performance(
            operation_type='PULL',
            model_name='multiple',
            batch_size=response_data['batch_info']['total_records'],
            processing_time=processing_time,
            query_count=response_data.get('query_count', 0)
        )
        
        # Log the operation
        self.log_sync_operation(
            user=request.user,
            operation='PULL',
            status='SUCCESS',
            object_count=response_data['batch_info']['total_records'],
            processing_time=processing_time
        )
        
        logger.info(f"PULL request completed for user {request.user.username} in {organization.name}: {response_data['batch_info']['total_records']} records")
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    def _process_pull_request_with_permissions(self, validated_data: dict, user, organization) -> dict:
        """Process pull request with multi-tenant permissions"""
        models_config = validated_data.get('models', {})
        
        # If no models specified, use default models from configuration
        if not models_config:
            default_models = get_default_models()
            models_config = {model: None for model in default_models}
            logger.info(f"No models specified in request, using {len(default_models)} default models")
        
        batch_size = validated_data.get('batch_size', 
            get_config('CORE', 'DEFAULT_BATCH_SIZE'))
        
        response_data = {
            'data': [],
            'metadata': {},
            'batch_info': {
                'batch_size': batch_size,
                'total_records': 0
            },
            'query_count': 0
        }
        
        total_records = 0
        
        for model_name, last_sync_time in models_config.items():
            try:
                # Check if model is enabled in configuration
                if not is_model_enabled(model_name):
                    response_data['metadata'][model_name] = {
                        'error': f"Model {model_name} is not enabled for sync operations",
                        'count': 0
                    }
                    continue
                
                # Check if user has pull permission for this model
                if not SyncPermission.can_access_model(user, organization, model_name, 'pull'):
                    response_data['metadata'][model_name] = {
                        'error': f"User {user.username} does not have pull permission for {model_name} in {organization.name}",
                        'count': 0
                    }
                    continue
                
                # Get user's last sync time for this model
                user_metadata = SyncPermission.get_user_sync_metadata(user, organization, model_name)
                user_last_sync = user_metadata.last_sync
                
                # Check cache first
                cache_key = f"pull_data_{user.id}_{organization.id}_{model_name}_{user_last_sync}"
                cached_data = CacheOptimizer.get_cached_model_data(cache_key)
                
                if cached_data:
                    response_data['data'].extend(cached_data['data'])
                    response_data['metadata'][model_name] = cached_data['metadata']
                    total_records += cached_data['count']
                    continue
                
                # Get model class
                model_class = apps.get_model(model_name)
                
                # Build base queryset
                queryset = model_class.objects.all()
                
                # Apply organization filter
                if hasattr(model_class, 'organization'):
                    queryset = queryset.filter(organization=organization)
                
                # Apply user-specific data filters
                filters = SyncPermission.get_data_filters(user, organization, model_name)
                queryset = SyncPermission.apply_filters_to_queryset(queryset, filters)
                
                # Filter by timestamp if provided
                if user_last_sync:
                    # Assume models have created_at/updated_at fields
                    timestamp_filter = Q()
                    if hasattr(model_class, 'created_at'):
                        timestamp_filter |= Q(created_at__gt=user_last_sync)
                    if hasattr(model_class, 'updated_at'):
                        timestamp_filter |= Q(updated_at__gt=user_last_sync)
                    
                    if timestamp_filter:
                        queryset = queryset.filter(timestamp_filter)
                
                # Apply batch size limit and optimize query
                queryset = queryset[:batch_size]
                
                # Use values() for better performance
                model_data = []
                for obj in queryset.values():
                    obj_data = {'_model': model_name}
                    obj_data.update(obj)
                    model_data.append(obj_data)
                
                response_data['data'].extend(model_data)
                
                # Update metadata
                model_metadata = {
                    'count': len(model_data),
                    'last_sync': timezone.now().isoformat(),
                    'user_last_sync': user_last_sync.isoformat() if user_last_sync else None
                }
                response_data['metadata'][model_name] = model_metadata
                
                # Cache the results
                cache_data = {
                    'data': model_data,
                    'metadata': model_metadata,
                    'count': len(model_data)
                }
                CacheOptimizer.cache_model_data(cache_key, cache_data, timeout=300)  # 5 minutes
                
                total_records += len(model_data)
                
                # Update user sync metadata
                SyncPermission.update_user_sync_metadata(user, organization, model_name, len(model_data))
                
            except LookupError:
                logger.warning(f"Model '{model_name}' not found")
                response_data['metadata'][model_name] = {
                    'error': f"Model '{model_name}' not found",
                    'count': 0
                }
            except Exception as e:
                logger.error(f"Error processing model '{model_name}': {str(e)}")
                response_data['metadata'][model_name] = {
                    'error': str(e),
                    'count': 0
                }
        
        response_data['batch_info']['total_records'] = total_records
        return response_data
    
    def log_sync_operation(self, **kwargs):
        """Log sync operation to database"""
        try:
            SyncLog.objects.create(**kwargs)
        except Exception as e:
            logger.error(f"Failed to log sync operation: {str(e)}")

class AuthTokenView(APIView):
    """
    Generate JWT token for authentication
    """
    @handle_errors
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            raise ValidationError(
                'Username and password required',
                context={'missing_fields': [f for f in ['username', 'password'] if not request.data.get(f)]}
            )
        
        from django.contrib.auth import authenticate
        user = authenticate(username=username, password=password)
        
        if user:
            # Get user's organizations and groups
            user_organizations = UserOrganization.objects.filter(
                user=user,
                is_active=True
            ).select_related('organization', 'group')
            
            organizations_data = []
            for user_org in user_organizations:
                organizations_data.append({
                    'id': user_org.organization.id,
                    'name': user_org.organization.name,
                    'slug': user_org.organization.slug,
                    'group': user_org.group.name
                })
            
            token = JWTAuthentication.generate_token(user)
            return Response({
                'token': token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                },
                'organizations': organizations_data
            })
        else:
            raise AuthenticationError(
                'Invalid credentials',
                context={'username': username}
            )

class PerformanceView(APIView):
    """
    Performance monitoring and statistics
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get performance statistics"""
        days = int(request.GET.get('days', 7))
        
        # Get performance stats
        stats = PerformanceMonitor.get_performance_stats(days)
        
        # Get memory usage
        memory_usage = MemoryOptimizer.get_memory_usage()
        
        # Get cache statistics
        cache_stats = {
            'cache_hits': cache.get('cache_hits', 0),
            'cache_misses': cache.get('cache_misses', 0),
        }
        
        return Response({
            'performance_stats': stats,
            'current_memory_usage': memory_usage,
            'cache_stats': cache_stats,
            'optimization_suggestions': self._get_optimization_suggestions()
        })
    
    def _get_optimization_suggestions(self):
        """Get optimization suggestions based on current performance"""
        suggestions = []
        
        # Check memory usage
        memory_usage = MemoryOptimizer.get_memory_usage()
        if memory_usage > 500:  # 500MB threshold
            suggestions.append("High memory usage detected. Consider reducing batch sizes.")
        
        # Check cache hit rate
        cache_hits = cache.get('cache_hits', 0)
        cache_misses = cache.get('cache_misses', 0)
        
        if cache_hits + cache_misses > 0:
            hit_rate = cache_hits / (cache_hits + cache_misses)
            if hit_rate < 0.7:  # 70% threshold
                suggestions.append("Low cache hit rate. Consider adjusting cache settings.")
        
        return suggestions


# Web-based Configuration Views

@staff_member_required
def config_dashboard(request):
    """Main configuration dashboard"""
    organizations = Organization.objects.filter(is_active=True)
    groups = Group.objects.all()
    models = get_all_models()
    
    context = {
        'organizations': organizations,
        'groups': groups,
        'models': models,
        'total_models': len(models),
        'total_organizations': organizations.count(),
        'total_groups': groups.count(),
    }
    
    return render(request, 'sb_sync/config_dashboard.html', context)


@staff_member_required
def permission_matrix(request, organization_id=None):
    """Permission matrix view for managing model permissions"""
    if organization_id:
        organization = Organization.objects.get(id=organization_id)
    else:
        # Get first organization or redirect to dashboard
        organization = Organization.objects.filter(is_active=True).first()
        if not organization:
            return redirect('sb_sync:config_dashboard')
    
    groups = Group.objects.all()
    models = get_all_models()
    
    # Get existing permissions for this organization
    existing_permissions = {}
    permissions = ModelPermission.objects.filter(organization=organization)
    for perm in permissions:
        key = f"{perm.group.id}_{perm.model_name}"
        existing_permissions[key] = {
            'can_push': perm.can_push,
            'can_pull': perm.can_pull,
            'can_create': perm.can_create,
            'can_update': perm.can_update,
            'can_delete': perm.can_delete,
            'can_read': perm.can_read,
        }
    
    context = {
        'organization': organization,
        'organizations': Organization.objects.filter(is_active=True),
        'groups': groups,
        'models': models,
        'existing_permissions': existing_permissions,
        'permission_types': [
            ('can_push', 'Push'),
            ('can_pull', 'Pull'),
            ('can_create', 'Create'),
            ('can_update', 'Update'),
            ('can_delete', 'Delete'),
            ('can_read', 'Read'),
        ]
    }
    
    return render(request, 'sb_sync/permission_matrix.html', context)


@csrf_exempt
@require_http_methods(["POST"])
@staff_member_required
def update_permission(request):
    """Update a single permission via AJAX"""
    try:
        data = json.loads(request.body)
        organization_id = data.get('organization_id')
        group_id = data.get('group_id')
        model_name = data.get('model_name')
        permission_type = data.get('permission_type')
        value = data.get('value')
        
        if not all([organization_id, group_id, model_name, permission_type]):
            return JsonResponse({'success': False, 'error': 'Missing required parameters'})
        
        organization = Organization.objects.get(id=organization_id)
        group = Group.objects.get(id=group_id)
        
        # Get or create permission
        permission, created = ModelPermission.objects.get_or_create(
            organization=organization,
            group=group,
            model_name=model_name,
            defaults={
                'can_push': False,
                'can_pull': False,
                'can_create': False,
                'can_update': False,
                'can_delete': False,
                'can_read': True,  # Default to read access
            }
        )
        
        # Update the specific permission
        setattr(permission, permission_type, value)
        permission.save()
        
        # Invalidate cache
        cache_key = f"model_permission_{organization_id}_{group_id}_{model_name}"
        cache.delete(cache_key)
        
        return JsonResponse({
            'success': True,
            'message': f'Permission {permission_type} updated to {value}',
            'permission': {
                'organization_id': organization_id,
                'group_id': group_id,
                'model_name': model_name,
                permission_type: value
            }
        })
        
    except Exception as e:
        logger.error(f"Error updating permission: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
@staff_member_required
def bulk_update_permissions(request):
    """Bulk update permissions"""
    try:
        data = json.loads(request.body)
        organization_id = data.get('organization_id')
        group_id = data.get('group_id')
        permissions = data.get('permissions', [])
        
        if not organization_id or not group_id:
            return JsonResponse({'success': False, 'error': 'Missing organization or group'})
        
        organization = Organization.objects.get(id=organization_id)
        group = Group.objects.get(id=group_id)
        
        updated_count = 0
        for perm_data in permissions:
            model_name = perm_data.get('model_name')
            permission_type = perm_data.get('permission_type')
            value = perm_data.get('value')
            
            if not all([model_name, permission_type]):
                continue
            
            permission, created = ModelPermission.objects.get_or_create(
                organization=organization,
                group=group,
                model_name=model_name,
                defaults={
                    'can_push': False,
                    'can_pull': False,
                    'can_create': False,
                    'can_update': False,
                    'can_delete': False,
                    'can_read': True,
                }
            )
            
            setattr(permission, permission_type, value)
            permission.save()
            updated_count += 1
        
        return JsonResponse({
            'success': True,
            'message': f'Updated {updated_count} permissions',
            'updated_count': updated_count
        })
        
    except Exception as e:
        logger.error(f"Error bulk updating permissions: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


@staff_member_required
def model_discovery_config(request):
    """Model discovery configuration page"""
    from .config import SyncConfig
    
    if request.method == 'POST':
        # Handle form submission
        include_apps = request.POST.getlist('include_apps')
        exclude_models = request.POST.getlist('exclude_models')
        auto_discover = request.POST.get('auto_discover') == 'on'
        include_custom = request.POST.get('include_custom') == 'on'
        
        # Update configuration
        SyncConfig.set_config('MODEL_DISCOVERY', 'AUTO_DISCOVER_MODELS', auto_discover)
        SyncConfig.set_config('MODEL_DISCOVERY', 'INCLUDE_APPS', include_apps)
        SyncConfig.set_config('MODEL_DISCOVERY', 'EXCLUDE_MODELS', exclude_models)
        SyncConfig.set_config('MODEL_DISCOVERY', 'INCLUDE_CUSTOM_MODELS', include_custom)
        
        return redirect('sb_sync:model_discovery_config')
    
    # Get current configuration
    config = SyncConfig.get_config('MODEL_DISCOVERY')
    all_apps = [app.label for app in apps.get_app_configs()]
    all_models = get_all_models()
    
    context = {
        'config': config,
        'all_apps': all_apps,
        'all_models': all_models,
        'discovered_models': get_all_models(),
    }
    
    return render(request, 'sb_sync/model_discovery_config.html', context)


@staff_member_required
def sync_logs(request):
    """View sync logs"""
    logs = SyncLog.objects.all().order_by('-timestamp')[:100]
    
    context = {
        'logs': logs,
        'total_logs': SyncLog.objects.count(),
    }
    
    return render(request, 'sb_sync/sync_logs.html', context)


@staff_member_required
def performance_metrics(request):
    """View performance metrics"""
    from .models import PerformanceMetrics
    
    metrics = PerformanceMetrics.objects.all().order_by('-timestamp')[:50]
    
    context = {
        'metrics': metrics,
        'total_metrics': PerformanceMetrics.objects.count(),
    }
    
    return render(request, 'sb_sync/performance_metrics.html', context)


@staff_member_required
def audit_trails(request):
    """View audit trails for all sync models"""
    from .models import (
        SyncLog, SyncMetadata, PerformanceMetrics, Organization, 
        UserOrganization, ModelPermission, UserSyncMetadata, DataFilter
    )
    
    # Get model choices for filtering
    model_choices = [
        ('SyncLog', 'Sync Logs'),
        ('SyncMetadata', 'Sync Metadata'),
        ('PerformanceMetrics', 'Performance Metrics'),
        ('Organization', 'Organizations'),
        ('UserOrganization', 'User Organizations'),
        ('ModelPermission', 'Model Permissions'),
        ('UserSyncMetadata', 'User Sync Metadata'),
        ('DataFilter', 'Data Filters'),
    ]
    
    # Get filter parameters
    model_type = request.GET.get('model_type', '')
    user_filter = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Get history records based on filters
    history_records = []
    
    if model_type:
        # Get history for specific model type
        if model_type == 'SyncLog':
            history_records = SyncLog.history.all()
        elif model_type == 'SyncMetadata':
            history_records = SyncMetadata.history.all()
        elif model_type == 'PerformanceMetrics':
            history_records = PerformanceMetrics.history.all()
        elif model_type == 'Organization':
            history_records = Organization.history.all()
        elif model_type == 'UserOrganization':
            history_records = UserOrganization.history.all()
        elif model_type == 'ModelPermission':
            history_records = ModelPermission.history.all()
        elif model_type == 'UserSyncMetadata':
            history_records = UserSyncMetadata.history.all()
        elif model_type == 'DataFilter':
            history_records = DataFilter.history.all()
    else:
        # Get all history records
        all_histories = []
        all_histories.extend(SyncLog.history.all())
        all_histories.extend(SyncMetadata.history.all())
        all_histories.extend(PerformanceMetrics.history.all())
        all_histories.extend(Organization.history.all())
        all_histories.extend(UserOrganization.history.all())
        all_histories.extend(ModelPermission.history.all())
        all_histories.extend(UserSyncMetadata.history.all())
        all_histories.extend(DataFilter.history.all())
        history_records = sorted(all_histories, key=lambda x: x.history_date, reverse=True)
    
    # Apply additional filters
    if user_filter:
        history_records = [r for r in history_records if hasattr(r, 'history_user') and r.history_user and user_filter.lower() in r.history_user.username.lower()]
    
    if date_from:
        from datetime import datetime
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            history_records = [r for r in history_records if r.history_date >= date_from_obj]
        except ValueError:
            pass
    
    if date_to:
        from datetime import datetime
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            history_records = [r for r in history_records if r.history_date <= date_to_obj]
        except ValueError:
            pass
    
    # Limit to last 100 records
    history_records = history_records[:100]
    
    context = {
        'history_records': history_records,
        'model_choices': model_choices,
        'model_type': model_type,
        'user_filter': user_filter,
        'date_from': date_from,
        'date_to': date_to,
        'total_records': len(history_records),
    }
    
    return render(request, 'sb_sync/audit_trails.html', context)
