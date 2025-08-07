from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from simple_history.admin import SimpleHistoryAdmin
from .models import UserSite, ModelPermission, UserSyncMetadata, DataFilter, SyncConfiguration

# Site admin removed - using Django Sites instead

@admin.register(UserSite)
class UserSiteAdmin(admin.ModelAdmin):
    list_display = ('user', 'site', 'group', 'is_active', 'created_at')
    list_filter = ('site', 'group', 'is_active', 'created_at')
    search_fields = ('user__username', 'user__email', 'site__name', 'group__name')
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'site', 'group')

@admin.register(ModelPermission)
class ModelPermissionAdmin(admin.ModelAdmin):
    list_display = ('site', 'group', 'model_name', 'can_push', 'can_pull', 'created_at')
    list_filter = ('site', 'group', 'can_push', 'can_pull', 'created_at')
    search_fields = ('model_name', 'site__name', 'group__name')
    ordering = ('site__name', 'group__name', 'model_name')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('site', 'group')

@admin.register(UserSyncMetadata)
class UserSyncMetadataAdmin(admin.ModelAdmin):
    list_display = ('user', 'site', 'model_name', 'last_sync', 'total_synced', 'created_at')
    list_filter = ('site', 'model_name', 'last_sync', 'created_at')
    search_fields = ('user__username', 'model_name', 'site__name')
    ordering = ('-last_sync',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'site')

@admin.register(DataFilter)
class DataFilterAdmin(admin.ModelAdmin):
    list_display = ('filter_name', 'site', 'group', 'model_name', 'is_active', 'created_at')
    list_filter = ('site', 'group', 'model_name', 'is_active', 'created_at')
    search_fields = ('filter_name', 'model_name', 'site__name', 'group__name')
    ordering = ('site__name', 'model_name', 'filter_name')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('site', 'group')

@admin.register(SyncConfiguration)
class SyncConfigurationAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'description', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('key', 'value', 'description')
    ordering = ('key',)
    readonly_fields = ('created_at', 'updated_at')

# Customize the admin site
admin.site.site_header = "SB Sync Administration"
admin.site.site_title = "SB Sync Admin"
admin.site.index_title = "Welcome to SB Sync Administration"

# Add custom admin actions
@admin.action(description="Activate selected organizations")
def activate_organizations(modeladmin, request, queryset):
    queryset.update(is_active=True)
activate_organizations.short_description = "Activate selected organizations"

@admin.action(description="Deactivate selected organizations")
def deactivate_organizations(modeladmin, request, queryset):
    queryset.update(is_active=False)
deactivate_organizations.short_description = "Deactivate selected organizations"

# Register custom actions for Site model
SiteAdmin = admin.site._registry[Site]
SiteAdmin.actions = list(SiteAdmin.actions) + [activate_organizations, deactivate_organizations]
