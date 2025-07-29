# Configuration Guide for sb-sync

This guide explains how to manage the simplified configuration system for the sb-sync package.

## Overview

The configuration system has been completely restructured to be more manageable and user-friendly. Instead of one massive 727-line configuration file, we now have:

1. **Core Settings** - Essential settings with sensible defaults
2. **Advanced Settings** - Optional settings for advanced users
3. **Modular Configuration** - Organized by functionality
4. **Management Commands** - Easy-to-use commands for configuration management

## Configuration Structure

### 1. Core Settings (Essential)

These are the most important settings that most users will need to configure:

```python
# Basic configuration
SB_SYNC_BATCH_SIZE = 100
SB_SYNC_MAX_BATCH_SIZE = 1000
SB_SYNC_LOG_DIR = 'logs'
SB_SYNC_LOG_RETENTION_DAYS = 90

# Rate limiting
SB_SYNC_RATE_LIMIT_PER_MINUTE = 60
SB_SYNC_RATE_LIMIT_PER_HOUR = 3000

# Authentication
SB_SYNC_TOKEN_EXPIRY_DAYS = 7
SB_SYNC_REQUIRE_AUTHENTICATION = True

# Caching
SB_SYNC_ENABLE_CACHE = True
SB_SYNC_CACHE_TIMEOUT = 3600

# Performance
SB_SYNC_ENABLE_PERFORMANCE_MONITORING = True
SB_SYNC_ENABLE_BULK_OPERATIONS = True
SB_SYNC_BULK_BATCH_SIZE = 1000

# Error handling
SB_SYNC_ENABLE_RETRY = True
SB_SYNC_MAX_RETRIES = 3
SB_SYNC_RETRY_DELAY = 1

# Models
SB_SYNC_ALLOWED_MODELS = []
SB_SYNC_EXCLUDED_MODELS = ['sb_sync.SyncLog', 'sb_sync.SyncMetadata']
```

### 2. Advanced Settings (Optional)

These settings are for advanced users who need fine-grained control:

```python
# Error handling
SB_SYNC_ENABLE_ERROR_CATEGORIZATION = True
SB_SYNC_ENABLE_ERROR_SEVERITY = True
SB_SYNC_ENABLE_ERROR_CONTEXT = True
SB_SYNC_ENABLE_PARTIAL_SUCCESS = True
SB_SYNC_PARTIAL_SUCCESS_THRESHOLD = 0.5

# Security
SB_SYNC_ENABLE_CSRF = False
SB_SYNC_ENABLE_CORS = True
SB_SYNC_CORS_ORIGINS = ['*']

# API features
SB_SYNC_ENABLE_COMPRESSION = True
SB_SYNC_ENABLE_PAGINATION = True
SB_SYNC_PAGE_SIZE = 50
SB_SYNC_MAX_PAGE_SIZE = 200
SB_SYNC_ENABLE_FILTERING = True
SB_SYNC_ENABLE_SORTING = True
SB_SYNC_ENABLE_SEARCH = True
SB_SYNC_SEARCH_FIELDS = ['name', 'description']

# Transactions
SB_SYNC_ENABLE_TRANSACTIONS = True
SB_SYNC_ENABLE_ROLLBACK = True

# Background tasks
SB_SYNC_ENABLE_BACKGROUND_TASKS = True
SB_SYNC_CELERY_BROKER_URL = 'redis://localhost:6379/0'
SB_SYNC_CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Monitoring
SB_SYNC_ENABLE_METRICS = True
SB_SYNC_METRICS_BACKEND = 'memory'
SB_SYNC_ENABLE_ALERTS = False
SB_SYNC_ENABLE_DASHBOARD = False
```

### 3. Modular Configuration

Configuration is now organized into logical sections:

#### Error Configuration
```python
ERROR_CONFIG = {
    'categories': ['validation', 'authentication', 'authorization', 'database', ...],
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
```

#### Performance Configuration
```python
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
```

#### Security Configuration
```python
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
```

## Configuration Management Commands

### 1. Show Configuration

```bash
# Show all configuration
python manage.py manage_config show

# Show specific section
python manage.py manage_config show --section=core
python manage.py manage_config show --section=advanced
python manage.py manage_config show --section=error
python manage.py manage_config show --section=performance
python manage.py manage_config show --section=security

# Show in different formats
python manage.py manage_config show --format=json
python manage.py manage_config show --format=yaml
python manage.py manage_config show --format=env
```

### 2. Export Configuration

```bash
# Export all configuration
python manage.py manage_config export --file=config.json

# Export specific section
python manage.py manage_config export --section=core --file=core_config.json
python manage.py manage_config export --section=advanced --file=advanced_config.yaml --format=yaml

# Export with different formats
python manage.py manage_config export --format=env --file=config.env
```

### 3. Import Configuration

```bash
# Import from JSON file
python manage.py manage_config import --file=config.json

# Import from YAML file
python manage.py manage_config import --file=config.yaml

# Import from environment file
python manage.py manage_config import --file=config.env

# Force import without confirmation
python manage.py manage_config import --file=config.json --force
```

### 4. Validate Configuration

```bash
# Validate current configuration
python manage.py manage_config validate
```

### 5. Show Configuration Summary

```bash
# Show configuration summary
python manage.py manage_config summary
```

### 6. Reset Configuration

```bash
# Reset to defaults
python manage.py manage_config reset

# Force reset without confirmation
python manage.py manage_config reset --force
```

## Quick Start Guide

### 1. Basic Setup

For most users, the default configuration will work fine. You only need to set a few essential settings:

```python
# In your Django settings.py
SB_SYNC_BATCH_SIZE = 100
SB_SYNC_RATE_LIMIT_PER_MINUTE = 60
SB_SYNC_REQUIRE_AUTHENTICATION = True
SB_SYNC_ENABLE_CACHE = True
```

### 2. Advanced Setup

For advanced users who need more control:

```python
# Performance tuning
SB_SYNC_BATCH_SIZE = 500
SB_SYNC_MAX_BATCH_SIZE = 2000
SB_SYNC_BULK_BATCH_SIZE = 2000

# Rate limiting
SB_SYNC_RATE_LIMIT_PER_MINUTE = 120
SB_SYNC_RATE_LIMIT_PER_HOUR = 5000

# Background tasks
SB_SYNC_ENABLE_BACKGROUND_TASKS = True
SB_SYNC_CELERY_BROKER_URL = 'redis://localhost:6379/0'

# Monitoring
SB_SYNC_ENABLE_PERFORMANCE_MONITORING = True
SB_SYNC_ENABLE_METRICS = True
```

### 3. Production Setup

For production environments:

```python
# Security
SB_SYNC_REQUIRE_AUTHENTICATION = True
SB_SYNC_ENABLE_CSRF = False  # For API endpoints
SB_SYNC_ENABLE_CORS = True
SB_SYNC_CORS_ORIGINS = ['https://yourdomain.com']

# Performance
SB_SYNC_ENABLE_CACHE = True
SB_SYNC_CACHE_TIMEOUT = 7200  # 2 hours
SB_SYNC_ENABLE_PERFORMANCE_MONITORING = True

# Error handling
SB_SYNC_ENABLE_RETRY = True
SB_SYNC_MAX_RETRIES = 5
SB_SYNC_ENABLE_PARTIAL_SUCCESS = True

# Monitoring
SB_SYNC_ENABLE_METRICS = True
SB_SYNC_ENABLE_ALERTS = True
```

## Configuration Best Practices

### 1. Start with Defaults

Always start with the default configuration and only change what you need:

```bash
# Check current configuration
python manage.py manage_config summary

# Validate configuration
python manage.py manage_config validate
```

### 2. Use Environment Variables

For sensitive settings, use environment variables:

```python
import os

SB_SYNC_CELERY_BROKER_URL = os.environ.get('SB_SYNC_CELERY_BROKER_URL', 'redis://localhost:6379/0')
SB_SYNC_ENABLE_ALERTS = os.environ.get('SB_SYNC_ENABLE_ALERTS', 'False').lower() == 'true'
```

### 3. Export Your Configuration

After setting up your configuration, export it for backup:

```bash
python manage.py manage_config export --file=my_config.json
```

### 4. Validate Changes

Always validate your configuration after making changes:

```bash
python manage.py manage_config validate
```

### 5. Use Configuration Sections

Work with specific sections when you only need to modify certain aspects:

```bash
# Only work with performance settings
python manage.py manage_config show --section=performance

# Export only core settings
python manage.py manage_config export --section=core --file=core_settings.json
```

## Troubleshooting

### Common Issues

1. **Configuration Not Found**
   ```bash
   python manage.py manage_config validate
   ```

2. **Invalid Settings**
   ```bash
   python manage.py manage_config show --section=core
   ```

3. **Performance Issues**
   ```bash
   python manage.py manage_config show --section=performance
   ```

### Getting Help

1. **Show Configuration Summary**
   ```bash
   python manage.py manage_config summary
   ```

2. **Validate Configuration**
   ```bash
   python manage.py manage_config validate
   ```

3. **Export Current Configuration**
   ```bash
   python manage.py manage_config export --file=current_config.json
   ```

## Migration from Old Configuration

If you're migrating from the old configuration system:

1. **Export Old Configuration**
   ```bash
   # If you have the old config file
   python manage.py manage_config import --file=old_config.json
   ```

2. **Validate Migration**
   ```bash
   python manage.py manage_config validate
   ```

3. **Export New Configuration**
   ```bash
   python manage.py manage_config export --file=new_config.json
   ```

## Benefits of the New System

1. **Simplified Structure**: From 727 lines to organized, manageable sections
2. **Better Organization**: Logical grouping of related settings
3. **Easier Management**: Command-line tools for configuration management
4. **Validation**: Built-in configuration validation
5. **Documentation**: Clear documentation and examples
6. **Flexibility**: Easy to extend and customize
7. **Backup/Restore**: Export and import configuration
8. **Environment Support**: Easy to manage different environments

## Conclusion

The new configuration system makes it much easier to:

- **Get Started**: Sensible defaults work out of the box
- **Customize**: Easy to modify specific settings
- **Manage**: Command-line tools for all operations
- **Validate**: Built-in validation prevents errors
- **Deploy**: Easy to manage different environments
- **Troubleshoot**: Clear tools for diagnosing issues

This approach reduces the intimidation factor significantly while maintaining all the power and flexibility of the original system. 