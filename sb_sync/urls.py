from django.urls import path
from . import views

app_name = 'sb_sync'

urlpatterns = [
    # API endpoints
    path('api/push/', views.PushAPIView.as_view(), name='push_api'),
    path('api/pull/', views.PullAPIView.as_view(), name='pull_api'),
    path('api/auth/token/', views.auth_token, name='auth_token'),
    
    # Configuration dashboard
    path('config/', views.config_dashboard, name='config_dashboard'),
    path('config/performance/', views.performance_dashboard, name='performance_dashboard'),
    
    # Permission management
    path('config/permissions/<int:site_id>/', views.permission_matrix, name='permission_matrix_site'),
    path('config/permissions/save/', views.save_permission, name='save_permission'),
    path('config/permissions/bulk-save/', views.bulk_save_permissions, name='bulk_save_permissions'),
    
    # Model discovery
    path('config/model-discovery/', views.model_discovery_config, name='model_discovery_config'),
    
    # Audit and monitoring
    path('config/audit-trails/', views.audit_trails, name='audit_trails'),
]