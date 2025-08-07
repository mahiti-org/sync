"""
Multi-tenant and Group-based Access Control for sb-sync
"""
from django.core.cache import cache
from django.db.models import Q
from django.apps import apps
from django.contrib.auth.models import Group
from rest_framework import permissions
from .models import (
    Organization, UserOrganization, ModelPermission, 
    UserSyncMetadata, DataFilter
)
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class MultiTenantPermission(permissions.BasePermission):
    """
    Custom permission class for multi-tenant access control
    """
    
    def has_permission(self, request, view):
        """Check if user has permission to access the view"""
        if not request.user.is_authenticated:
            return False
        
        # Get user's organizations and groups
        user_orgs = self._get_user_organizations(request.user)
        if not user_orgs:
            return False
        
        # Store user context for use in has_object_permission
        request.user_organizations = user_orgs
        return True
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access specific objects"""
        user_orgs = getattr(request, 'user_organizations', [])
        
        # Check if object belongs to user's organization
        if hasattr(obj, 'organization'):
            return obj.organization in [uo.organization for uo in user_orgs]
        
        return True
    
    def _get_user_organizations(self, user):
        """Get user's organizations with groups"""
        cache_key = f"user_organizations_{user.id}"
        user_orgs = cache.get(cache_key)
        
        if user_orgs is None:
            user_orgs = list(UserOrganization.objects.filter(
                user=user, 
                is_active=True
            ).select_related('organization', 'group'))
            cache.set(cache_key, user_orgs, timeout=300)  # Cache for 5 minutes
        
        return user_orgs


class SyncPermission:
    """
    Utility class for checking sync permissions using Django Groups
    """
    
    @staticmethod
    def can_access_model(user, organization, model_name, operation='read'):
        """Check if user can access a specific model based on their groups"""
        cache_key = f"model_permission_{user.id}_{organization.id}_{model_name}_{operation}"
        has_permission = cache.get(cache_key)
        
        if has_permission is None:
            try:
                # Superusers have all permissions
                if user.is_superuser:
                    has_permission = True
                    cache.set(cache_key, has_permission, timeout=300)
                    logger.debug(f"Superuser {user.username} granted {operation} permission for {model_name}")
                    return has_permission
                
                # Get user's groups in this organization
                user_groups = SyncPermission.get_user_groups(user, organization)
                logger.debug(f"User {user.username} groups for {organization.name}: {[g.name for g in user_groups]}")
                
                # Check if any of user's groups have permission
                has_permission = False
                for group in user_groups:
                    permission = ModelPermission.objects.filter(
                        organization=organization,
                        group=group,
                        model_name=model_name
                    ).first()
                    
                    if permission:
                        logger.debug(f"Found permission for group {group.name}: push={permission.can_push}, pull={permission.can_pull}")
                        if operation == 'push':
                            has_permission = permission.can_push
                        elif operation == 'pull':
                            has_permission = permission.can_pull
                        else:
                            # Default to pull for any other operation
                            has_permission = permission.can_pull
                        
                        if has_permission:
                            logger.debug(f"User {user.username} granted {operation} permission for {model_name} via group {group.name}")
                            break
                    else:
                        logger.debug(f"No permission found for group {group.name} on model {model_name}")
                
                if not has_permission:
                    logger.warning(f"User {user.username} denied {operation} permission for {model_name} in {organization.name}")
                
                cache.set(cache_key, has_permission, timeout=300)
                
            except Exception as e:
                logger.error(f"Error checking permission for {user.username} on {model_name}: {str(e)}")
                has_permission = False
                cache.set(cache_key, has_permission, timeout=300)
        
        return has_permission
    
    @staticmethod
    def get_user_groups(user, organization):
        """Get user's groups for a specific organization"""
        cache_key = f"user_groups_{user.id}_{organization.id}"
        groups = cache.get(cache_key)
        
        if groups is None:
            # Superusers have access to all groups
            if user.is_superuser:
                groups = list(Group.objects.all())
            else:
                user_org = UserOrganization.objects.filter(
                    user=user,
                    organization=organization,
                    is_active=True
                ).first()
                
                groups = [user_org.group] if user_org else []
            
            cache.set(cache_key, groups, timeout=300)
        
        return groups
    
    @staticmethod
    def get_data_filters(user, organization, model_name):
        """Get data filters for user's groups and model"""
        cache_key = f"data_filters_{user.id}_{organization.id}_{model_name}"
        filters = cache.get(cache_key)
        
        if filters is None:
            user_groups = SyncPermission.get_user_groups(user, organization)
            
            filters = []
            for group in user_groups:
                model_filters = DataFilter.objects.filter(
                    organization=organization,
                    group=group,
                    model_name=model_name,
                    is_active=True
                )
                filters.extend(model_filters)
            
            cache.set(cache_key, filters, timeout=300)
        
        return filters
    
    @staticmethod
    def apply_filters_to_queryset(queryset, filters):
        """Apply data filters to a queryset"""
        for filter_obj in filters:
            condition = filter_obj.filter_condition
            
            field = condition.get('field')
            operator = condition.get('operator')
            value = condition.get('value')
            
            if field and operator and value is not None:
                if operator == 'in':
                    queryset = queryset.filter(**{f"{field}__in": value})
                elif operator == 'exact':
                    queryset = queryset.filter(**{field: value})
                elif operator == 'contains':
                    queryset = queryset.filter(**{f"{field}__contains": value})
                elif operator == 'gte':
                    queryset = queryset.filter(**{f"{field}__gte": value})
                elif operator == 'lte':
                    queryset = queryset.filter(**{f"{field}__lte": value})
                elif operator == 'startswith':
                    queryset = queryset.filter(**{f"{field}__startswith": value})
                elif operator == 'endswith':
                    queryset = queryset.filter(**{f"{field}__endswith": value})
        
        return queryset
    
    @staticmethod
    def get_user_sync_metadata(user, organization, model_name):
        """Get or create user sync metadata"""
        metadata, created = UserSyncMetadata.objects.get_or_create(
            user=user,
            organization=organization,
            model_name=model_name,
            defaults={'total_synced': 0}
        )
        return metadata
    
    @staticmethod
    def update_user_sync_metadata(user, organization, model_name, count):
        """Update user sync metadata"""
        metadata = SyncPermission.get_user_sync_metadata(user, organization, model_name)
        metadata.total_synced += count
        metadata.last_sync = timezone.now()
        metadata.save()
        
        # Invalidate cache
        cache_key = f"user_sync_metadata_{user.id}_{organization.id}_{model_name}"
        cache.delete(cache_key)


class OrganizationContextMiddleware:
    """
    Middleware to add organization context to requests
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            # Get user's primary organization (you can modify this logic)
            user_org = UserOrganization.objects.filter(
                user=request.user,
                is_active=True
            ).first()
            
            if user_org:
                request.organization = user_org.organization
                request.user_group = user_org.group
            else:
                request.organization = None
                request.user_group = None
        
        response = self.get_response(request)
        return response


# Example usage in views
class MultiTenantMixin:
    """
    Mixin to add multi-tenant functionality to views
    """
    
    def get_user_organizations(self, user):
        """Get user's organizations"""
        return UserOrganization.objects.filter(
            user=user,
            is_active=True
        ).select_related('organization', 'group')
    
    def check_model_permission(self, user, organization, model_name, operation='read'):
        """Check if user has permission for a model based on their groups"""
        return SyncPermission.can_access_model(user, organization, model_name, operation)
    
    def get_filtered_queryset(self, user, organization, model_name, base_queryset):
        """Get filtered queryset based on user permissions"""
        # Apply data filters
        filters = SyncPermission.get_data_filters(user, organization, model_name)
        return SyncPermission.apply_filters_to_queryset(base_queryset, filters)
    
    def validate_user_access(self, user, organization, model_name, operation='read'):
        """Validate user access to a model"""
        if not self.check_model_permission(user, organization, model_name, operation):
            raise PermissionError(
                f"User {user.username} does not have {operation} permission for {model_name} in {organization.name}"
            ) 