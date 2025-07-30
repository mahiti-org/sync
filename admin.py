from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import (
    SyncLog, SyncMetadata, PerformanceMetrics, Organization, 
    UserOrganization, ModelPermission, UserSyncMetadata, DataFilter
)

@admin.register(SyncLog)
class SyncLogAdmin(SimpleHistoryAdmin):
    list_display = ['timestamp', 'user', 'operation', 'status', 'model_name', 'object_count', 'processing_time']
    list_filter = ['operation', 'status', 'timestamp', 'model_name']
    search_fields = ['user__username', 'model_name', 'error_message']
    readonly_fields = ['timestamp', 'processing_time']
    ordering = ['-timestamp']
    history_list_display = ['timestamp', 'user', 'operation', 'status', 'model_name']
    
    def has_add_permission(self, request):
        return False

@admin.register(SyncMetadata)
class SyncMetadataAdmin(SimpleHistoryAdmin):
    list_display = ['model_name', 'last_sync', 'total_synced']
    search_fields = ['model_name']
    readonly_fields = ['last_sync', 'total_synced']
    ordering = ['model_name']
    history_list_display = ['model_name', 'last_sync', 'total_synced']

@admin.register(PerformanceMetrics)
class PerformanceMetricsAdmin(SimpleHistoryAdmin):
    list_display = ['timestamp', 'operation_type', 'model_name', 'batch_size', 'processing_time', 'query_count']
    list_filter = ['operation_type', 'timestamp', 'model_name']
    search_fields = ['model_name', 'operation_type']
    readonly_fields = ['timestamp', 'processing_time', 'memory_usage', 'query_count']
    ordering = ['-timestamp']
    history_list_display = ['timestamp', 'operation_type', 'model_name', 'processing_time']

@admin.register(Organization)
class OrganizationAdmin(SimpleHistoryAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']
    history_list_display = ['name', 'slug', 'is_active']

@admin.register(UserOrganization)
class UserOrganizationAdmin(SimpleHistoryAdmin):
    list_display = ['user', 'organization', 'group', 'is_active', 'created_at']
    list_filter = ['is_active', 'organization', 'group', 'created_at']
    search_fields = ['user__username', 'organization__name', 'group__name']
    ordering = ['organization', 'user']
    history_list_display = ['user', 'organization', 'group', 'is_active']

@admin.register(ModelPermission)
class ModelPermissionAdmin(SimpleHistoryAdmin):
    list_display = ['organization', 'group', 'model_name', 'can_push', 'can_pull', 'can_create', 'can_update', 'can_delete', 'can_read']
    list_filter = ['organization', 'group', 'can_push', 'can_pull', 'can_create', 'can_update', 'can_delete', 'can_read']
    search_fields = ['organization__name', 'group__name', 'model_name']
    list_editable = ['can_push', 'can_pull', 'can_create', 'can_update', 'can_delete', 'can_read']
    ordering = ['organization', 'group', 'model_name']
    history_list_display = ['organization', 'group', 'model_name', 'can_push', 'can_pull', 'can_create', 'can_update', 'can_delete', 'can_read']

@admin.register(UserSyncMetadata)
class UserSyncMetadataAdmin(SimpleHistoryAdmin):
    list_display = ['user', 'organization', 'model_name', 'last_sync', 'total_synced']
    list_filter = ['organization', 'model_name', 'last_sync']
    search_fields = ['user__username', 'organization__name', 'model_name']
    readonly_fields = ['last_sync', 'total_synced']
    ordering = ['organization', 'user', 'model_name']
    history_list_display = ['user', 'organization', 'model_name', 'last_sync', 'total_synced']

@admin.register(DataFilter)
class DataFilterAdmin(SimpleHistoryAdmin):
    list_display = ['organization', 'group', 'model_name', 'filter_name', 'is_active', 'created_at']
    list_filter = ['organization', 'group', 'model_name', 'is_active', 'created_at']
    search_fields = ['organization__name', 'group__name', 'model_name', 'filter_name']
    readonly_fields = ['created_at']
    ordering = ['organization', 'group', 'model_name']
    history_list_display = ['organization', 'group', 'model_name', 'filter_name', 'is_active']
