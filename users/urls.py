# users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, NotificationStatusViewSet, HealthCheckView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'status', NotificationStatusViewSet, basename='notification-status')

urlpatterns = [
    path('api/v1/', include(router.urls)),
    
    # Specific endpoint for notification status with type
    path('api/v1/<str:notification_preference>/status/', 
         NotificationStatusViewSet.as_view({'post': 'create'}), 
         name='notification-status-create'),
    
    # Health check
    path('health/', HealthCheckView.as_view(), name='health-check'),
]