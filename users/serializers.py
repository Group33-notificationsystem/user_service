# users/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, UserPreference, NotificationStatusLog
from .enums import NotificationStatus

class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = ['email', 'push']

class UserCreateSerializer(serializers.ModelSerializer):
    preferences = UserPreferenceSerializer()
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'push_token', 'preferences', 'password']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        preferences_data = validated_data.pop('preferences')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        # Create user preferences
        UserPreference.objects.create(user=user, **preferences_data)
        
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    preferences = UserPreferenceSerializer(required=False)
    
    class Meta:
        model = User
        fields = ['name', 'push_token', 'preferences']
    
    def update(self, instance, validated_data):
        preferences_data = validated_data.pop('preferences', None)
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update preferences if provided
        if preferences_data:
            preference_instance = instance.preference
            for attr, value in preferences_data.items():
                setattr(preference_instance, attr, value)
            preference_instance.save()
        
        return instance

class UserResponseSerializer(serializers.ModelSerializer):
    preferences = UserPreferenceSerializer(source='preference')
    
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'push_token', 'preferences', 'created_at', 'updated_at']

class NotificationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationStatusLog
        fields = ['notification_id', 'status', 'timestamp', 'error']
    
    def create(self, validated_data):
        # The user will be set in the view
        return super().create(validated_data)

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include "email" and "password"')