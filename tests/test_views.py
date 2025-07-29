from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from sb_sync.models import SyncLog, SyncMetadata
import json


class AuthenticationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_auth_token_generation(self):
        """Test JWT token generation"""
        url = reverse('sb_sync:auth_token')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'testuser')

    def test_auth_invalid_credentials(self):
        """Test authentication with invalid credentials"""
        url = reverse('sb_sync:auth_token')
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_auth_missing_credentials(self):
        """Test authentication with missing credentials"""
        url = reverse('sb_sync:auth_token')
        data = {}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class PushAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Get authentication token
        auth_response = self.client.post(reverse('sb_sync:auth_token'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.token = auth_response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_push_valid_data(self):
        """Test pushing valid data"""
        url = reverse('sb_sync:push')
        data = {
            'data': [
                {
                    '_model': 'auth.User',
                    'id': self.user.id,
                    'username': 'updateduser',
                    'email': 'updated@example.com'
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertIn('processed', response.data)
        self.assertIn('errors', response.data)

    def test_push_invalid_data(self):
        """Test pushing invalid data"""
        url = reverse('sb_sync:push')
        data = {
            'data': [
                {
                    '_model': 'auth.User',
                    'id': 99999,  # Non-existent user
                    'username': 'newuser',
                    'email': 'new@example.com'
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        # Should still return 200 but with errors
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(response.data['errors'], 0)

    def test_push_missing_model_field(self):
        """Test pushing data without _model field"""
        url = reverse('sb_sync:push')
        data = {
            'data': [
                {
                    'id': 1,
                    'username': 'testuser'
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(response.data['errors'], 0)

    def test_push_unauthorized(self):
        """Test push without authentication"""
        client = APIClient()  # No authentication
        url = reverse('sb_sync:push')
        data = {'data': []}
        
        response = client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PullAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Get authentication token
        auth_response = self.client.post(reverse('sb_sync:auth_token'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.token = auth_response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_pull_valid_request(self):
        """Test pulling data with valid request"""
        url = reverse('sb_sync:pull')
        data = {
            'models': {
                'auth.User': None  # No timestamp filter
            },
            'batch_size': 10
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('metadata', response.data)
        self.assertIn('batch_info', response.data)

    def test_pull_with_timestamp_filter(self):
        """Test pulling data with timestamp filter"""
        url = reverse('sb_sync:pull')
        data = {
            'models': {
                'auth.User': '2024-01-01T00:00:00Z'
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)

    def test_pull_invalid_model(self):
        """Test pulling data with invalid model name"""
        url = reverse('sb_sync:pull')
        data = {
            'models': {
                'invalid.Model': None
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should have error in metadata for invalid model
        self.assertIn('invalid.Model', response.data['metadata'])

    def test_pull_unauthorized(self):
        """Test pull without authentication"""
        client = APIClient()  # No authentication
        url = reverse('sb_sync:pull')
        data = {'models': {}}
        
        response = client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class HealthCheckTest(TestCase):
    def test_health_check_endpoint(self):
        """Test health check endpoint"""
        client = APIClient()
        url = reverse('sb_sync:health_check')
        
        response = client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertIn('timestamp', response.data)
        self.assertIn('checks', response.data) 