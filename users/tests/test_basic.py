# users/tests/test_basic.py
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import User, UserPreference

class BasicTests(APITestCase):
    def test_health_endpoint(self):
        """Test health endpoint works"""
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')

    def test_user_creation(self):
        """Test user creation via API"""
        data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpass123",
            "preferences": {
                "email": True,
                "push": True
            }
        }
        
        response = self.client.post('/api/v1/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # Verify user was created in database
        user = User.objects.get(email="test@example.com")
        self.assertEqual(user.name, "Test User")
        
        # Verify preferences were created
        self.assertTrue(user.preference.email)
        self.assertTrue(user.preference.push)

    def test_user_login(self):
        """Test user login"""
        # First create a user
        user = User.objects.create_user(
            email="login@example.com",
            password="testpass123",
            name="Login User"
        )
        UserPreference.objects.create(user=user)
        
        # Test login
        data = {
            "email": "login@example.com",
            "password": "testpass123"
        }
        
        response = self.client.post('/api/v1/users/login/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data['data'])