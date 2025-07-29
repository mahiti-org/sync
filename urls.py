from django.urls import path
from .views import PushAPIView, PullAPIView, AuthTokenView, PerformanceView

app_name = 'sb_sync'

urlpatterns = [
    path('push/', PushAPIView.as_view(), name='sync_push'),
    path('pull/', PullAPIView.as_view(), name='sync_pull'),
    path('auth/token/', AuthTokenView.as_view(), name='sync_auth_token'),
    path('performance/', PerformanceView.as_view(), name='sync_performance'),
]