# users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, 
    HealthCheckView,
    UserPreferencesView,
    UserContactInfoView
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('api/v1/', include(router.urls)),
    
    # User-specific endpoints (what other services need)
    path('api/v1/users/<uuid:user_id>/preferences/', 
         UserPreferencesView.as_view(), 
         name='user-preferences'),
    
    path('api/v1/users/<uuid:user_id>/contact-info/', 
         UserContactInfoView.as_view(), 
         name='user-contact-info'),
    
    path('api/v1/users/<uuid:user_id>/status/', 
         UserViewSet.as_view({'get': 'retrieve'}), 
         name='user-status'),
    
    # Health check
    path('health/', HealthCheckView.as_view(), name='health-check'),
]
