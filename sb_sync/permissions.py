"""
Multi-tenant and Group-based Access Control for sb-sync
"""
import json
import logging
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.db import transaction
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import BasePermission
from rest_framework import exceptions
from .models import UserSite, ModelPermission, UserSyncMetadata, DataFilter
from .authentication import JWTAuthentication
from django.utils import timezone

logger = logging.getLogger(__name__)


class MultiTenantPermission:
    """
    Custom permission class for multi-tenant access control
    """
    
    def has_permission(self, request, view):
        """Check if user has permission to access the view"""
        if not request.user.is_authenticated:
            return False
        
        # Get user's sites and groups
        user_sites = self._get_user_sites(request.user)
        if not user_sites:
            return False
        
        # Store user context for use in has_object_permission
        request.user_sites = user_sites
        return True
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access specific objects"""
        user_sites = getattr(request, 'user_sites', [])
        
        # Check if object belongs to user's site
        if hasattr(obj, 'site'):
            return obj.site in [us.site for us in user_sites]
        
        return True
    
    def _get_user_sites(self, user):
        """Get user's sites with groups"""
        cache_key = f"user_sites_{user.id}"
        user_sites = cache.get(cache_key)
        
        if user_sites is None:
            user_sites = list(UserSite.objects.filter(
                user=user, 
                is_active=True
            ).select_related('site', 'group'))
            cache.set(cache_key, user_sites, timeout=300)  # Cache for 5 minutes
        
        return user_sites


class SyncPermission:
    """Permission checking for sync operations"""
    
    @staticmethod
    def check_object_permission(request, obj):
        """Check if user has permission to access this object"""
        # Get user's sites and groups
        user_sites = getattr(request, 'user_sites', [])
        
        if not user_sites:
            user_sites = getattr(request, 'user_sites', [])
        
        # Check if object belongs to user's site
        if hasattr(obj, 'site'):
            return obj.site in [us.site for us in user_sites]
        
        return True
    
    @staticmethod
    def _get_user_sites(user):
        """Get user's sites with groups"""
        cache_key = f"user_sites_{user.id}"
        user_sites = cache.get(cache_key)
        
        if user_sites is None:
            user_sites = list(UserSite.objects.filter(
                user=user,
                is_active=True
            ).select_related('site', 'group'))
            cache.set(cache_key, user_sites, timeout=300)  # Cache for 5 minutes
        
        return user_sites
    
    @staticmethod
    def can_access_model(user, site, model_name, operation='read'):
        """Check if user can access a specific model for a specific operation"""
        cache_key = f"model_permission_{user.id}_{site.id}_{model_name}_{operation}"
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            return cached_result
        
        # Superuser has all permissions
        if user.is_superuser:
            cache.set(cache_key, True, timeout=300)
            return True
        
        # Get user's groups in this site
        user_groups = SyncPermission.get_user_groups(user, site)
        logger.debug(f"User {user.username} groups for {site.name}: {[g.name for g in user_groups]}")
        
        if not user_groups:
            cache.set(cache_key, False, timeout=300)
            return False
        
        # Check permissions for any of user's groups
        permission_exists = ModelPermission.objects.filter(
            site=site,
            group__in=user_groups,
            model_name=model_name
        ).exists()
        
        if permission_exists:
            # Check specific operation permission
            if operation == 'push':
                has_permission = ModelPermission.objects.filter(
                    site=site,
                    group__in=user_groups,
                    model_name=model_name,
                    can_push=True
                ).exists()
            elif operation == 'pull':
                has_permission = ModelPermission.objects.filter(
                    site=site,
                    group__in=user_groups,
                    model_name=model_name,
                    can_pull=True
                ).exists()
            else:
                # Default to pull permission for other operations
                has_permission = ModelPermission.objects.filter(
                    site=site,
                    group__in=user_groups,
                    model_name=model_name,
                    can_pull=True
                ).exists()
            
            cache.set(cache_key, has_permission, timeout=300)
            return has_permission
        
        logger.warning(f"User {user.username} denied {operation} permission for {model_name} in {site.name}")
        cache.set(cache_key, False, timeout=300)
        return False
    
    @staticmethod
    def get_user_groups(user, site):
        """Get user's groups for a specific site"""
        cache_key = f"user_groups_{user.id}_{site.id}"
        cached_groups = cache.get(cache_key)
        
        if cached_groups is not None:
            return cached_groups
        
        # Superuser gets all groups
        if user.is_superuser:
            groups = list(Group.objects.all())
            cache.set(cache_key, groups, timeout=300)
            return groups
        
        # Get user's site association
        user_site = UserSite.objects.filter(
            user=user,
            site=site,
            is_active=True
        ).select_related('group').first()
        
        groups = [user_site.group] if user_site else []
        cache.set(cache_key, groups, timeout=300)
        return groups
    
    @staticmethod
    def get_data_filters(user, site, model_name):
        """Get data filters for a user/site/model combination"""
        cache_key = f"data_filters_{user.id}_{site.id}_{model_name}"
        cached_filters = cache.get(cache_key)
        
        if cached_filters is not None:
            return cached_filters
        
        user_groups = SyncPermission.get_user_groups(user, site)
        
        if not user_groups:
            return []
        
        filters = DataFilter.objects.filter(
            site=site,
            group__in=user_groups,
            model_name=model_name,
            is_active=True
        )
        
        cache.set(cache_key, list(filters), timeout=300)
        return filters
    
    @staticmethod
    def get_user_sync_metadata(user, site, model_name):
        """Get user's sync metadata for a specific model"""
        metadata, created = UserSyncMetadata.objects.get_or_create(
            user=user,
            site=site,
            model_name=model_name,
            defaults={'total_synced': 0}
        )
        return metadata
    
    @staticmethod
    def update_user_sync_metadata(user, site, model_name, count):
        """Update user's sync metadata"""
        metadata = SyncPermission.get_user_sync_metadata(user, site, model_name)
        metadata.total_synced += count
        metadata.save()
        
        # Clear cache
        cache_key = f"user_sync_metadata_{user.id}_{site.id}_{model_name}"
        cache.delete(cache_key)


class SiteContextMiddleware:
    """
    Middleware to add site context to requests
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip for non-authenticated requests
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return self.get_response(request)
        
        try:
            # Get user's sites directly
            user_site = UserSite.objects.filter(
                user=request.user,
                is_active=True
            ).select_related('site', 'group').first()
            
            if user_site:
                request.site = user_site.site
                request.user_group = user_site.group
            else:
                request.site = None
                logger.warning(f"No site found for user: {request.user.username}")
            
            # Get all user sites for permission checking
            user_sites = UserSite.objects.filter(
                user=request.user,
                is_active=True
            ).select_related('site', 'group')
            
            request.user_sites = list(user_sites)
            
        except Exception as e:
            logger.warning(f"Error in SiteContextMiddleware: {str(e)}")
            request.site = None
            request.user_sites = []
        
        return self.get_response(request)
    
    def get_user_sites(self, user):
        """Get user's sites"""
        return UserSite.objects.filter(
            user=user,
            is_active=True
        ).select_related('site', 'group')
    
    def check_model_permission(self, user, site, model_name, operation='read'):
        """Check if user has permission for a model"""
        return SyncPermission.can_access_model(user, site, model_name, operation)
    
    def get_filtered_queryset(self, user, site, model_name, base_queryset):
        """Get filtered queryset based on user permissions"""
        filters = SyncPermission.get_data_filters(user, site, model_name)
        # Apply filters to queryset
        return base_queryset
    
    def validate_user_access(self, user, site, model_name, operation='read'):
        """Validate user access and raise exception if denied"""
        if not self.check_model_permission(user, site, model_name, operation):
            raise PermissionError(
                f"User {user.username} does not have {operation} permission for {model_name} in {site.name}"
            ) 