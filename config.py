"""
Configuration settings for sb-sync package
"""
from django.conf import settings
from typing import Dict, Any, List, Optional
import os
import json
from pathlib import Path


class SbSyncConfig:
    """Configuration manager for sb-sync package with simplified structure"""
    
    # Core settings with sensible defaults
    CORE_DEFAULTS = {
        # Basic configuration
        'SB_SYNC_BATCH_SIZE': 100,
        'SB_SYNC_MAX_BATCH_SIZE': 1000,
        'SB_SYNC_LOG_DIR': 'logs',
        'SB_SYNC_LOG_RETENTION_DAYS': 90,
        
        # Rate limiting
        'SB_SYNC_RATE_LIMIT_PER_MINUTE': 60,
        'SB_SYNC_RATE_LIMIT_PER_HOUR': 3000,
        
        # Authentication
        'SB_SYNC_TOKEN_EXPIRY_DAYS': 7,
        'SB_SYNC_REQUIRE_AUTHENTICATION': True,
        
        # Caching
        'SB_SYNC_ENABLE_CACHE': True,
        'SB_SYNC_CACHE_TIMEOUT': 3600,
        
        # Performance
        'SB_SYNC_ENABLE_PERFORMANCE_MONITORING': True,
        'SB_SYNC_ENABLE_BULK_OPERATIONS': True,
        'SB_SYNC_BULK_BATCH_SIZE': 1000,
        
        # Error handling
        'SB_SYNC_ENABLE_RETRY': True,
        'SB_SYNC_MAX_RETRIES': 3,
        'SB_SYNC_RETRY_DELAY': 1,
        
        # Models
        'SB_SYNC_ALLOWED_MODELS': [],
        'SB_SYNC_EXCLUDED_MODELS': ['sb_sync.SyncLog', 'sb_sync.SyncMetadata'],
    }
    
    # Advanced settings (optional)
    ADVANCED_DEFAULTS = {
        # Error handling
        'SB_SYNC_ENABLE_ERROR_CATEGORIZATION': True,
        'SB_SYNC_ENABLE_ERROR_SEVERITY': True,
        'SB_SYNC_ENABLE_ERROR_CONTEXT': True,
        'SB_SYNC_ENABLE_PARTIAL_SUCCESS': True,
        'SB_SYNC_PARTIAL_SUCCESS_THRESHOLD': 0.5,
        
        # Security
        'SB_SYNC_ENABLE_CSRF': False,
        'SB_SYNC_ENABLE_CORS': True,
        'SB_SYNC_CORS_ORIGINS': ['*'],
        
        # API features
        'SB_SYNC_ENABLE_COMPRESSION': True,
        'SB_SYNC_ENABLE_PAGINATION': True,
        'SB_SYNC_PAGE_SIZE': 50,
        'SB_SYNC_MAX_PAGE_SIZE': 200,
        'SB_SYNC_ENABLE_FILTERING': True,
        'SB_SYNC_ENABLE_SORTING': True,
        'SB_SYNC_ENABLE_SEARCH': True,
        'SB_SYNC_SEARCH_FIELDS': ['name', 'description'],
        
        # Transactions
        'SB_SYNC_ENABLE_TRANSACTIONS': True,
        'SB_SYNC_ENABLE_ROLLBACK': True,
        
        # Background tasks
        'SB_SYNC_ENABLE_BACKGROUND_TASKS': True,
        'SB_SYNC_CELERY_BROKER_URL': 'redis://localhost:6379/0',
        'SB_SYNC_CELERY_RESULT_BACKEND': 'redis://localhost:6379/0',
        
        # Monitoring
        'SB_SYNC_ENABLE_METRICS': True,
        'SB_SYNC_METRICS_BACKEND': 'memory',
        'SB_SYNC_ENABLE_ALERTS': False,
        'SB_SYNC_ENABLE_DASHBOARD': False,
    }
    
    # Error handling configuration
    ERROR_CONFIG = {
        'categories': [
            'validation', 'authentication', 'authorization', 'database',
            'network', 'timeout', 'rate_limit', 'configuration',
            'security', 'performance', 'unknown'
        ],
        'severity_levels': ['low', 'medium', 'high', 'critical'],
        'retryable_errors': ['database', 'network', 'timeout', 'rate_limit'],
        'retry_config': {
            'max_retries': 3,
            'base_delay': 1,
            'max_delay': 60,
            'backoff_factor': 2,
        },
        'recovery_strategies': {
            'database': 'reconnect',
            'network': 'wait_and_retry',
            'configuration': 'reload_settings'
        },
        'fallback_strategies': {
            'database': 'cache',
            'network': 'offline_mode',
            'validation': 'default_values'
        },
    }
    
    # Performance configuration
    PERFORMANCE_CONFIG = {
        'memory_thresholds': {
            'warning': 500,  # MB
            'critical': 1000,  # MB
        },
        'cache_thresholds': {
            'hit_rate_warning': 0.7,  # 70%
            'hit_rate_critical': 0.5,  # 50%
        },
        'processing_thresholds': {
            'warning': 5.0,  # seconds
            'critical': 10.0,  # seconds
        },
        'query_thresholds': {
            'warning': 50,  # queries
            'critical': 100,  # queries
        },
    }
    
    # Security configuration
    SECURITY_CONFIG = {
        'encryption_enabled': False,
        'encryption_algorithm': 'AES256',
        'signing_enabled': False,
        'signing_algorithm': 'HMAC-SHA256',
        'sanitization_rules': [
            'html_escaping',
            'sql_injection_prevention',
            'xss_prevention'
        ],
        'validation_rules': [
            'required_fields',
            'data_types',
            'value_ranges',
            'format_validation'
        ],
    }
    
    @classmethod
    def get_setting(cls, key: str, default: Any = None) -> Any:
        """Get a setting value with fallback to defaults"""
        # Check Django settings first
        if hasattr(settings, key):
            return getattr(settings, key)
        
        # Check core defaults
        if key in cls.CORE_DEFAULTS:
            return cls.CORE_DEFAULTS[key]
        
        # Check advanced defaults
        if key in cls.ADVANCED_DEFAULTS:
            return cls.ADVANCED_DEFAULTS[key]
        
        return default
    
    @classmethod
    def get_all_settings(cls) -> Dict[str, Any]:
        """Get all current settings"""
        config = {}
        
        # Add core settings
        for key in cls.CORE_DEFAULTS:
            config[key] = cls.get_setting(key)
        
        # Add advanced settings
        for key in cls.ADVANCED_DEFAULTS:
            config[key] = cls.get_setting(key)
        
        return config
    
    @classmethod
    def get_error_config(cls) -> Dict[str, Any]:
        """Get error handling configuration"""
        return cls.ERROR_CONFIG
    
    @classmethod
    def get_performance_config(cls) -> Dict[str, Any]:
        """Get performance configuration"""
        return cls.PERFORMANCE_CONFIG
    
    @classmethod
    def get_security_config(cls) -> Dict[str, Any]:
        """Get security configuration"""
        return cls.SECURITY_CONFIG
    
    @classmethod
    def validate_settings(cls) -> List[str]:
        """Validate current settings and return list of issues"""
        issues = []
        
        # Check required Django settings
        required_settings = ['SECRET_KEY', 'DATABASES']
        for setting in required_settings:
            if not hasattr(settings, setting):
                issues.append(f"Missing required Django setting: {setting}")
        
        # Check database configuration
        if hasattr(settings, 'DATABASES'):
            if 'default' not in settings.DATABASES:
                issues.append("Missing 'default' database configuration")
        
        # Check log directory
        log_dir = cls.get_setting('SB_SYNC_LOG_DIR')
        if log_dir:
            try:
                Path(log_dir).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(f"Cannot create log directory '{log_dir}': {str(e)}")
        
        # Check Celery configuration
        if cls.get_setting('SB_SYNC_ENABLE_BACKGROUND_TASKS'):
            broker_url = cls.get_setting('SB_SYNC_CELERY_BROKER_URL')
            if not broker_url:
                issues.append("Celery broker URL not configured")
        
        # Check batch sizes
        batch_size = cls.get_setting('SB_SYNC_BATCH_SIZE')
        max_batch_size = cls.get_setting('SB_SYNC_MAX_BATCH_SIZE')
        if batch_size > max_batch_size:
            issues.append(f"Batch size ({batch_size}) cannot exceed max batch size ({max_batch_size})")
        
        return issues
    
    @classmethod
    def get_model_config(cls, model_name: str) -> Dict[str, Any]:
        """Get configuration for a specific model"""
        allowed_models = cls.get_setting('SB_SYNC_ALLOWED_MODELS', [])
        excluded_models = cls.get_setting('SB_SYNC_EXCLUDED_MODELS', [])
        
        config = {
            'enabled': True,
            'sync_enabled': True,
            'push_enabled': True,
            'pull_enabled': True,
            'validation_enabled': True,
            'sanitization_enabled': True,
            'compression_enabled': True,
            'conflict_resolution': 'last_write_wins',
            'sync_status_enabled': True,
            'sync_history_enabled': True,
            'sync_statistics_enabled': True,
            'sync_monitoring_enabled': True,
            'sync_api_docs_enabled': True,
            'sync_hooks_enabled': True,
            'sync_middleware_enabled': True,
            'sync_signals_enabled': True,
            'sync_permissions_enabled': True,
            'sync_authentication_enabled': True,
            'sync_throttling_enabled': True,
        }
        
        # Check if model is allowed/excluded
        if allowed_models and model_name not in allowed_models:
            config['enabled'] = False
            config['sync_enabled'] = False
        
        if model_name in excluded_models:
            config['enabled'] = False
            config['sync_enabled'] = False
        
        return config
    
    @classmethod
    def export_config(cls, filepath: Optional[str] = None) -> str:
        """Export current configuration to JSON file"""
        config = {
            'core_settings': {k: cls.get_setting(k) for k in cls.CORE_DEFAULTS},
            'advanced_settings': {k: cls.get_setting(k) for k in cls.ADVANCED_DEFAULTS},
            'error_config': cls.get_error_config(),
            'performance_config': cls.get_performance_config(),
            'security_config': cls.get_security_config(),
        }
        
        if filepath:
            with open(filepath, 'w') as f:
                json.dump(config, f, indent=2)
            return f"Configuration exported to {filepath}"
        
        return json.dumps(config, indent=2)
    
    @classmethod
    def import_config(cls, filepath: str) -> str:
        """Import configuration from JSON file"""
        try:
            with open(filepath, 'r') as f:
                config = json.load(f)
            
            # Update Django settings (this is a simplified approach)
            # In practice, you'd want to be more careful about this
            for section, settings_dict in config.items():
                if section == 'core_settings':
                    for key, value in settings_dict.items():
                        setattr(settings, key, value)
            
            return f"Configuration imported from {filepath}"
        except Exception as e:
            return f"Failed to import configuration: {str(e)}"
    
    @classmethod
    def get_config_summary(cls) -> Dict[str, Any]:
        """Get a summary of current configuration"""
        return {
            'core_settings_count': len(cls.CORE_DEFAULTS),
            'advanced_settings_count': len(cls.ADVANCED_DEFAULTS),
            'validation_issues': cls.validate_settings(),
            'performance_enabled': cls.get_setting('SB_SYNC_ENABLE_PERFORMANCE_MONITORING'),
            'caching_enabled': cls.get_setting('SB_SYNC_ENABLE_CACHE'),
            'background_tasks_enabled': cls.get_setting('SB_SYNC_ENABLE_BACKGROUND_TASKS'),
            'authentication_required': cls.get_setting('SB_SYNC_REQUIRE_AUTHENTICATION'),
            'rate_limiting_enabled': cls.get_setting('SB_SYNC_RATE_LIMIT_PER_MINUTE') > 0,
        }


# Convenience functions for easier access
def get_setting(key: str, default: Any = None) -> Any:
    """Get a setting value"""
    return SbSyncConfig.get_setting(key, default)


def get_all_settings() -> Dict[str, Any]:
    """Get all settings"""
    return SbSyncConfig.get_all_settings()


def validate_settings() -> List[str]:
    """Validate settings"""
    return SbSyncConfig.validate_settings()


def get_model_config(model_name: str) -> Dict[str, Any]:
    """Get model configuration"""
    return SbSyncConfig.get_model_config(model_name)


def get_config_summary() -> Dict[str, Any]:
    """Get configuration summary"""
    return SbSyncConfig.get_config_summary() 