# users/authentication.py
import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()

class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return None
            
        try:
            token = auth_header.split(' ')[1]
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            user_id = payload.get('user_id')
            
            if not user_id:
                raise AuthenticationFailed('Invalid token')
                
            user = User.objects.get(id=user_id, is_active=True)
            return (user, token)
            
        except (IndexError, jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            raise AuthenticationFailed('Invalid token')
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found')

def generate_jwt_token(user):
    from datetime import datetime, timedelta
    
    payload = {
        'user_id': str(user.id),
        'email': user.email,
        'exp': datetime.utcnow() + settings.JWT_EXPIRATION_DELTA
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)