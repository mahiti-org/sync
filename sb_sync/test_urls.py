from django.contrib import admin
from django.urls import path, include
from sb_sync.views import PushAPIView, PullAPIView, HealthCheckView
from sb_sync.authentication import JWTAuthenticationView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/sync/auth/token/', JWTAuthenticationView.as_view(), name='sb_sync:auth_token'),
    path('api/sync/push/', PushAPIView.as_view(), name='sb_sync:push'),
    path('api/sync/pull/', PullAPIView.as_view(), name='sb_sync:pull'),
    path('api/sync/health/', HealthCheckView.as_view(), name='sb_sync:health'),
] 