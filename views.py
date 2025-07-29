import json
import logging
from django.apps import apps
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .authentication import JWTAuthentication
from .serializers import PushDataSerializer, PullRequestSerializer
from .models import SyncLog, SyncMetadata, Organization, UserOrganization, UserSyncMetadata
from .permissions import MultiTenantPermission, SyncPermission, MultiTenantMixin
from .utils import DataProcessor
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
        models_config = validated_data['models']
        batch_size = validated_data.get('batch_size', 
            getattr(settings, 'SB_SYNC_BATCH_SIZE', 100))
        
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
            # Get user's organizations and roles
            user_organizations = UserOrganization.objects.filter(
                user=user,
                is_active=True
            ).select_related('organization')
            
            organizations_data = []
            for user_org in user_organizations:
                organizations_data.append({
                    'id': user_org.organization.id,
                    'name': user_org.organization.name,
                    'slug': user_org.organization.slug,
                    'role': user_org.role
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
