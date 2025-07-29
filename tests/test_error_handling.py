from django.test import TestCase
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
import time

from sb_sync.error_handling import (
    SyncError, ValidationError, AuthenticationError, DatabaseError,
    ConfigurationError, NetworkError, TimeoutError, RateLimitError,
    SecurityError, PerformanceError,
    ErrorCategory, ErrorSeverity,
    ErrorHandler, RetryHandler, PartialSuccessHandler,
    ErrorRecoveryHandler, ErrorReportingHandler,
    error_handler, retry_handler, partial_success_handler,
    recovery_handler, reporting_handler
)


class ErrorHandlingTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        
        # Get authentication token
        auth_response = self.client.post('/api/sync/auth/token/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.token = auth_response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_validation_error(self):
        """Test validation error handling"""
        error = ValidationError(
            "Invalid data format",
            field="email",
            context={'data': {'email': 'invalid'}}
        )
        
        self.assertEqual(error.category, ErrorCategory.VALIDATION)
        self.assertEqual(error.severity, ErrorSeverity.MEDIUM)
        self.assertFalse(error.retryable)
        self.assertIn('email', error.context['data'])

    def test_database_error(self):
        """Test database error handling"""
        error = DatabaseError(
            "Connection failed",
            context={'operation': 'insert'}
        )
        
        self.assertEqual(error.category, ErrorCategory.DATABASE)
        self.assertEqual(error.severity, ErrorSeverity.HIGH)
        self.assertTrue(error.retryable)

    def test_authentication_error(self):
        """Test authentication error handling"""
        error = AuthenticationError(
            "Invalid token",
            context={'user_id': 123}
        )
        
        self.assertEqual(error.category, ErrorCategory.AUTHENTICATION)
        self.assertEqual(error.severity, ErrorSeverity.HIGH)
        self.assertFalse(error.retryable)

    def test_security_error(self):
        """Test security error handling"""
        error = SecurityError(
            "SQL injection detected",
            context={'input': "'; DROP TABLE users; --"}
        )
        
        self.assertEqual(error.category, ErrorCategory.SECURITY)
        self.assertEqual(error.severity, ErrorSeverity.CRITICAL)
        self.assertFalse(error.retryable)

    def test_error_handler_status_codes(self):
        """Test error handler returns correct HTTP status codes"""
        handler = ErrorHandler()
        
        # Test validation error
        error = ValidationError("Invalid data")
        response, status_code = handler.handle_error(error)
        self.assertEqual(status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test authentication error
        error = AuthenticationError("Invalid credentials")
        response, status_code = handler.handle_error(error)
        self.assertEqual(status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test database error
        error = DatabaseError("Connection failed")
        response, status_code = handler.handle_error(error)
        self.assertEqual(status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Test rate limit error
        error = RateLimitError("Too many requests")
        response, status_code = handler.handle_error(error)
        self.assertEqual(status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_retry_handler_success(self):
        """Test retry handler with successful operation"""
        handler = RetryHandler(max_retries=2, base_delay=0.1)
        
        def successful_operation():
            return "success"
        
        result = handler.retry(successful_operation)
        self.assertEqual(result, "success")

    def test_retry_handler_retryable_error(self):
        """Test retry handler with retryable error"""
        handler = RetryHandler(max_retries=2, base_delay=0.1)
        
        call_count = 0
        def failing_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise DatabaseError("Temporary failure")
            return "success"
        
        result = handler.retry(failing_operation)
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)

    def test_retry_handler_non_retryable_error(self):
        """Test retry handler with non-retryable error"""
        handler = RetryHandler(max_retries=2, base_delay=0.1)
        
        def failing_operation():
            raise ValidationError("Invalid data")
        
        with self.assertRaises(ValidationError):
            handler.retry(failing_operation)

    def test_retry_handler_max_retries_exceeded(self):
        """Test retry handler when max retries exceeded"""
        handler = RetryHandler(max_retries=2, base_delay=0.1)
        
        def always_failing_operation():
            raise DatabaseError("Persistent failure")
        
        with self.assertRaises(DatabaseError):
            handler.retry(always_failing_operation)

    def test_partial_success_handler_complete_success(self):
        """Test partial success handler with complete success"""
        handler = PartialSuccessHandler()
        
        results = {
            'success_count': 10,
            'error_count': 0,
            'errors': []
        }
        
        response = handler.handle_partial_success(results, 10)
        
        self.assertEqual(response['status'], 'success')
        self.assertEqual(response['success_count'], 10)
        self.assertEqual(response['error_count'], 0)

    def test_partial_success_handler_partial_success(self):
        """Test partial success handler with partial success"""
        handler = PartialSuccessHandler()
        
        results = {
            'success_count': 7,
            'error_count': 3,
            'errors': ['Error 1', 'Error 2', 'Error 3']
        }
        
        response = handler.handle_partial_success(results, 10)
        
        self.assertEqual(response['status'], 'partial_success')
        self.assertEqual(response['success_count'], 7)
        self.assertEqual(response['error_count'], 3)
        self.assertEqual(response['success_rate'], 0.7)

    def test_partial_success_handler_complete_failure(self):
        """Test partial success handler with complete failure"""
        handler = PartialSuccessHandler()
        
        results = {
            'success_count': 0,
            'error_count': 10,
            'errors': ['Error 1', 'Error 2', 'Error 3']
        }
        
        response = handler.handle_partial_success(results, 10)
        
        self.assertEqual(response['status'], 'error')
        self.assertEqual(response['success_count'], 0)
        self.assertEqual(response['error_count'], 10)

    def test_error_recovery_handler_database_recovery(self):
        """Test error recovery handler for database errors"""
        handler = ErrorRecoveryHandler()
        
        error = DatabaseError("Connection lost")
        
        # Mock database connection
        with patch('django.db.connection') as mock_connection:
            mock_connection.close.return_value = None
            mock_connection.ensure_connection.return_value = None
            
            result = handler.recover_from_error(error)
            self.assertTrue(result)

    def test_error_recovery_handler_network_recovery(self):
        """Test error recovery handler for network errors"""
        handler = ErrorRecoveryHandler()
        
        error = NetworkError("Connection timeout")
        
        with patch('time.sleep') as mock_sleep:
            result = handler.recover_from_error(error)
            self.assertTrue(result)
            mock_sleep.assert_called_once_with(5)

    def test_error_recovery_handler_configuration_recovery(self):
        """Test error recovery handler for configuration errors"""
        handler = ErrorRecoveryHandler()
        
        error = ConfigurationError("Invalid setting")
        
        with patch('django.conf.settings._setup') as mock_setup:
            result = handler.recover_from_error(error)
            self.assertTrue(result)
            mock_setup.assert_called_once()

    def test_error_reporting_handler(self):
        """Test error reporting handler"""
        handler = ErrorReportingHandler()
        
        error = SecurityError("SQL injection detected")
        
        with patch.object(handler.logger, 'error') as mock_log:
            handler.report_error(error)
            mock_log.assert_called_once()

    def test_error_reporting_handler_with_alert(self):
        """Test error reporting handler with alert enabled"""
        handler = ErrorReportingHandler()
        handler.enable_alerts = True
        handler.alert_webhook = "http://example.com/webhook"
        
        error = SecurityError("Critical security breach")
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            handler.report_error(error)
            mock_post.assert_called_once()

    def test_push_api_with_validation_error(self):
        """Test PUSH API with validation error"""
        url = '/api/sync/push/'
        data = {
            'data': [
                {
                    'id': 1,
                    'username': 'testuser'
                    # Missing _model field
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_push_api_with_database_error(self):
        """Test PUSH API with database error"""
        url = '/api/sync/push/'
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
        
        # Should return 200 with partial success
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)

    def test_pull_api_with_invalid_model(self):
        """Test PULL API with invalid model"""
        url = '/api/sync/pull/'
        data = {
            'models': {
                'invalid.Model': None
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('metadata', response.data)
        self.assertIn('invalid.Model', response.data['metadata'])

    def test_auth_api_with_missing_credentials(self):
        """Test auth API with missing credentials"""
        url = '/api/sync/auth/token/'
        data = {}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_auth_api_with_invalid_credentials(self):
        """Test auth API with invalid credentials"""
        url = '/api/sync/auth/token/'
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_error_decorators(self):
        """Test error handling decorators"""
        from sb_sync.error_handling import handle_errors, retry_on_error, with_recovery
        
        @handle_errors
        def function_with_error():
            raise ValidationError("Test error")
        
        response = function_with_error()
        self.assertIn('error', response.data)

        @retry_on_error
        def function_with_retry():
            raise DatabaseError("Retryable error")
        
        with self.assertRaises(DatabaseError):
            function_with_retry()

        @with_recovery
        def function_with_recovery():
            raise DatabaseError("Recoverable error")
        
        with self.assertRaises(DatabaseError):
            function_with_recovery()

    def test_error_context_preservation(self):
        """Test that error context is preserved"""
        error = ValidationError(
            "Invalid field",
            field="email",
            context={'user_id': 123, 'operation': 'create'}
        )
        
        self.assertEqual(error.field, "email")
        self.assertEqual(error.context['user_id'], 123)
        self.assertEqual(error.context['operation'], 'create')

    def test_error_severity_levels(self):
        """Test error severity levels"""
        # Critical error
        critical_error = SecurityError("Critical breach")
        self.assertEqual(critical_error.severity, ErrorSeverity.CRITICAL)
        
        # High error
        high_error = AuthenticationError("Invalid token")
        self.assertEqual(high_error.severity, ErrorSeverity.HIGH)
        
        # Medium error
        medium_error = ValidationError("Invalid data")
        self.assertEqual(medium_error.severity, ErrorSeverity.MEDIUM)
        
        # Low error (default)
        low_error = SyncError("Minor issue")
        self.assertEqual(low_error.severity, ErrorSeverity.MEDIUM)  # Default

    def test_error_retryable_flags(self):
        """Test error retryable flags"""
        # Retryable errors
        retryable_errors = [
            DatabaseError("Connection failed"),
            NetworkError("Timeout"),
            TimeoutError("Request timeout"),
            RateLimitError("Too many requests")
        ]
        
        for error in retryable_errors:
            self.assertTrue(error.retryable)
        
        # Non-retryable errors
        non_retryable_errors = [
            ValidationError("Invalid data"),
            AuthenticationError("Invalid credentials"),
            SecurityError("Security breach"),
            ConfigurationError("Invalid config")
        ]
        
        for error in non_retryable_errors:
            self.assertFalse(error.retryable) 