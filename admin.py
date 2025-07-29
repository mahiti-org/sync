from django.contrib import admin
from .models import SyncLog, SyncMetadata

@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'operation', 'status', 'model_name', 'object_count', 'processing_time']
    list_filter = ['operation', 'status', 'timestamp', 'model_name']
    search_fields = ['user__username', 'model_name', 'error_message']
    readonly_fields = ['timestamp', 'processing_time']
    ordering = ['-timestamp']
    
    def has_add_permission(self, request):
        return False

@admin.register(SyncMetadata)
class SyncMetadataAdmin(admin.ModelAdmin):
    list_display = ['model_name', 'last_sync', 'total_synced']
    readonly_fields = ['model_name', 'last_sync', 'total_synced']
    
    def has_add_permission(self, request):
        return False
