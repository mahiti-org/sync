"""
Comprehensive error handling system for sb-sync package
"""
import time
import logging
import traceback
from typing import Dict, Any, List, Optional, Callable, Type
from functools import wraps
from enum import Enum
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction, DatabaseError
from rest_framework import status
from rest_framework.response import Response
from .config import SyncConfig


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


class ErrorCategory(Enum):
    """Error categories for better organization"""
    VALIDATION = 'validation'
    AUTHENTICATION = 'authentication'
    AUTHORIZATION = 'authorization'
    DATABASE = 'database'
    NETWORK = 'network'
    TIMEOUT = 'timeout'
    RATE_LIMIT = 'rate_limit'
    CONFIGURATION = 'configuration'
    SECURITY = 'security'
    PERFORMANCE = 'performance'
    UNKNOWN = 'unknown'


class SyncError(Exception):
    """Base exception for sync operations"""
    
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.UNKNOWN,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM, 
                 retryable: bool = False, context: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.retryable = retryable
        self.context = context or {}
        self.timestamp = time.time()
        self.traceback = traceback.format_exc()


class ValidationError(SyncError):
    """Validation error"""
    def __init__(self, message: str, field: str = None, **kwargs):
        super().__init__(message, ErrorCategory.VALIDATION, **kwargs)
        self.field = field


class AuthenticationError(SyncError):
    """Authentication error"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH, **kwargs)


class AuthorizationError(SyncError):
    """Authorization error"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.AUTHORIZATION, ErrorSeverity.HIGH, **kwargs)


class DatabaseError(SyncError):
    """Database error"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.DATABASE, ErrorSeverity.HIGH, retryable=True, **kwargs)


class NetworkError(SyncError):
    """Network error"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.NETWORK, ErrorSeverity.MEDIUM, retryable=True, **kwargs)


class TimeoutError(SyncError):
    """Timeout error"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.TIMEOUT, ErrorSeverity.MEDIUM, retryable=True, **kwargs)


class RateLimitError(SyncError):
    """Rate limit error"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.RATE_LIMIT, ErrorSeverity.MEDIUM, retryable=True, **kwargs)


class ConfigurationError(SyncError):
    """Configuration error"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.CONFIGURATION, ErrorSeverity.HIGH, **kwargs)


class SecurityError(SyncError):
    """Security error"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.SECURITY, ErrorSeverity.CRITICAL, **kwargs)


class PerformanceError(SyncError):
    """Performance error"""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.PERFORMANCE, ErrorSeverity.MEDIUM, **kwargs)


class ErrorHandler:
    """Comprehensive error handler"""
    
    def __init__(self):
        self.logger = logging.getLogger('sb_sync.errors')
        self.error_counts = {}
        self.retry_config = {
            'max_retries': 3,
            'base_delay': 1,
            'max_delay': 60,
            'backoff_factor': 2,
        }
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle an error and return error response"""
        if isinstance(error, SyncError):
            return self._handle_sync_error(error, context)
        else:
            return self._handle_generic_error(error, context)
    
    def _handle_sync_error(self, error: SyncError, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle sync-specific errors"""
        # Log error
        self._log_error(error, context)
        
        # Update error counts
        self._update_error_counts(error)
        
        # Determine HTTP status code
        status_code = self._get_status_code(error)
        
        # Build error response
        response = {
            'error': {
                'type': error.category.value,
                'message': error.message,
                'severity': error.severity.value,
                'retryable': error.retryable,
                'timestamp': error.timestamp,
            }
        }
        
        # Add context if available
        if error.context:
            response['error']['context'] = error.context
        
        # Add retry information if retryable
        if error.retryable:
            response['error']['retry_info'] = self._get_retry_info(error)
        
        return response, status_code
    
    def _handle_generic_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle generic exceptions"""
        # Convert to SyncError
        sync_error = SyncError(
            message=str(error),
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.HIGH,
            context=context or {}
        )
        
        return self._handle_sync_error(sync_error, context)
    
    def _log_error(self, error: SyncError, context: Dict[str, Any] = None):
        """Log error with appropriate level"""
        log_data = {
            'error_type': error.category.value,
            'severity': error.severity.value,
            'message': error.message,
            'retryable': error.retryable,
            'context': context or {},
            'traceback': error.traceback,
        }
        
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"Critical error: {log_data}")
        elif error.severity == ErrorSeverity.HIGH:
            self.logger.error(f"High severity error: {log_data}")
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"Medium severity error: {log_data}")
        else:
            self.logger.info(f"Low severity error: {log_data}")
    
    def _update_error_counts(self, error: SyncError):
        """Update error count statistics"""
        key = f"{error.category.value}_{error.severity.value}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
    
    def _get_status_code(self, error: SyncError) -> int:
        """Get appropriate HTTP status code for error"""
        status_map = {
            ErrorCategory.VALIDATION: status.HTTP_400_BAD_REQUEST,
            ErrorCategory.AUTHENTICATION: status.HTTP_401_UNAUTHORIZED,
            ErrorCategory.AUTHORIZATION: status.HTTP_403_FORBIDDEN,
            ErrorCategory.DATABASE: status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCategory.NETWORK: status.HTTP_503_SERVICE_UNAVAILABLE,
            ErrorCategory.TIMEOUT: status.HTTP_408_REQUEST_TIMEOUT,
            ErrorCategory.RATE_LIMIT: status.HTTP_429_TOO_MANY_REQUESTS,
            ErrorCategory.CONFIGURATION: status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCategory.SECURITY: status.HTTP_403_FORBIDDEN,
            ErrorCategory.PERFORMANCE: status.HTTP_503_SERVICE_UNAVAILABLE,
            ErrorCategory.UNKNOWN: status.HTTP_500_INTERNAL_SERVER_ERROR,
        }
        
        return status_map.get(error.category, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_retry_info(self, error: SyncError) -> Dict[str, Any]:
        """Get retry information for retryable errors"""
        return {
            'max_retries': self.retry_config['max_retries'],
            'base_delay': self.retry_config['base_delay'],
            'max_delay': self.retry_config['max_delay'],
            'backoff_factor': self.retry_config['backoff_factor'],
        }


class RetryHandler:
    """Retry mechanism with exponential backoff"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, 
                 max_delay: float = 60.0, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.logger = logging.getLogger('sb_sync.retry')
    
    def retry(self, func: Callable, *args, **kwargs) -> Any:
        """Retry a function with exponential backoff"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                # Check if error is retryable
                if not self._is_retryable(e):
                    raise e
                
                # If this is the last attempt, raise the exception
                if attempt == self.max_retries:
                    break
                
                # Calculate delay
                delay = min(
                    self.base_delay * (self.backoff_factor ** attempt),
                    self.max_delay
                )
                
                self.logger.warning(
                    f"Attempt {attempt + 1} failed: {str(e)}. "
                    f"Retrying in {delay} seconds..."
                )
                
                time.sleep(delay)
        
        # If we get here, all retries failed
        raise last_exception
    
    def _is_retryable(self, error: Exception) -> bool:
        """Check if error is retryable"""
        if isinstance(error, SyncError):
            return error.retryable
        
        # Check for specific retryable exceptions
        retryable_exceptions = (
            DatabaseError,
            NetworkError,
            TimeoutError,
            RateLimitError,
        )
        
        return isinstance(error, retryable_exceptions)


class PartialSuccessHandler:
    """Handle partial success scenarios"""
    
    def __init__(self):
        self.logger = logging.getLogger('sb_sync.partial_success')
    
    def handle_partial_success(self, results: Dict[str, Any], 
                              total_items: int) -> Dict[str, Any]:
        """Handle partial success and return appropriate response"""
        success_count = results.get('success_count', 0)
        error_count = results.get('error_count', 0)
        
        if success_count == 0 and error_count > 0:
            # Complete failure
            return {
                'status': 'error',
                'message': 'All operations failed',
                'success_count': 0,
                'error_count': error_count,
                'errors': results.get('errors', []),
            }
        elif success_count > 0 and error_count > 0:
            # Partial success
            return {
                'status': 'partial_success',
                'message': f'Completed {success_count} operations, {error_count} failed',
                'success_count': success_count,
                'error_count': error_count,
                'errors': results.get('errors', []),
                'success_rate': success_count / total_items,
            }
        else:
            # Complete success
            return {
                'status': 'success',
                'message': 'All operations completed successfully',
                'success_count': success_count,
                'error_count': 0,
            }


class ErrorRecoveryHandler:
    """Handle error recovery procedures"""
    
    def __init__(self):
        self.logger = logging.getLogger('sb_sync.recovery')
    
    def recover_from_error(self, error: SyncError, context: Dict[str, Any] = None) -> bool:
        """Attempt to recover from an error"""
        try:
            if error.category == ErrorCategory.DATABASE:
                return self._recover_database_error(error, context)
            elif error.category == ErrorCategory.NETWORK:
                return self._recover_network_error(error, context)
            elif error.category == ErrorCategory.CONFIGURATION:
                return self._recover_configuration_error(error, context)
            else:
                return False
        except Exception as e:
            self.logger.error(f"Recovery failed: {str(e)}")
            return False
    
    def _recover_database_error(self, error: SyncError, context: Dict[str, Any] = None) -> bool:
        """Recover from database errors"""
        try:
            # Try to reconnect to database
            from django.db import connection
            connection.close()
            connection.ensure_connection()
            return True
        except Exception as e:
            self.logger.error(f"Database recovery failed: {str(e)}")
            return False
    
    def _recover_network_error(self, error: SyncError, context: Dict[str, Any] = None) -> bool:
        """Recover from network errors"""
        try:
            # Wait and retry
            time.sleep(5)
            return True
        except Exception as e:
            self.logger.error(f"Network recovery failed: {str(e)}")
            return False
    
    def _recover_configuration_error(self, error: SyncError, context: Dict[str, Any] = None) -> bool:
        """Recover from configuration errors"""
        try:
            # Reload configuration
            from django.conf import settings
            settings._setup()
            return True
        except Exception as e:
            self.logger.error(f"Configuration recovery failed: {str(e)}")
            return False


class ErrorReportingHandler:
    """Handle error reporting and notifications"""
    
    def __init__(self):
        self.logger = logging.getLogger('sb_sync.reporting')
        self.enable_alerts = False
        self.alert_webhook = None
    
    def report_error(self, error: SyncError, context: Dict[str, Any] = None):
        """Report error through configured channels"""
        # Log error
        self._log_error_report(error, context)
        
        # Send alert if enabled and error is critical/high
        if self.enable_alerts and error.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            self._send_alert(error, context)
    
    def _log_error_report(self, error: SyncError, context: Dict[str, Any] = None):
        """Log detailed error report"""
        report = {
            'error_id': f"{error.category.value}_{int(error.timestamp)}",
            'error_type': error.category.value,
            'severity': error.severity.value,
            'message': error.message,
            'timestamp': error.timestamp,
            'context': context or {},
            'traceback': error.traceback,
        }
        
        self.logger.error(f"Error report: {report}")
    
    def _send_alert(self, error: SyncError, context: Dict[str, Any] = None):
        """Send alert notification"""
        if not self.alert_webhook:
            return
        
        try:
            import requests
            
            alert_data = {
                'error_type': error.category.value,
                'severity': error.severity.value,
                'message': error.message,
                'timestamp': error.timestamp,
                'context': context or {},
            }
            
            response = requests.post(self.alert_webhook, json=alert_data, timeout=10)
            response.raise_for_status()
            
            self.logger.info(f"Alert sent successfully: {alert_data}")
        except Exception as e:
            self.logger.error(f"Failed to send alert: {str(e)}")


# Global error handlers
error_handler = ErrorHandler()
retry_handler = RetryHandler()
partial_success_handler = PartialSuccessHandler()
recovery_handler = ErrorRecoveryHandler()
reporting_handler = ErrorReportingHandler()


def handle_errors(func: Callable) -> Callable:
    """Decorator to handle errors in functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Convert to SyncError if not already
            if not isinstance(e, SyncError):
                e = SyncError(str(e), context={'function': func.__name__})
            
            # Handle error
            error_response, status_code = error_handler.handle_error(e)
            
            # Report error
            reporting_handler.report_error(e)
            
            # Return error response
            return Response(error_response, status=status_code)
    
    return wrapper


def retry_on_error(func: Callable) -> Callable:
    """Decorator to retry functions on error"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return retry_handler.retry(func, *args, **kwargs)
    
    return wrapper


def with_recovery(func: Callable) -> Callable:
    """Decorator to attempt recovery on error"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SyncError as e:
            # Attempt recovery
            if recovery_handler.recover_from_error(e):
                # Retry once after recovery
                return func(*args, **kwargs)
            else:
                raise e
    
    return wrapper 