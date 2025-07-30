from django.urls import path
from .views import (
    PushAPIView, PullAPIView, AuthTokenView, PerformanceView,
    config_dashboard, permission_matrix, update_permission, bulk_update_permissions,
    model_discovery_config, sync_logs, performance_metrics, audit_trails
)

app_name = 'sb_sync'

urlpatterns = [
    # API Endpoints
    path('push/', PushAPIView.as_view(), name='sync_push'),
    path('pull/', PullAPIView.as_view(), name='sync_pull'),
    path('auth/token/', AuthTokenView.as_view(), name='sync_auth_token'),
    path('performance/', PerformanceView.as_view(), name='sync_performance'),
    
    # Web Configuration Interface
    path('config/', config_dashboard, name='config_dashboard'),
    path('config/permissions/', permission_matrix, name='permission_matrix'),
    path('config/permissions/<int:organization_id>/', permission_matrix, name='permission_matrix_org'),
    path('config/permissions/update/', update_permission, name='update_permission'),
    path('config/permissions/bulk-update/', bulk_update_permissions, name='bulk_update_permissions'),
    path('config/model-discovery/', model_discovery_config, name='model_discovery_config'),
    path('config/logs/', sync_logs, name='sync_logs'),
    path('config/metrics/', performance_metrics, name='performance_metrics'),
    path('config/audit-trails/', audit_trails, name='audit_trails'),
]