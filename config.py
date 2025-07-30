"""
Configuration management for sb-sync package
"""
import os
import json
import logging
from django.conf import settings
from django.apps import apps
from typing import Dict, Any, List, Optional

logger = logging.getLogger('sb_sync')

class SyncConfig:
    """Configuration management for sb-sync"""
    
    # Core Configuration
    CORE = {
        'ENABLED': True,
        'DEBUG': False,
        'LOG_LEVEL': 'INFO',
        'DEFAULT_BATCH_SIZE': 1000,
        'MAX_BATCH_SIZE': 10000,
        'DEFAULT_TIMEOUT': 30,
        'MAX_TIMEOUT': 300,
        'RETRY_ATTEMPTS': 3,
        'RETRY_DELAY': 1,
    }
    
    # Advanced Configuration
    ADVANCED = {
        'ENABLE_CACHING': True,
        'CACHE_TIMEOUT': 3600,
        'ENABLE_COMPRESSION': True,
        'COMPRESSION_LEVEL': 6,
        'ENABLE_ENCRYPTION': False,
        'ENCRYPTION_KEY': None,
        'ENABLE_LOGGING': True,
        'LOG_FILE': 'sb_sync.log',
        'ENABLE_METRICS': True,
        'METRICS_INTERVAL': 60,
    }
    
    # Error Handling Configuration
    ERROR = {
        'ENABLE_ERROR_HANDLING': True,
        'ERROR_RETRY_ATTEMPTS': 3,
        'ERROR_RETRY_DELAY': 1,
        'ERROR_LOG_LEVEL': 'ERROR',
        'ERROR_NOTIFICATION_EMAIL': None,
        'ERROR_SLACK_WEBHOOK': None,
        'ERROR_DISCORD_WEBHOOK': None,
        'ERROR_TELEGRAM_BOT_TOKEN': None,
        'ERROR_TELEGRAM_CHAT_ID': None,
    }
    
    # Performance Configuration
    PERFORMANCE = {
        'ENABLE_QUERY_OPTIMIZATION': True,
        'ENABLE_MEMORY_OPTIMIZATION': True,
        'ENABLE_CONNECTION_POOLING': True,
        'POOL_SIZE': 10,
        'MAX_CONNECTIONS': 100,
        'CONNECTION_TIMEOUT': 30,
        'ENABLE_BULK_OPERATIONS': True,
        'BULK_SIZE': 1000,
        'ENABLE_ASYNC_PROCESSING': True,
        'ASYNC_WORKERS': 4,
        'ASYNC_QUEUE_SIZE': 1000,
    }
    
    # Security Configuration
    SECURITY = {
        'ENABLE_RATE_LIMITING': True,
        'RATE_LIMIT_REQUESTS': 100,
        'RATE_LIMIT_WINDOW': 60,
        'ENABLE_IP_WHITELIST': False,
        'IP_WHITELIST': [],
        'ENABLE_API_KEY_AUTH': True,
        'API_KEY_HEADER': 'X-API-Key',
        'ENABLE_JWT_AUTH': True,
        'JWT_SECRET_KEY': None,
        'JWT_ALGORITHM': 'HS256',
        'JWT_EXPIRATION': 3600,
    }
    
    # Model Discovery Configuration
    MODEL_DISCOVERY = {
        'AUTO_DISCOVER_MODELS': True,
        'INCLUDE_APPS': [
            # List of apps whose models will be synced
            # Empty list = include all apps
            # Example: ['myapp', 'ecommerce', 'inventory']
        ],
        'EXCLUDE_MODELS': [
            # Models within the included apps that will be excluded from sync
            'sb_sync.SyncLog',
            'sb_sync.SyncMetadata',
            'sb_sync.PerformanceMetrics',
            'sb_sync.Organization',
            'sb_sync.UserOrganization',
            'sb_sync.ModelPermission',
            'sb_sync.UserSyncMetadata',
            'sb_sync.DataFilter',
        ],
        'INCLUDE_CUSTOM_MODELS': True,
        'MODEL_PREFIX': '',
        'MODEL_SUFFIX': '',
        'MODEL_NAMESPACE': '',
    }
    

    
    # Permission Configuration
    PERMISSIONS = {
        'ENABLE_DYNAMIC_PERMISSIONS': True,
        'AUTO_GENERATE_PERMISSIONS': True,
        'DEFAULT_PERMISSION_TEMPLATE': 'read_write',
        'ENABLE_ROLE_BASED_ACCESS': True,
        'ENABLE_MULTI_TENANT': True,
        'ENABLE_DATA_FILTERING': True,
        'DEFAULT_FILTER_TEMPLATE': 'organization',
    }
    
    @classmethod
    def get_config(cls, section: str = None, key: str = None) -> Any:
        """Get configuration value"""
        if section is None:
            return {
                'CORE': cls.CORE,
                'ADVANCED': cls.ADVANCED,
                'ERROR': cls.ERROR,
                'PERFORMANCE': cls.PERFORMANCE,
                'SECURITY': cls.SECURITY,
                'MODEL_DISCOVERY': cls.MODEL_DISCOVERY,

                'PERMISSIONS': cls.PERMISSIONS,
            }
        
        section_config = getattr(cls, section.upper(), {})
        
        if key is None:
            return section_config
        
        return section_config.get(key)
    
    @classmethod
    def set_config(cls, section: str, key: str, value: Any) -> None:
        """Set configuration value"""
        section_name = section.upper()
        if hasattr(cls, section_name):
            section_config = getattr(cls, section_name)
            section_config[key] = value
            logger.info(f"Configuration updated: {section}.{key} = {value}")
        else:
            logger.error(f"Invalid configuration section: {section}")
    
    @classmethod
    def get_all_models(cls) -> List[str]:
        """Get all models from the application scope with inclusions and exclusions"""
        if not cls.get_config('MODEL_DISCOVERY', 'AUTO_DISCOVER_MODELS'):
            return []
        
        all_models = []
        include_apps = cls.get_config('MODEL_DISCOVERY', 'INCLUDE_APPS')
        exclude_models = cls.get_config('MODEL_DISCOVERY', 'EXCLUDE_MODELS')
        
        for app_config in apps.get_app_configs():
            app_label = app_config.label
            
            # If INCLUDE_APPS is specified, only include models from those apps
            if include_apps and app_label not in include_apps:
                continue
            
            if app_config.models_module:
                for model in app_config.models_module.__dict__.values():
                    if hasattr(model, '_meta') and hasattr(model._meta, 'app_label'):
                        model_name = f"{app_label}.{model.__name__}"
                        
                        # Skip models that are explicitly excluded
                        if model_name in exclude_models:
                            continue
                        
                        all_models.append(model_name)
        
        return all_models
    
    @classmethod
    def get_model_config(cls, model_name: str) -> Dict[str, Any]:
        """Get configuration for a specific model"""
        model_config = {
            'enabled': True,
            'push_enabled': True,
            'pull_enabled': True,
            'batch_size': cls.get_config('CORE', 'DEFAULT_BATCH_SIZE'),
            'timeout': cls.get_config('CORE', 'DEFAULT_TIMEOUT'),
            'retry_attempts': cls.get_config('CORE', 'RETRY_ATTEMPTS'),
            'retry_delay': cls.get_config('CORE', 'RETRY_DELAY'),
            'caching_enabled': cls.get_config('ADVANCED', 'ENABLE_CACHING'),
            'compression_enabled': cls.get_config('ADVANCED', 'ENABLE_COMPRESSION'),
            'encryption_enabled': cls.get_config('ADVANCED', 'ENABLE_ENCRYPTION'),
            'logging_enabled': cls.get_config('ADVANCED', 'ENABLE_LOGGING'),
            'metrics_enabled': cls.get_config('ADVANCED', 'ENABLE_METRICS'),
        }
        
        return model_config
    
    @classmethod
    def is_model_enabled(cls, model_name: str) -> bool:
        """Check if a model is enabled for sync operations"""
        exclude_models = cls.get_config('MODEL_DISCOVERY', 'EXCLUDE_MODELS')
        include_apps = cls.get_config('MODEL_DISCOVERY', 'INCLUDE_APPS')
        
        # Check if model is explicitly excluded
        if model_name in exclude_models:
            return False
        
        # If INCLUDE_APPS is specified, check if model's app is included
        if include_apps:
            app_label = model_name.split('.')[0] if '.' in model_name else model_name
            if app_label not in include_apps:
                return False
        
        return True
    
    @classmethod
    def get_default_models(cls) -> List[str]:
        """Get default models for push and pull operations"""
        return cls.get_all_models()
    
    @classmethod
    def export_config(cls, file_path: str = None) -> Dict[str, Any]:
        """Export current configuration"""
        config = {
            'CORE': cls.CORE,
            'ADVANCED': cls.ADVANCED,
            'ERROR': cls.ERROR,
            'PERFORMANCE': cls.PERFORMANCE,
            'SECURITY': cls.SECURITY,
            'MODEL_DISCOVERY': cls.MODEL_DISCOVERY,

            'PERMISSIONS': cls.PERMISSIONS,
        }
        
        if file_path:
            with open(file_path, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Configuration exported to {file_path}")
        
        return config
    
    @classmethod
    def import_config(cls, config_data: Dict[str, Any]) -> None:
        """Import configuration from dictionary"""
        for section, section_data in config_data.items():
            if hasattr(cls, section.upper()):
                section_config = getattr(cls, section.upper())
                section_config.update(section_data)
                logger.info(f"Configuration section {section} imported")
            else:
                logger.warning(f"Unknown configuration section: {section}")
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """Validate configuration and return errors"""
        errors = []
        
        # Validate core configuration
        if cls.CORE['DEFAULT_BATCH_SIZE'] > cls.CORE['MAX_BATCH_SIZE']:
            errors.append("DEFAULT_BATCH_SIZE cannot be greater than MAX_BATCH_SIZE")
        
        if cls.CORE['DEFAULT_TIMEOUT'] > cls.CORE['MAX_TIMEOUT']:
            errors.append("DEFAULT_TIMEOUT cannot be greater than MAX_TIMEOUT")
        
        # Validate performance configuration
        if cls.PERFORMANCE['POOL_SIZE'] > cls.PERFORMANCE['MAX_CONNECTIONS']:
            errors.append("POOL_SIZE cannot be greater than MAX_CONNECTIONS")
        
        # Validate security configuration
        if cls.SECURITY['RATE_LIMIT_REQUESTS'] <= 0:
            errors.append("RATE_LIMIT_REQUESTS must be greater than 0")
        
        if cls.SECURITY['RATE_LIMIT_WINDOW'] <= 0:
            errors.append("RATE_LIMIT_WINDOW must be greater than 0")
        
        return errors
    
    @classmethod
    def get_config_summary(cls) -> Dict[str, Any]:
        """Get configuration summary"""
        all_models = cls.get_all_models()
        enabled_models = [model for model in all_models if cls.is_model_enabled(model)]
        
        return {
            'total_models_discovered': len(all_models),
            'enabled_models': len(enabled_models),
            'excluded_models': len(all_models) - len(enabled_models),
            'auto_discovery_enabled': cls.get_config('MODEL_DISCOVERY', 'AUTO_DISCOVER_MODELS'),
            'include_apps_count': len(cls.get_config('MODEL_DISCOVERY', 'INCLUDE_APPS')),
            'exclude_models_count': len(cls.get_config('MODEL_DISCOVERY', 'EXCLUDE_MODELS')),

            'dynamic_permissions_enabled': cls.get_config('PERMISSIONS', 'ENABLE_DYNAMIC_PERMISSIONS'),
            'core_settings_count': len(cls.CORE),
            'advanced_settings_count': len(cls.ADVANCED),
            'performance_enabled': cls.get_config('PERFORMANCE', 'ENABLE_MONITORING'),
            'caching_enabled': cls.get_config('ADVANCED', 'ENABLE_CACHING'),
            'background_tasks_enabled': cls.get_config('ADVANCED', 'ENABLE_BACKGROUND_TASKS'),
            'authentication_required': cls.get_config('SECURITY', 'REQUIRE_AUTHENTICATION'),
            'rate_limiting_enabled': cls.get_config('SECURITY', 'ENABLE_RATE_LIMITING'),
            'validation_issues': cls.validate_config(),
        }
    
    @classmethod
    def reset_to_defaults(cls) -> None:
        """Reset configuration to default values"""
        # This is a simplified reset - in practice, you'd want to be more careful
        # about which settings to reset
        pass

# Convenience functions
def get_config(section: str = None, key: str = None) -> Any:
    """Get configuration value"""
    return SyncConfig.get_config(section, key)

def set_config(section: str, key: str, value: Any) -> None:
    """Set configuration value"""
    SyncConfig.set_config(section, key, value)

def get_all_models() -> List[str]:
    """Get all models from the application scope"""
    return SyncConfig.get_all_models()

def get_default_models() -> List[str]:
    """Get default models for push and pull operations"""
    return SyncConfig.get_default_models()

def is_model_enabled(model_name: str) -> bool:
    """Check if a model is enabled for sync operations"""
    return SyncConfig.is_model_enabled(model_name)

def export_config(file_path: str = None) -> Dict[str, Any]:
    """Export current configuration"""
    return SyncConfig.export_config(file_path)

def import_config(config_data: Dict[str, Any]) -> None:
    """Import configuration from dictionary"""
    SyncConfig.import_config(config_data)

def validate_config() -> List[str]:
    """Validate configuration and return errors"""
    return SyncConfig.validate_config()

def get_config_summary() -> Dict[str, Any]:
    """Get configuration summary"""
    return SyncConfig.get_config_summary() 