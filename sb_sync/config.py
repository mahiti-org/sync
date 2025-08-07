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
            'sb_sync.UserSite',
            'sb_sync.ModelPermission',
            'sb_sync.UserSyncMetadata',
            'sb_sync.DataFilter',
        ],
        'INCLUDE_CUSTOM_MODELS': True,
        'MODEL_PREFIX': '',
        'MODEL_SUFFIX': '',
        'MODEL_NAMESPACE': '',
        
        # New advanced configuration options
        'EXCLUDE_ABSTRACT_MODELS': True,  # Exclude abstract models
        'EXCLUDE_PROXY_MODELS': True,     # Exclude proxy models
        'EXCLUDE_HISTORICAL_MODELS': True, # Exclude historical models (simple_history)
        'EXCLUDE_MANAGER_MODELS': True,   # Exclude models with custom managers that shouldn't be synced
        
        # Pattern-based filtering
        'INCLUDE_MODEL_PATTERNS': [
            # Regex patterns for models to include
            # Example: [r'^myapp\.', r'^ecommerce\.']
        ],
        'EXCLUDE_MODEL_PATTERNS': [
            # Regex patterns for models to exclude
            r'^.*\.Historical.*$',  # Exclude all historical models
            r'^.*\.Log$',           # Exclude log models
            r'^.*\.Cache$',         # Exclude cache models
            r'^.*\.Session$',       # Exclude session models
            r'^.*\.Permission$',    # Exclude permission models
        ],
        
        # Field-based filtering
        'EXCLUDE_MODELS_WITH_FIELDS': [
            # Exclude models that have specific fields
            'created_at',  # Exclude models with created_at field (usually system models)
            'updated_at',  # Exclude models with updated_at field
            'deleted_at',  # Exclude soft-delete models
        ],
        'REQUIRE_MODELS_WITH_FIELDS': [
            # Only include models that have specific fields
            # Example: ['id'] - only models with 'id' field
        ],
        
        # App-specific configuration
        'APP_SPECIFIC_EXCLUSIONS': {
            # Per-app exclusion rules
            'auth': ['Group', 'Permission'],  # Exclude specific models from auth app
            'admin': ['LogEntry'],            # Exclude admin log entries
        },
        
        # Model type filtering
        'INCLUDE_MODEL_TYPES': [
            # Types of models to include: 'concrete', 'abstract', 'proxy'
            'concrete'
        ],
        
        # Performance and monitoring
        'ENABLE_DISCOVERY_CACHING': True,
        'DISCOVERY_CACHE_TIMEOUT': 3600,  # Cache discovery results for 1 hour
        'MAX_MODELS_PER_APP': 100,        # Limit models per app to prevent overload
        
        # Validation and safety
        'VALIDATE_MODEL_ACCESS': True,     # Validate that models can be accessed
        'CHECK_MODEL_PERMISSIONS': True,   # Check if current user can access models
        'SAFE_DISCOVERY_MODE': True,      # Only discover models that are safe to sync
        
        # Custom discovery hooks
        'CUSTOM_DISCOVERY_FUNCTIONS': [
            # List of custom functions to call during discovery
            # Example: ['myapp.discovery.custom_filter']
        ],
        
        # Discovery reporting
        'GENERATE_DISCOVERY_REPORT': True,
        'DISCOVERY_REPORT_FORMAT': 'json',  # 'json', 'csv', 'html'
        'SAVE_DISCOVERY_HISTORY': True,
    }
    

    
    # Permission Configuration
    PERMISSIONS = {
        'ENABLE_DYNAMIC_PERMISSIONS': True,
        'AUTO_GENERATE_PERMISSIONS': True,
        'DEFAULT_PERMISSION_TEMPLATE': 'read_write',
        'ENABLE_ROLE_BASED_ACCESS': True,
        'ENABLE_MULTI_TENANT': True,
        'ENABLE_DATA_FILTERING': True,
        'DEFAULT_FILTER_TEMPLATE': 'site',
    }
    
    @classmethod
    def get_config(cls, section: str = None, key: str = None) -> Any:
        """Get configuration value from database with fallback to defaults"""
        try:
            from .models import SyncConfiguration
            
            if section is None:
                # Return all sections with database values merged with defaults
                sections = {
                    'CORE': cls.CORE.copy(),
                    'ADVANCED': cls.ADVANCED.copy(),
                    'ERROR': cls.ERROR.copy(),
                    'PERFORMANCE': cls.PERFORMANCE.copy(),
                    'SECURITY': cls.SECURITY.copy(),
                    'MODEL_DISCOVERY': cls.MODEL_DISCOVERY.copy(),
                    'PERMISSIONS': cls.PERMISSIONS.copy(),
                }
                
                # Merge database values with defaults
                for section_name in sections:
                    db_section = SyncConfiguration.get_section(section_name)
                    sections[section_name].update(db_section)
                
                return sections
            
            section_config = getattr(cls, section.upper(), {}).copy()
            
            if key is None:
                # Return entire section with database values merged
                db_section = SyncConfiguration.get_section(section)
                section_config.update(db_section)
                return section_config
            
            # Try database first, then fallback to defaults
            db_value = SyncConfiguration.get_value(section, key)
            if db_value is not None:
                return db_value
            
            return section_config.get(key)
            
        except Exception as e:
            # Fallback to in-memory defaults if database is not available
            logger.warning(f"Database configuration not available, using defaults: {e}")
            
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
        """Set configuration value in database"""
        try:
            from .models import SyncConfiguration
            
            # Validate section
            section_name = section.upper()
            if not hasattr(cls, section_name):
                logger.error(f"Invalid configuration section: {section}")
                return
            
            # Store in database
            SyncConfiguration.set_value(section, key, value)
            logger.info(f"Configuration updated in database: {section}.{key} = {value}")
            
        except Exception as e:
            # Fallback to in-memory storage if database is not available
            logger.warning(f"Database not available, using in-memory storage: {e}")
            section_name = section.upper()
            if hasattr(cls, section_name):
                section_config = getattr(cls, section_name)
                section_config[key] = value
                logger.info(f"Configuration updated in memory: {section}.{key} = {value}")
            else:
                logger.error(f"Invalid configuration section: {section}")
    
    @classmethod
    def get_all_models(cls) -> List[str]:
        """Get all models from the application scope with advanced filtering options"""
        if not cls.get_config('MODEL_DISCOVERY', 'AUTO_DISCOVER_MODELS'):
            return []
        
        import re
        from django.core.cache import cache
        
        # Check cache first if enabled
        cache_key = 'sb_sync_model_discovery'
        if cls.get_config('MODEL_DISCOVERY', 'ENABLE_DISCOVERY_CACHING'):
            cached_models = cache.get(cache_key)
            if cached_models is not None:
                return cached_models
        
        all_models = []
        include_apps = cls.get_config('MODEL_DISCOVERY', 'INCLUDE_APPS')
        exclude_models = cls.get_config('MODEL_DISCOVERY', 'EXCLUDE_MODELS')
        
        # Get advanced configuration options
        exclude_abstract = cls.get_config('MODEL_DISCOVERY', 'EXCLUDE_ABSTRACT_MODELS')
        exclude_proxy = cls.get_config('MODEL_DISCOVERY', 'EXCLUDE_PROXY_MODELS')
        exclude_historical = cls.get_config('MODEL_DISCOVERY', 'EXCLUDE_HISTORICAL_MODELS')
        exclude_manager = cls.get_config('MODEL_DISCOVERY', 'EXCLUDE_MANAGER_MODELS')
        
        include_patterns = cls.get_config('MODEL_DISCOVERY', 'INCLUDE_MODEL_PATTERNS')
        exclude_patterns = cls.get_config('MODEL_DISCOVERY', 'EXCLUDE_MODEL_PATTERNS')
        exclude_models_with_fields = cls.get_config('MODEL_DISCOVERY', 'EXCLUDE_MODELS_WITH_FIELDS')
        require_models_with_fields = cls.get_config('MODEL_DISCOVERY', 'REQUIRE_MODELS_WITH_FIELDS')
        app_specific_exclusions = cls.get_config('MODEL_DISCOVERY', 'APP_SPECIFIC_EXCLUSIONS')
        include_model_types = cls.get_config('MODEL_DISCOVERY', 'INCLUDE_MODEL_TYPES')
        max_models_per_app = cls.get_config('MODEL_DISCOVERY', 'MAX_MODELS_PER_APP')
        
        # Comprehensive list of apps to exclude when INCLUDE_APPS is empty
        excluded_apps = {
            # Django built-in apps
            'admin', 'auth', 'contenttypes', 'sessions', 'messages', 'staticfiles',
            # sb-sync app itself and its internal models
            'sb_sync',
            # sb-sync dependencies and external packages
            'rest_framework', 'rest_framework_simplejwt', 'simple_history',
            'django_filters', 'django_cors_headers', 'django_debug_toolbar',
            'django_extensions', 'django_silk', 'django_prometheus',
            'django_cacheops', 'django_simple_history',
            # Other common Django apps that shouldn't be synced
            'sites', 'flatpages', 'redirects', 'humanize', 'postgres', 'mysql',
            'oracle', 'sqlite3', 'cache', 'gis', 'localflavor',
            # Additional Django contrib apps
            'sitemaps', 'syndication', 'comments', 'webdesign',
            # Database and cache backends
            'django_db', 'django_cache', 'django_redis',
            # Test and development apps
            'test', 'tests', 'test_project', 'test_app',
            # Common third-party apps that shouldn't be synced
            'celery', 'redis', 'psutil', 'prometheus_client',
            'bleach', 'html5lib', 'lxml', 'beautifulsoup4',
            'markupsafe', 'webencodings', 'cssselect', 'soupsieve',
            'click', 'kombu', 'billiard', 'amqp', 'vine',
            'importlib_metadata', 'zipp', 'typing_extensions',
            'packaging', 'pyparsing', 'python_dateutil', 'pytz',
            'six', 'certifi', 'charset_normalizer', 'idna',
            'urllib3', 'requests', 'python_json_logger',
            'PyJWT', 'asgiref', 'sqlparse', 'tzdata',
            'wcwidth', 'prompt_toolkit', 'click_repl', 'click_plugins',
            'click_didyoumean', 'funcy', 'gprof2dot'
        }
        
        for app_config in apps.get_app_configs():
            app_label = app_config.label
            
            # If INCLUDE_APPS is specified, only include models from those apps
            if include_apps:
                if app_label not in include_apps:
                    continue
            else:
                # If INCLUDE_APPS is empty, exclude Django built-ins, sb-sync, and dependencies
                if app_label in excluded_apps:
                    continue
            
            # Skip apps without models module
            if not app_config.models_module:
                continue
                
            app_models = []
            
            # Get models from the app
            for model_name, model in app_config.models_module.__dict__.items():
                # Skip if it's not a model class
                if not hasattr(model, '_meta') or not hasattr(model._meta, 'app_label'):
                    continue
                    
                full_model_name = f"{app_label}.{model.__name__}"
                
                # Skip models that are explicitly excluded
                if full_model_name in exclude_models:
                    continue
                
                # Check app-specific exclusions
                if app_label in app_specific_exclusions:
                    if model.__name__ in app_specific_exclusions[app_label]:
                        continue
                
                # Check model type filtering
                if model._meta.abstract and exclude_abstract:
                    continue
                if model._meta.proxy and exclude_proxy:
                    continue
                
                # Check model type inclusion
                model_type = 'abstract' if model._meta.abstract else 'proxy' if model._meta.proxy else 'concrete'
                if model_type not in include_model_types:
                    continue
                
                # Check pattern-based filtering
                if include_patterns:
                    if not any(re.match(pattern, full_model_name) for pattern in include_patterns):
                        continue
                
                if exclude_patterns:
                    if any(re.match(pattern, full_model_name) for pattern in exclude_patterns):
                        continue
                
                # Check historical model exclusion
                if exclude_historical and 'Historical' in model.__name__:
                    continue
                
                # Check field-based filtering
                model_fields = [field.name for field in model._meta.fields]
                
                # Exclude models with specific fields
                if exclude_models_with_fields:
                    if any(field in model_fields for field in exclude_models_with_fields):
                        continue
                
                # Require models with specific fields
                if require_models_with_fields:
                    if not all(field in model_fields for field in require_models_with_fields):
                        continue
                
                # Check manager-based exclusion
                if exclude_manager and hasattr(model, '_default_manager'):
                    manager_name = model._default_manager.__class__.__name__
                    if manager_name in ['EmptyManager', 'DisabledManager']:
                        continue
                
                app_models.append(full_model_name)
            
            # Limit models per app
            if max_models_per_app and len(app_models) > max_models_per_app:
                app_models = app_models[:max_models_per_app]
            
            all_models.extend(app_models)
        
        # Sort the final list
        all_models = sorted(all_models)
        
        # Cache the results if enabled
        if cls.get_config('MODEL_DISCOVERY', 'ENABLE_DISCOVERY_CACHING'):
            cache_timeout = cls.get_config('MODEL_DISCOVERY', 'DISCOVERY_CACHE_TIMEOUT')
            cache.set(cache_key, all_models, timeout=cache_timeout)
        
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
        """Check if a model is enabled for sync operations with advanced filtering"""
        import re
        from django.apps import apps
        
        exclude_models = cls.get_config('MODEL_DISCOVERY', 'EXCLUDE_MODELS')
        include_apps = cls.get_config('MODEL_DISCOVERY', 'INCLUDE_APPS')
        
        # Check if model is explicitly excluded
        if model_name in exclude_models:
            return False
        
        # Get advanced configuration options
        exclude_abstract = cls.get_config('MODEL_DISCOVERY', 'EXCLUDE_ABSTRACT_MODELS')
        exclude_proxy = cls.get_config('MODEL_DISCOVERY', 'EXCLUDE_PROXY_MODELS')
        exclude_historical = cls.get_config('MODEL_DISCOVERY', 'EXCLUDE_HISTORICAL_MODELS')
        
        include_patterns = cls.get_config('MODEL_DISCOVERY', 'INCLUDE_MODEL_PATTERNS')
        exclude_patterns = cls.get_config('MODEL_DISCOVERY', 'EXCLUDE_MODEL_PATTERNS')
        exclude_models_with_fields = cls.get_config('MODEL_DISCOVERY', 'EXCLUDE_MODELS_WITH_FIELDS')
        require_models_with_fields = cls.get_config('MODEL_DISCOVERY', 'REQUIRE_MODELS_WITH_FIELDS')
        app_specific_exclusions = cls.get_config('MODEL_DISCOVERY', 'APP_SPECIFIC_EXCLUSIONS')
        include_model_types = cls.get_config('MODEL_DISCOVERY', 'INCLUDE_MODEL_TYPES')
        
        # Comprehensive list of apps to exclude when INCLUDE_APPS is empty
        excluded_apps = {
            # Django built-in apps
            'admin', 'auth', 'contenttypes', 'sessions', 'messages', 'staticfiles',
            # sb-sync app itself and its internal models
            'sb_sync',
            # sb-sync dependencies and external packages
            'rest_framework', 'rest_framework_simplejwt', 'simple_history',
            'django_filters', 'django_cors_headers', 'django_debug_toolbar',
            'django_extensions', 'django_silk', 'django_prometheus',
            'django_cacheops', 'django_simple_history',
            # Other common Django apps that shouldn't be synced
            'sites', 'flatpages', 'redirects', 'humanize', 'postgres', 'mysql',
            'oracle', 'sqlite3', 'cache', 'gis', 'localflavor',
            # Additional Django contrib apps
            'sitemaps', 'syndication', 'comments', 'webdesign',
            # Database and cache backends
            'django_db', 'django_cache', 'django_redis',
            # Test and development apps
            'test', 'tests', 'test_project', 'test_app',
            # Common third-party apps that shouldn't be synced
            'celery', 'redis', 'psutil', 'prometheus_client',
            'bleach', 'html5lib', 'lxml', 'beautifulsoup4',
            'markupsafe', 'webencodings', 'cssselect', 'soupsieve',
            'click', 'kombu', 'billiard', 'amqp', 'vine',
            'importlib_metadata', 'zipp', 'typing_extensions',
            'packaging', 'pyparsing', 'python_dateutil', 'pytz',
            'six', 'certifi', 'charset_normalizer', 'idna',
            'urllib3', 'requests', 'python_json_logger',
            'PyJWT', 'asgiref', 'sqlparse', 'tzdata',
            'wcwidth', 'prompt_toolkit', 'click_repl', 'click_plugins',
            'click_didyoumean', 'funcy', 'gprof2dot'
        }
        
        # Get the app label and model name from the model name
        if '.' in model_name:
            app_label, model_class_name = model_name.split('.', 1)
        else:
            app_label = model_name
            model_class_name = model_name
        
        # If INCLUDE_APPS is specified, check if model's app is included
        if include_apps:
            if app_label not in include_apps:
                return False
        else:
            # If INCLUDE_APPS is empty, exclude Django built-ins, sb-sync, and dependencies
            if app_label in excluded_apps:
                return False
        
        # Check app-specific exclusions
        if app_label in app_specific_exclusions:
            if model_class_name in app_specific_exclusions[app_label]:
                return False
        
        # Check pattern-based filtering
        if include_patterns:
            if not any(re.match(pattern, model_name) for pattern in include_patterns):
                return False
        
        if exclude_patterns:
            if any(re.match(pattern, model_name) for pattern in exclude_patterns):
                return False
        
        # Check historical model exclusion
        if exclude_historical and 'Historical' in model_class_name:
            return False
        
        # Try to get the actual model class for advanced checks
        try:
            model_class = apps.get_model(model_name)
            
            # Check model type filtering
            if exclude_abstract and model_class._meta.abstract:
                return False
            if exclude_proxy and model_class._meta.proxy:
                return False
            
            # Check model type inclusion
            model_type = 'abstract' if model_class._meta.abstract else 'proxy' if model_class._meta.proxy else 'concrete'
            if model_type not in include_model_types:
                return False
            
            # Check field-based filtering
            model_fields = [field.name for field in model_class._meta.fields]
            
            # Exclude models with specific fields
            if exclude_models_with_fields:
                if any(field in model_fields for field in exclude_models_with_fields):
                    return False
            
            # Require models with specific fields
            if require_models_with_fields:
                if not all(field in model_fields for field in require_models_with_fields):
                    return False
                    
        except Exception:
            # If we can't get the model class, assume it's enabled
            pass
        
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