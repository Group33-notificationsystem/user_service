
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.utils import timezone
from django.core.cache import cache

from .models import User, UserPreference, NotificationStatusLog
from .serializers import (
    UserCreateSerializer, UserUpdateSerializer, UserResponseSerializer,
    NotificationStatusSerializer, UserLoginSerializer
)
from .authentication import generate_jwt_token
from .services import UserCacheService

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_active=True).select_related('preference')
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserResponseSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def create(self, request):
        """
        POST /api/v1/users/
        {
          "name": "str",
          "email": "email@example.com", 
          "push_token": "optional_str",
          "preferences": {
            "email": true,
            "push": true
          },
          "password": "str"
        }
        """
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT token for immediate login
            token = generate_jwt_token(user)
            
            # Invalidate cache
            UserCacheService.invalidate_user(user.id)
            
            return Response({
                "success": True,
                "message": "User created successfully",
                "data": {
                    "user": UserResponseSerializer(user).data,
                    "token": token
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            "success": False,
            "error": "validation_failed",
            "message": "Please check your input",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def list(self, request):
        """Get all users (for internal use)"""
        users = self.get_queryset()
        serializer = UserResponseSerializer(users, many=True)
        
        return Response({
            "success": True,
            "message": "Users retrieved successfully",
            "data": serializer.data
        })
    
    def retrieve(self, request, pk=None):
        """Get specific user"""
        try:
            user = self.get_queryset().get(id=pk)
            serializer = UserResponseSerializer(user)
            
            return Response({
                "success": True,
                "message": "User retrieved successfully",
                "data": serializer.data
            })
        except User.DoesNotExist:
            return Response({
                "success": False,
                "error": "user_not_found",
                "message": "User not found",
                "data": {}
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """User login"""
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token = generate_jwt_token(user)
            
            user.save()  # Update last login
            UserCacheService.invalidate_user(user.id)
            
            return Response({
                "success": True,
                "message": "Login successful",
                "data": {
                    "user": UserResponseSerializer(user).data,
                    "token": token
                }
            })
        
        return Response({
            "success": False,
            "error": "authentication_failed", 
            "message": "Invalid credentials",
            "data": serializer.errors
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    @action(detail=True, methods=['patch'])
    def update_push_token(self, request, pk=None):
        """Update user's push token"""
        user = self.get_object()
        push_token = request.data.get('push_token')
        
        if not push_token:
            return Response({
                "success": False,
                "error": "missing_push_token",
                "message": "push_token is required",
                "data": {}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.push_token = push_token
        user.save()
        UserCacheService.invalidate_user(user.id)
        
        return Response({
            "success": True,
            "message": "Push token updated successfully",
            "data": UserResponseSerializer(user).data
        })

class NotificationStatusViewSet(viewsets.ModelViewSet):
    queryset = NotificationStatusLog.objects.all()
    serializer_class = NotificationStatusSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, notification_preference=None):
        """
        POST /api/v1/{notification_preference}/status/
        {
          "notification_id": "str",
          "status": "delivered|pending|failed", 
          "timestamp": "2024-01-01T10:00:00Z",  # optional
          "error": "str"  # optional, required for failed status
        }
        """
        # Validate notification_preference
        if notification_preference not in ['email', 'push']:
            return Response({
                "success": False,
                "error": "invalid_notification_type",
                "message": "Notification type must be 'email' or 'push'",
                "data": {}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate status
        status_value = request.data.get('status')
        if status_value not in ['delivered', 'pending', 'failed']:
            return Response({
                "success": False, 
                "error": "invalid_status",
                "message": "Status must be 'delivered', 'pending', or 'failed'",
                "data": {}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate error for failed status
        if status_value == 'failed' and not request.data.get('error'):
            return Response({
                "success": False,
                "error": "missing_error",
                "message": "Error field is required for failed status",
                "data": {}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Add user and notification_type from context
            notification_log = serializer.save(
                user=request.user,
                notification_type=notification_preference
            )
            
            return Response({
                "success": True,
                "message": "Notification status logged successfully",
                "data": NotificationStatusSerializer(notification_log).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            "success": False,
            "error": "validation_failed",
            "message": "Please check your input",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get notification history for current user"""
        notification_type = request.query_params.get('type')
        
        queryset = NotificationStatusLog.objects.filter(user=request.user)
        
        if notification_type in ['email', 'push']:
            queryset = queryset.filter(notification_type=notification_type)
        
        queryset = queryset.order_by('-timestamp')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            "success": True,
            "message": "Notification history retrieved successfully",
            "data": serializer.data
        })

class HealthCheckView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            User.objects.first()
            db_status = 'healthy'
        except Exception as e:
            db_status = f'unhealthy: {str(e)}'
        
        try:
            cache.set('health_check', 'ok', 1)
            redis_status = 'healthy'
        except Exception as e:
            redis_status = f'unhealthy: {str(e)}'
        
        return Response({
            "status": "healthy",
            "service": "user-service",
            "timestamp": timezone.now().isoformat(),
            "dependencies": {
                "database": db_status,
                "redis": redis_status
            }
        })
