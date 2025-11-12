# users/services.py
import json
from django.core.cache import cache
from .models import User

class UserCacheService:
    @staticmethod
    def get_user(user_id):
        cache_key = f"user:{user_id}"
        cached_user = cache.get(cache_key)
        
        if cached_user:
            return json.loads(cached_user)
        
        try:
            user = User.objects.select_related('preference').get(id=user_id)
            user_data = {
                'id': str(user.id),
                'email': user.email,
                'name': user.name,
                'push_token': user.push_token,
                'preferences': {
                    'email': user.preference.email,
                    'push': user.preference.push
                }
            }
            
            cache.set(cache_key, json.dumps(user_data), 300)
            return user_data
        except User.DoesNotExist:
            return None
    
    @staticmethod
    def invalidate_user(user_id):
        cache_key = f"user:{user_id}"
        cache.delete(cache_key)
    
    @staticmethod
    def get_user_preferences(user_id):
        cache_key = f"user_preferences:{user_id}"
        cached_prefs = cache.get(cache_key)
        
        if cached_prefs:
            return json.loads(cached_prefs)
        
        try:
            user = User.objects.select_related('preference').get(id=user_id)
            preferences = {
                'email': user.preference.email,
                'push': user.preference.push
            }
            
            cache.set(cache_key, json.dumps(preferences), 600)
            return preferences
        except User.DoesNotExist:
            return None