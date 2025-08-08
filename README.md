# SB Sync - Django Data Synchronization Package

A robust Django package for data synchronization with PUSH/PULL APIs, featuring JWT authentication, comprehensive logging, performance optimizations, and **multi-tenant, role-based access control** for any Django application.

## 🚀 Features

- **PUSH/PULL API Endpoints**: Bidirectional data synchronization
- **🌐 Web-Based Configuration Interface**: Visual management of permissions and settings
- **📋 Audit Trails**: Complete change history tracking with Django Simple History
- **JWT Authentication**: Secure token-based authentication
- **Multi-Tenant Support**: Organization-based data isolation
- **Role-Based Access Control**: Granular permissions per user role
- **Comprehensive Logging**: Detailed sync operation tracking
- **Performance Optimizations**: Bulk operations and caching
- **Health Monitoring**: Built-in health check endpoints
- **Background Tasks**: Celery integration for maintenance tasks
- **Data Validation**: Automatic model structure validation
- **Error Handling**: Robust error handling and reporting
- **🔄 Auto-Migration System**: Automatic version detection and schema migration

## 📋 Requirements

- Python >= 3.8
- Django >= 3.2, < 5.3 (supports Django 3.2, 4.0, 4.1, 4.2, 5.0, 5.1, 5.2)
- Django REST Framework >= 3.14.0
- PyJWT >= 2.6.0
- Django Simple History >= 3.4.0 (for audit trails)
- Celery (for background tasks)

## 🔧 Django Compatibility

This package is designed to work with a wide range of Django versions:

| Django Version | Status | Support Level |
|----------------|--------|---------------|
| 3.2.x | ✅ Supported | LTS (Long Term Support) |
| 4.0.x | ✅ Supported | Standard |
| 4.1.x | ✅ Supported | Standard |
| 4.2.x | ✅ Supported | LTS (Long Term Support) |
| 5.0.x | ✅ Supported | Standard |
| 5.1.x | ✅ Supported | Standard |
| 5.2.x | ✅ Supported | Standard |
| 5.3.x | ❌ Not yet | Future versions |

**Note**: The package is tested against Django LTS versions and the latest stable releases. For production use, we recommend using Django LTS versions (3.2.x, 4.2.x) for maximum stability.

## 🛠️ Installation

1. Install the package:
```bash
pip install sb-sync
```

2. Add to your Django settings:
```python
INSTALLED_APPS = [
    # ... other apps
    'sb_sync',
]

# Optional settings
SB_SYNC_LOG_DIR = 'logs'  # Directory for sync logs
```

3. Run migrations:
```bash
python manage.py migrate
```

4. Access the web configuration interface:
```bash
# Navigate to: http://your-domain/api/sync/config/
# Login with admin credentials (staff members only)
```

5. Setup audit trails (optional but recommended):
```bash
# Setup Django Simple History for audit trails
python manage.py setup_audit_trails --action setup

# Check audit trails status
python manage.py setup_audit_trails --action check

# Cleanup old audit trail records
python manage.py setup_audit_trails --action cleanup
```

## 🔧 Configuration

### Required Settings

Add to your Django settings:

```python
# JWT Settings
SECRET_KEY = 'your-secret-key'

# Celery Settings (for background tasks)
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Optional: Custom log directory
SB_SYNC_LOG_DIR = 'logs'
```

### Model Discovery Configuration

The package automatically discovers Django models for synchronization with advanced filtering options.

#### Basic Configuration

```python
from sb_sync.config import SyncConfig

# Include specific apps
SyncConfig.set_config('MODEL_DISCOVERY', 'INCLUDE_APPS', ['myapp', 'ecommerce'])

# Exclude specific models
SyncConfig.set_config('MODEL_DISCOVERY', 'EXCLUDE_MODELS', ['myapp.LogModel', 'ecommerce.CacheModel'])

# Enable/disable auto discovery
SyncConfig.set_config('MODEL_DISCOVERY', 'AUTO_DISCOVER_MODELS', True)
```

#### Advanced Configuration Options

##### Model Type Filtering
```python
# Exclude abstract and proxy models
SyncConfig.set_config('MODEL_DISCOVERY', 'EXCLUDE_ABSTRACT_MODELS', True)
SyncConfig.set_config('MODEL_DISCOVERY', 'EXCLUDE_PROXY_MODELS', True)

# Include only concrete models
SyncConfig.set_config('MODEL_DISCOVERY', 'INCLUDE_MODEL_TYPES', ['concrete'])
```

##### Pattern-Based Filtering
```python
# Include models matching patterns
SyncConfig.set_config('MODEL_DISCOVERY', 'INCLUDE_MODEL_PATTERNS', [
    r'^myapp\.',  # All models from myapp
    r'^ecommerce\.Product.*$'  # Product models from ecommerce
])

# Exclude models matching patterns
SyncConfig.set_config('MODEL_DISCOVERY', 'EXCLUDE_MODEL_PATTERNS', [
    r'^.*\.Historical.*$',  # Exclude historical models
    r'^.*\.Log$',           # Exclude log models
    r'^.*\.Cache$',         # Exclude cache models
])
```

##### Field-Based Filtering
```python
# Exclude models with specific fields
SyncConfig.set_config('MODEL_DISCOVERY', 'EXCLUDE_MODELS_WITH_FIELDS', [
    'created_at',  # Exclude models with created_at field
    'updated_at',  # Exclude models with updated_at field
    'deleted_at',  # Exclude soft-delete models
])

# Require models to have specific fields
SyncConfig.set_config('MODEL_DISCOVERY', 'REQUIRE_MODELS_WITH_FIELDS', [
    'id'  # Only include models with 'id' field
])
```

##### App-Specific Exclusions
```python
# Exclude specific models from specific apps
SyncConfig.set_config('MODEL_DISCOVERY', 'APP_SPECIFIC_EXCLUSIONS', {
    'auth': ['Group', 'Permission'],  # Exclude Group and Permission from auth
    'admin': ['LogEntry'],            # Exclude LogEntry from admin
})
```

##### Performance and Caching
```python
# Enable discovery caching
SyncConfig.set_config('MODEL_DISCOVERY', 'ENABLE_DISCOVERY_CACHING', True)
SyncConfig.set_config('MODEL_DISCOVERY', 'DISCOVERY_CACHE_TIMEOUT', 3600)  # 1 hour

# Limit models per app
SyncConfig.set_config('MODEL_DISCOVERY', 'MAX_MODELS_PER_APP', 100)
```

#### Management Command

Use the management command to configure model discovery:

```bash
# List current configuration
python manage.py configure_model_discovery --list-current

# Set include apps
python manage.py configure_model_discovery --set-include-apps myapp ecommerce

# Set exclude patterns
python manage.py configure_model_discovery --set-exclude-patterns ".*Log" ".*Cache"

# Set field-based exclusions
python manage.py configure_model_discovery --set-exclude-fields created_at updated_at

# Test discovery with current settings
python manage.py configure_model_discovery --test-discovery

# Reset to defaults
python manage.py configure_model_discovery --reset-to-defaults
```

### 🔄 Auto-Migration System

The package includes an intelligent auto-migration system that automatically detects version gaps and handles schema migrations gracefully.

#### Features

- **Automatic Version Detection**: Detects current database schema version
- **Schema Change Detection**: Identifies required migrations
- **Data Preservation**: Safely migrates data between versions
- **Graceful Error Handling**: Comprehensive error recovery
- **Rollback Capabilities**: Support for migration rollbacks
- **Management Commands**: Command-line migration control
- **Startup Auto-Migration**: Automatic migration on app startup

#### Migration Scenarios Handled

- **v1.x → v2.x**: Organization-based to Site-based migration
- **Fresh Installations**: New database setup
- **Schema Updates**: Field and table structure changes
- **Data Preservation**: Maintains existing data during migration
- **Error Recovery**: Handles migration failures gracefully

#### Management Commands

```bash
# Check migration status (dry run)
python manage.py auto_migrate --dry-run --verbose

# Force migration (even if not needed)
python manage.py auto_migrate --force

# Verbose migration with detailed output
python manage.py auto_migrate --verbose
```

#### Automatic Startup Migration

The auto-migration system runs automatically when the Django app starts:

```python
# In your Django app's apps.py
class SbSyncConfig(AppConfig):
    def ready(self):
        # Auto-migration runs automatically
        from .migration_utils import setup_auto_migration
        setup_auto_migration()
```

#### Migration Detection

The system detects migration needs by checking:

- Database schema version
- Table structure differences
- Foreign key relationships
- Data integrity requirements

#### Example Migration Flow

```python
# 1. Version Detection
current_version = detector.detect_current_version()  # Returns '1.x', '2.x', or 'fresh'

# 2. Schema Change Detection
schema_changes = detector.detect_schema_changes()  # Identifies required changes

# 3. Migration Execution
if migrator.needs_migration():
    success = migrator.auto_migrate()  # Performs migration
```

#### Error Handling

The auto-migration system includes comprehensive error handling:

- **Database Connection Issues**: Graceful handling of connection failures
- **Schema Conflicts**: Resolution of table structure conflicts
- **Data Integrity**: Validation of migrated data
- **Rollback Support**: Ability to revert failed migrations

#### Configuration

```python
# Disable auto-migration (if needed)
SB_SYNC_AUTO_MIGRATION = False

# Custom migration timeout
SB_SYNC_MIGRATION_TIMEOUT = 300  # 5 minutes

# Enable verbose migration logging
SB_SYNC_MIGRATION_VERBOSE = True
```

#### Model Discovery Settings

##### Basic Settings
- `AUTO_DISCOVER_MODELS`: Enable/disable automatic model discovery
- `INCLUDE_APPS`: List of apps whose models will be synced (empty = all apps)
- `EXCLUDE_MODELS`: List of specific models to exclude from sync
- `INCLUDE_CUSTOM_MODELS`: Include custom models in discovery
- `MODEL_PREFIX`: Prefix for model names
- `MODEL_SUFFIX`: Suffix for model names
- `MODEL_NAMESPACE`: Namespace for model names

##### Advanced Settings
- `EXCLUDE_ABSTRACT_MODELS`: Exclude abstract models
- `EXCLUDE_PROXY_MODELS`: Exclude proxy models
- `EXCLUDE_HISTORICAL_MODELS`: Exclude historical models (simple_history)
- `EXCLUDE_MANAGER_MODELS`: Exclude models with custom managers
- `INCLUDE_MODEL_PATTERNS`: Regex patterns for models to include
- `EXCLUDE_MODEL_PATTERNS`: Regex patterns for models to exclude
- `EXCLUDE_MODELS_WITH_FIELDS`: Field names that will exclude models
- `REQUIRE_MODELS_WITH_FIELDS`: Field names that models must have
- `APP_SPECIFIC_EXCLUSIONS`: Per-app exclusion rules
- `INCLUDE_MODEL_TYPES`: Types of models to include ('concrete', 'abstract', 'proxy')
- `ENABLE_DISCOVERY_CACHING`: Enable discovery result caching
- `DISCOVERY_CACHE_TIMEOUT`: Cache timeout in seconds
- `MAX_MODELS_PER_APP`: Maximum models per app
- `VALIDATE_MODEL_ACCESS`: Validate that models can be accessed
- `CHECK_MODEL_PERMISSIONS`: Check if current user can access models
- `SAFE_DISCOVERY_MODE`: Only discover models that are safe to sync

### URL Configuration

Include the sync URLs in your main `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    # ... other URLs
    path('api/sync/', include('sb_sync.urls')),
]
```

## 🏢 Multi-Tenant Setup

### 1. Create Organizations

```bash
# Create organizations
python manage.py setup_organizations --action create_org --org-name "Acme Corporation" --org-slug acme-corp
python manage.py setup_organizations --action create_org --org-name "Global Retail" --org-slug global-retail
python manage.py setup_organizations --action create_org --org-name "City University" --org-slug city-university
```

### 2. Create Django Groups

```bash
# Create common groups for the application
python manage.py setup_organizations --action create_groups
```

### 3. Add Users to Organizations

```bash
# Add users with specific groups
python manage.py setup_organizations --action add_user --username john_manager --org-slug acme-corp --group-name Managers
python manage.py setup_organizations --action add_user --username mary_sales --org-slug global-retail --group-name Sales
python manage.py setup_organizations --action add_user --username bob_analyst --org-slug city-university --group-name Analysts
```

### 4. Setup Complete Example System

```bash
# Setup all example organizations with groups and permissions
python manage.py setup_organizations --action setup_example
```

## 👥 User Groups and Permissions

### Using Django Groups

The system uses Django's built-in `auth.Group` system for role-based access control. This makes it completely generic and reusable across any Django project.

### Available Groups

The system comes with common groups that can be customized for any domain:

1. **Administrators** - Full access to all data (create, read, update, delete)
2. **Managers** - Can push/pull data, create, update (no delete)
3. **Users** - Can push/pull data, create, update (no delete)
4. **Analysts** - Can only pull data (read-only access)
5. **Sales** - Can push/pull sales-related data
6. **Support** - Can push/pull support-related data
7. **Read Only** - Can only pull data, no push access

### Permission Matrix

| Group | Push | Pull |
|-------|------|------|
| Administrators | ✅ Yes | ✅ Yes |
| Managers | ✅ Yes | ✅ Yes |
| Users | ✅ Yes | ✅ Yes |
| Analysts | ❌ No | ✅ Yes |
| Sales | ✅ Yes | ✅ Yes |
| Support | ✅ Yes | ✅ Yes |
| Read Only | ❌ No | ✅ Yes |

## 🌐 Web-Based Configuration Interface

The SB Sync package includes a comprehensive web-based configuration interface that allows you to manage model permissions, monitor sync operations, and configure model discovery through an intuitive web interface.

### 🚀 Interface Features

- **📊 Dashboard**: Overview statistics and quick actions
- **🔐 Permission Matrix**: Visual matrix interface for managing model permissions
- **🔍 Model Discovery**: Configure which models are available for sync
- **📋 Sync Logs**: View operation history and performance data
- **📈 Performance Metrics**: Interactive charts and detailed metrics

### 🛠️ Accessing the Interface

1. **Navigate to the configuration dashboard**:
   ```
   http://your-domain/api/sync/config/
   ```

2. **Login with admin credentials** (staff members only)

3. **Use the sidebar navigation** to access different sections

### 🔐 Permission Matrix

The permission matrix provides a visual interface for managing model permissions:

- **Visual Matrix**: See all models vs permissions in a matrix format
- **Checkbox Controls**: Grant or revoke permissions with simple checkboxes
- **Organization Selection**: Switch between different organizations
- **Real-time Updates**: Changes are saved immediately via AJAX
- **Bulk Operations**: Select all/deselect all functionality

**URL**: `/api/sync/config/permissions/`

### 🔍 Model Discovery Configuration

Configure which models are discovered and available for sync:

- **Auto Discovery Settings**: Enable/disable automatic model discovery
- **App Filtering**: Include specific apps or all apps
- **Model Exclusion**: Exclude specific models from sync operations
- **Live Preview**: See which models are discovered in real-time

**URL**: `/api/sync/config/model-discovery/`

### 📋 Sync Logs

Monitor sync operations and performance:

- **Operation History**: View all sync operations with timestamps
- **Performance Data**: See processing times and record counts
- **Export Functionality**: Download logs as CSV
- **Auto-refresh**: Logs update automatically every 30 seconds

**URL**: `/api/sync/config/logs/`

### 📈 Performance Metrics

Track system performance and optimization:

- **Performance Charts**: Visual charts showing processing time trends
- **Detailed Metrics**: View batch sizes, memory usage, and query counts
- **Performance Analysis**: Automatic suggestions for optimization
- **Export Data**: Download performance data as CSV

**URL**: `/api/sync/config/metrics/`

### 📋 Audit Trails

Track all changes to sync system with comprehensive audit trails:

- **Complete History**: Track all changes to sync models (create, update, delete)
- **User Attribution**: See who made each change and when
- **Field-Level Changes**: View exactly what fields were modified
- **Filtering & Search**: Filter by model type, user, date range
- **Export Capabilities**: Download audit trail data as CSV
- **Real-time Updates**: Auto-refreshing audit trail display

**URL**: `/api/sync/config/audit-trails/`

### 🎨 Interface Features

- **Modern Design**: Bootstrap 5 with gradient backgrounds and smooth animations
- **Responsive Design**: Works on all devices (mobile, tablet, desktop)
- **Real-time Updates**: AJAX-powered with immediate feedback
- **Security**: Staff-only access with CSRF protection
- **Performance**: Cached data and optimized queries

## 📡 API Endpoints

### Authentication

**POST** `/api/sync/auth/token/`

Get JWT token for authentication:
```json
{
    "username": "your_username",
    "password": "your_password"
}
```

Response (now includes organization info):
```json
{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "dr_smith",
        "email": "dr.smith@citygeneral.com"
    },
    "organizations": [
        {
            "id": 1,
            "name": "Acme Corporation",
            "slug": "acme-corp",
            "group": "Managers"
        }
    ]
}
```

### PUSH API

**POST** `/api/sync/push/`

Push data to Django models (with multi-tenant permissions):

```json
{
    "data": [
        {
            "_model": "myapp.Customer",
            "name": "John Doe",
            "age": 45,
            "department": "SALES",
            "assigned_manager_id": 1
        }
    ]
}
```

Headers:
```
Authorization: Bearer <your_jwt_token>
```

Response:
```json
{
    "status": "success",
    "success_count": 1,
    "error_count": 0,
    "processed_models": {
        "myapp.Customer": {
            "created": 1,
            "updated": 0
        }
    },
    "processing_time": 0.045
}
```

### PULL API

**POST** `/api/sync/pull/`

Pull data from Django models (with role-based filtering):

```json
{
    "models": {
        "myapp.Customer": "2024-01-14T10:00:00Z",
        "myapp.Order": "2024-01-14T10:00:00Z"
    },
    "batch_size": 100
}
```

Headers:
```
Authorization: Bearer <your_jwt_token>
```

Response:
```json
{
    "data": [
        {
            "_model": "myapp.Customer",
            "id": 1,
            "name": "John Doe",
            "age": 45,
            "department": "SALES",
            "assigned_manager_id": 1,
            "organization": 1
        }
    ],
    "metadata": {
        "myapp.Customer": {
            "count": 1,
            "last_sync": "2024-01-15T10:30:00Z",
            "user_last_sync": "2024-01-14T10:00:00Z"
        }
    },
    "batch_info": {
        "batch_size": 100,
        "total_records": 1
    }
}
```

### Performance Monitoring

**GET** `/api/sync/performance/`

Get performance statistics:

```json
{
    "performance_stats": {
        "total_operations": 150,
        "average_processing_time": 0.045,
        "cache_hit_rate": 0.85
    },
    "current_memory_usage": 245.6,
    "cache_stats": {
        "cache_hits": 1200,
        "cache_misses": 200
    },
    "optimization_suggestions": [
        "High memory usage detected. Consider reducing batch sizes."
    ]
}
```

### Health Check

**GET** `/api/sync/health/`

Check system health:

```json
{
    "status": "healthy",
    "timestamp": "2024-01-01T12:00:00Z",
    "checks": {
        "database": "healthy",
        "cache": "healthy",
        "logging": "healthy"
    }
}
```

## 🗄️ Database Models

### Core Models

#### SyncLog

Tracks all synchronization operations:

```python
class SyncLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    operation = models.CharField(max_length=10, choices=[('PUSH', 'Push'), ('PULL', 'Pull')], db_index=True)
    status = models.CharField(max_length=10, choices=[('SUCCESS', 'Success'), ('ERROR', 'Error'), ('WARNING', 'Warning')], db_index=True)
    model_name = models.CharField(max_length=100, blank=True, db_index=True)
    object_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    request_data = models.JSONField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    processing_time = models.FloatField(default=0.0)
```

#### SyncMetadata

Tracks last sync timestamps for models:

```python
class SyncMetadata(models.Model):
    model_name = models.CharField(max_length=100, unique=True, db_index=True)
    last_sync = models.DateTimeField(default=timezone.now, db_index=True)
    total_synced = models.BigIntegerField(default=0)
```

#### PerformanceMetrics

Tracks performance metrics for optimization:

```python
class PerformanceMetrics(models.Model):
    operation_type = models.CharField(max_length=20, db_index=True)
    model_name = models.CharField(max_length=100, db_index=True)
    batch_size = models.IntegerField()
    processing_time = models.FloatField()
    memory_usage = models.FloatField(null=True, blank=True)
    query_count = models.IntegerField()
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
```

### Multi-Tenant Models

#### Organization

Represents organizations, companies, or institutions:

```python
class Organization(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.CharField(max_length=50, unique=True, db_index=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### UserOrganization

Links users to organizations with roles:

```python
class UserOrganization(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, db_index=True)
    role = models.CharField(max_length=50, choices=[
        ('ADMIN', 'Administrator'),
        ('MANAGER', 'Manager'),
        ('USER', 'User'),
        ('ANALYST', 'Analyst'),
        ('SALES', 'Sales'),
        ('SUPPORT', 'Support'),
        ('READ_ONLY', 'Read Only'),
    ], db_index=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### ModelPermission

Defines which models each group can access:

```python
class ModelPermission(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, db_index=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, db_index=True, help_text="Django auth group")
    model_name = models.CharField(max_length=100, db_index=True)
    can_push = models.BooleanField(default=False)
    can_pull = models.BooleanField(default=False)
    filters = models.JSONField(blank=True, null=True)  # Custom filters for data access
```

#### UserSyncMetadata

Tracks last sync timestamps for models per user/organization:

```python
class UserSyncMetadata(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, db_index=True)
    model_name = models.CharField(max_length=100, db_index=True)
    last_sync = models.DateTimeField(default=timezone.now, db_index=True)
    total_synced = models.BigIntegerField(default=0)
```

#### DataFilter

Custom data filters for role-based access:

```python
class DataFilter(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, db_index=True)
    role = models.CharField(max_length=50, db_index=True)
    model_name = models.CharField(max_length=100, db_index=True)
    filter_name = models.CharField(max_length=100)
    filter_condition = models.JSONField()  # e.g., {"field": "department", "operator": "exact", "value": "CARDIOLOGY"}
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

## 🔄 Background Tasks

### Celery Configuration

Add to your project's `__init__.py`:

```python
from .celery import app as celery_app
__all__ = ('celery_app',)
```

### Available Tasks

1. **cleanup_old_sync_logs**: Removes sync logs older than 90 days
2. **generate_sync_report**: Generates daily sync statistics
3. **optimize_database_tables**: Analyzes and optimizes database tables
4. **bulk_sync_operation**: Processes bulk sync operations asynchronously
5. **cache_warmup**: Warms up cache with frequently accessed data
6. **memory_optimization**: Performs garbage collection and cache cleanup
7. **performance_analysis**: Analyzes performance and provides recommendations

### Running Celery

```bash
# Start Celery worker
celery -A your_project worker -l info

# Start Celery beat (for scheduled tasks)
celery -A your_project beat -l info
```

## 🛡️ Security

- **JWT Authentication**: All API endpoints require valid JWT tokens
- **Token Expiration**: Tokens expire after 7 days by default
- **Multi-Tenant Isolation**: Complete data isolation between organizations
- **Role-Based Access Control**: Granular permissions per user role
- **Data Filtering**: Role-specific data access filters
- **User Validation**: All operations are tied to authenticated users
- **Input Validation**: Comprehensive data validation against Django models

## 📊 Monitoring & Logging

### Log Files

Sync operations are logged to `logs/sb_sync.log` with daily rotation and 30-day retention.

### Log Format

```
2024-01-01 12:00:00 - sb_sync - INFO - PUSH request from user john_manager in Acme Corporation: {"data": [...]}
```

### Health Monitoring

Use the health check endpoint to monitor:
- Database connectivity
- Cache functionality
- Log directory accessibility
- Memory usage
- Performance metrics

## ⚡ Performance Optimizations

### Bulk Operations

The package includes optimized bulk operations for high-volume data processing:

```python
from sb_sync.optimizations import BulkOperations

# Bulk create/update with batching
results = BulkOperations.bulk_create_or_update(
    model_class=YourModel,
    data_list=large_dataset,
    batch_size=1000
)
```

### Model Metadata Caching

Model field information is cached for improved performance:

```python
from sb_sync.optimizations import ModelMetadataCache

# Get cached model fields
fields = ModelMetadataCache.get_model_fields('app.ModelName')
```

### Query Optimization

```python
from sb_sync.optimizations import QueryOptimizer

# Get optimized sync logs
logs = QueryOptimizer.get_optimized_sync_logs(user, organization)

# Count queries with decorator
@QueryOptimizer.count_queries
def my_function():
    # Your code here
    pass
```

### Memory Optimization

```python
from sb_sync.optimizations import MemoryOptimizer

# Monitor memory usage
memory_usage = MemoryOptimizer.get_memory_usage()

# Memory monitoring decorator
@MemoryOptimizer.monitor_memory
def my_function():
    # Your code here
    pass
```

### Cache Optimization

```python
from sb_sync.optimizations import CacheOptimizer

# Get or set cache
data = CacheOptimizer.get_or_set_cache('key', lambda: expensive_operation())

# Cache model data
CacheOptimizer.cache_model_data('key', data, timeout=300)
```

## 🔧 Management Commands

### Model Discovery and Default Models

The system automatically discovers all Django models in your application and makes them available for push/pull operations by default. Only specific apps and models are excluded via configuration.

```bash
# Show model discovery summary
python manage.py show_models --action summary

# Show all discovered models
python manage.py show_models --action all

# Show enabled models only
python manage.py show_models --action enabled

# Show default models for push/pull operations
python manage.py show_models --action default

# Show detailed model information
python manage.py show_models --action details --verbose

# Show models from specific app
python manage.py show_models --action enabled --app-label myapp
```

**Default Behavior:**
- ✅ **Auto-discovers all Django models** in your application
- ✅ **`INCLUDE_APPS`**: List of apps whose models will be synced (empty = all apps)
- ✅ **`EXCLUDE_MODELS`**: Models within those included apps that will be excluded
- ✅ **Makes all discovered models available** for push/pull operations
- ✅ **No configuration required** - works out of the box

**Configuration Options:**
- `AUTO_DISCOVER_MODELS`: Enable/disable automatic model discovery
- `INCLUDE_APPS`: List of apps whose models will be synced (empty = all apps)
- `EXCLUDE_MODELS`: Models within included apps that will be excluded from sync
- `INCLUDE_CUSTOM_MODELS`: Include custom models from your apps

### Cleanup Sync Logs

```bash
python manage.py cleanup_sync_logs
```

### Performance Optimization

```bash
# Analyze performance
python manage.py optimize_performance --action analyze --days 7

# Optimize performance
python manage.py optimize_performance --action optimize --force

# Cleanup old data
python manage.py optimize_performance --action cleanup

# Monitor resources
python manage.py optimize_performance --action monitor
```

### Configuration Management

```bash
# Show current configuration
python manage.py manage_config --action show

# Export configuration
python manage.py manage_config --action export --file config.json --format json

# Import configuration
python manage.py manage_config --action import --file config.json --format json

# Validate configuration
python manage.py manage_config --action validate

# Get configuration summary
python manage.py manage_config --action summary

# Reset to defaults
python manage.py manage_config --action reset --force
```

### Organization Setup

```bash
# Create organization
python manage.py setup_organizations --action create_org --org-name "Acme Corporation" --org-slug acme-corp

# Add user to organization
python manage.py setup_organizations --action add_user --username john_manager --org-slug acme-corp --group-name Managers

# Set permissions from config file
python manage.py setup_organizations --action set_permissions --org-slug acme-corp --config-file permissions.json

# Setup complete example system
python manage.py setup_organizations --action setup_example
```

### Audit Trails Management

```bash
# Setup audit trails for all sync models
python manage.py setup_audit_trails --action setup

# Check audit trails status
python manage.py setup_audit_trails --action check

# Cleanup old audit trail records
python manage.py setup_audit_trails --action cleanup

# Setup audit trails for specific model
python manage.py setup_audit_trails --action setup --model sb_sync.Organization

# Check specific model audit trails
python manage.py setup_audit_trails --action check --model sb_sync.ModelPermission
```

### Dynamic Permission Configuration

```bash
# Discover all models in your project
python manage.py dynamic_permissions --action discover

# Generate permission configuration
python manage.py dynamic_permissions --action generate --org-slug acme-corp --permission-template read_write

# Apply permission configuration
python manage.py dynamic_permissions --action apply --org-slug acme-corp --config-file permissions.json

# Export current permissions
python manage.py dynamic_permissions --action export --org-slug acme-corp --output-file current_permissions.json

# Validate configuration file
python manage.py dynamic_permissions --action validate --config-file permissions.json

# Show available templates
python manage.py dynamic_permissions --action template
```

## 🧪 Testing

### Example Usage

```python
import requests
import json

# Get authentication token
auth_response = requests.post('http://localhost:8000/api/sync/auth/token/', {
    'username': 'dr_smith',
    'password': 'password'
})
token = auth_response.json()['token']

# Push data (with multi-tenant permissions)
headers = {'Authorization': f'Bearer {token}'}
push_data = {
    'data': [
        {
            '_model': 'myapp.Customer',
            'name': 'John Doe',
            'department': 'SALES',
            'assigned_manager_id': 1
        }
    ]
}
response = requests.post('http://localhost:8000/api/sync/push/', 
                        json=push_data, headers=headers)
print(response.json())

# Pull data (with role-based filtering)
pull_data = {
    'models': {
        'myapp.Customer': '2024-01-14T10:00:00Z',
        'myapp.Order': '2024-01-14T10:00:00Z'
    },
    'batch_size': 100
}
response = requests.post('http://localhost:8000/api/sync/pull/', 
                        json=pull_data, headers=headers)
print(response.json())
```

## 📝 Error Handling

The package provides comprehensive error handling:

- **Validation Errors**: Detailed field validation messages
- **Model Errors**: Clear error messages for missing or invalid models
- **Authentication Errors**: Proper JWT token validation
- **Permission Errors**: Multi-tenant and role-based access control errors
- **Database Errors**: Transaction rollback on errors
- **Partial Success Handling**: Graceful handling of partial failures

## 🏢 Multi-Tenant Use Case

### Scenario: Multiple Organizations

The system supports complex multi-tenant scenarios with multiple organizations:

```python
# Organization A (Acme Corp) - Manager Smith
POST /api/sync/push/
{
    "data": [
        {
            "_model": "myapp.Customer",
            "name": "John Doe",
            "department": "SALES",
            "assigned_manager_id": 1
        }
    ]
}
# ✅ Success - Manager Smith has permission

# Organization B (Global Retail) - Sales Wilson  
POST /api/sync/pull/
{
    "models": {"myapp.Customer": "2024-01-14T10:00:00Z"}
}
# ✅ Success - Sales Wilson gets only their assigned customers

# Organization C (City University) - Analyst Garcia
POST /api/sync/push/
{
    "data": [
        {
            "_model": "myapp.Report",
            "customer_id": 5,
            "report_type": "ANALYSIS",
            "results": "Positive"
        }
    ]
}
# ✅ Success - Analyst has permission for reports
```

### Key Benefits for Multi-Tenant Applications:

1. **🔒 Data Isolation**: Each organization only sees their own data
2. **👥 Role-Based Access**: Different roles have appropriate permissions
3. **📊 Granular Control**: Filter by department, assigned staff, etc.
4. **🔄 Per-User Sync Tracking**: Each user has their own sync history
5. **⚡ Performance**: Optimized for high-volume data processing
6. **🛡️ Security**: Meets enterprise data privacy requirements

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
- Check the health endpoint: `/api/sync/health/`
- Review sync logs in `logs/sb_sync.log`
- Monitor Celery task logs for background operations
- Check performance metrics: `/api/sync/performance/`

## �� Changelog

### **v2.0.0** (Latest) - 2025-08-07
**🚀 Major Release: Django Sites Integration & UI Improvements**
- **🔄 Architecture Change**: Replaced custom Organization model with Django's built-in Sites framework
- **🎨 UI Enhancement**: Updated all interfaces to use user-friendly "Organization" terminology
- **🔧 Technical Improvements**: 
  - Renamed `UserOrganization` to `UserSite` for better Django Sites integration
  - Updated all models to use `site` instead of `organization` fields
  - Simplified permission system with push/pull permissions only
  - Enhanced admin interface with proper field mappings
  - Fixed all indentation and configuration errors
- **📱 User Experience**: 
  - "Organization Selector" instead of "Site Selector" in permission matrix
  - "Organizations Overview" in configuration dashboard
  - Professional admin interface with organization actions
  - Consistent terminology across all interfaces
- **⚡ Performance**: 
  - Optimized database queries with proper select_related
  - Enhanced caching mechanisms
  - Improved bulk operations for permissions
- **🔒 Security**: 
  - Maintained all security features with Django Sites
  - Enhanced permission checking with proper site isolation
- **📊 Monitoring**: 
  - Added comprehensive audit trails
  - Enhanced logging and error handling
  - Improved performance metrics tracking

### **v1.9.2** - 2025-08-06
**🔧 Permission System Fixes**
- **Fixed**: Pull API permission issues causing "you don't have permission" errors
- **Fixed**: Removed invalid `is_active` filter from ModelPermission queries
- **Added**: Proper superuser handling in permission system
- **Enhanced**: Group resolution for admin users and superusers
- **Added**: Comprehensive debugging logs for permission troubleshooting
- **Improved**: Error handling and logging for permission checks
- **Fixed**: Admin users with proper group assignments now have correct pull/push permissions

### **v1.9.1** - 2025-08-06
**🎨 Improved Permission Matrix UI**
- **Enhanced**: Split push and pull permissions into separate columns
- **Added**: Individual "select all" checkboxes for push and pull permissions per group
- **Improved**: Better visual organization with dedicated columns for each permission type
- **Enhanced**: More intuitive interface for permission management
- **Updated**: JavaScript logic to handle separate column states independently
- **Improved**: User experience with clearer permission type separation
- **Maintained**: All existing functionality (auto-save, debouncing, bulk operations)

### **v1.9.0** - 2025-08-06
**🔧 Simplified Permission System**
- **Removed**: Delete, read, create, and update permissions from the system
- **Simplified**: Permission system now only includes push and pull permissions
- **Updated**: ModelPermission model to only have can_push and can_pull fields
- **Updated**: Permission matrix interface to show only push/pull permissions
- **Updated**: Admin interface to reflect simplified permission structure
- **Updated**: All views and templates to work with simplified permissions
- **Added**: Database migration to remove old permission fields
- **Improved**: Cleaner and more focused permission management

### **v1.8.0** - 2025-08-06
**🔧 Template Tag Fix & Version Display**
- **Fixed**: Template tag loading error for get_version in base.html
- **Added**: {% load sb_sync_extras %} to properly load custom template tags
- **Fixed**: Version display in configuration interface sidebar
- **Improved**: Template error handling and tag registration
- **Tested**: Template rendering without errors

### **v1.7.0** - 2025-08-06
**🚀 Persistent Configuration Storage**
- **Added**: SyncConfiguration model for persistent database storage
- **Implemented**: Database-backed configuration with JSONField support
- **Added**: History tracking for configuration changes with Django Simple History
- **Enhanced**: get_config() and set_config() methods with database fallback
- **Fixed**: Configuration persistence across server restarts
- **Added**: Graceful fallback to in-memory storage if database unavailable
- **Improved**: Model discovery with persistent INCLUDE_APPS configuration
- **Added**: Proper indexing and constraints for configuration table
- **Tested**: Configuration persistence and model discovery functionality

### **v1.6.1** - 2025-08-06
**🔧 Template Tag Fix & Bug Resolution**
- **Fixed**: AttributeError in permission matrix template ('bool' object has no attribute 'get')
- **Enhanced**: lookup filter in sb_sync_extras.py to handle multiple data types
- **Added**: Support for boolean values, dictionary-like objects, lists, and object attributes
- **Improved**: Error handling for template tag operations
- **Tested**: Permission matrix endpoint accessibility and functionality

### **v1.6.0** - 2025-08-06
**🔧 Model Discovery Logic Enhancement**
- **Fixed**: Model discovery logic to exclude Django built-in apps when INCLUDE_APPS is empty
- **Fixed**: Excluded sb-sync app itself and its dependencies from model discovery
- **Enhanced**: get_all_models() and is_model_enabled() methods with proper exclusion logic
- **Added**: Comprehensive list of excluded apps (Django built-ins, sb-sync, dependencies)
- **Fixed**: Missing dependencies (psutil, django-simple-history) installation issues
- **Updated**: URL configuration to properly expose model discovery endpoint
- **Tested**: Model discovery logic with custom test apps
- **Improved**: Server startup reliability and dependency management

### **v1.5.3** - 2025-08-06
**🔧 Package Installation Fixes**
- **Fixed**: Resolved pip installation issues with proper package structure
- **Fixed**: Moved all files to `sb_sync/` directory for correct Python package layout
- **Fixed**: Cleaned up excessive dependencies in `setup.py`
- **Fixed**: Removed invalid entry points that caused installation errors
- **Added**: `MANIFEST.in` file for proper package data inclusion
- **Updated**: Project URLs to point to correct GitHub repository
- **Tested**: Package installation and import functionality

### **v1.5.2** - 2025-08-06
**🔧 Django 5.2.x Compatibility & Installation Fixes**
- **Added**: Support for Django 5.2.x
- **Updated**: Django version constraint from `<5.1` to `<5.3`
- **Added**: Django 5.1 and 5.2 framework classifiers
- **Fixed**: Package structure for proper pip installation
- **Added**: Comprehensive Django compatibility documentation

### **v1.5.1** - 2025-08-06
**🔧 Django Compatibility Enhancement**
- **Added**: Support for Django 5.1.x and 5.2.x
- **Updated**: Django version requirements to support broader range
- **Added**: Django compatibility table in documentation
- **Fixed**: Version constraints in setup.py

### **v1.5.0** - 2024-01-XX
**🌐 Web-Based Configuration Interface & Audit Trails**
- **Added**: Complete web-based configuration interface with dashboard
- **Added**: Visual permission matrix for model permissions management
- **Added**: Model discovery configuration UI
- **Added**: Sync logs viewer with real-time updates
- **Added**: Performance metrics visualization with charts
- **Added**: Django Simple History integration for comprehensive audit trails
- **Added**: Audit trails management command (`setup_audit_trails`)
- **Added**: Custom template tags for enhanced UI functionality
- **Enhanced**: Admin interface with historical records support
- **Updated**: All sync models with audit trail capabilities
- **Added**: Bootstrap 5, Font Awesome, and Chart.js for modern UI

### **v1.4.0** - 2024-01-XX
**🧹 Package Streamlining & Code Organization**
- **Removed**: Dynamic data sources functionality for focused scope
- **Improved**: Code organization and structure
- **Enhanced**: Documentation clarity and completeness
- **Streamlined**: Package for Django model synchronization focus
- **Cleaned**: Codebase organization and removed unused components

### **v1.3.0** - 2024-01-XX
**🔍 Model Discovery & Configuration Enhancement**
- **Added**: Include-based model discovery system
- **Enhanced**: Configuration system with better flexibility
- **Improved**: Test coverage across all components
- **Updated**: Comprehensive documentation cleanup
- **Added**: Model introspection capabilities
- **Enhanced**: Error handling and validation

### **v1.2.0** - 2024-01-XX
**🚀 Performance & Multi-Tenant Features**
- **Added**: Multi-tenant support with organization-based isolation
- **Added**: Role-based access control (RBAC)
- **Enhanced**: Performance optimizations with bulk operations
- **Added**: Comprehensive health monitoring
- **Improved**: Background task processing with Celery
- **Added**: Advanced caching mechanisms

### **v1.1.0** - 2024-01-XX
**⚡ Performance & Error Handling**
- **Enhanced**: Configuration system flexibility
- **Added**: Performance optimizations for large datasets
- **Improved**: Error handling and reporting mechanisms
- **Added**: Advanced logging capabilities
- **Enhanced**: Data validation processes

### **v1.0.0** - 2024-01-XX
**🎉 Initial Release**
- **Added**: PUSH/PULL API endpoints for bidirectional sync
- **Added**: JWT authentication system
- **Added**: Comprehensive logging infrastructure
- **Added**: Basic model synchronization capabilities
- **Added**: Health check endpoints
- **Added**: Initial documentation and setup guides

---

## 🔄 Migration Guide

### **Upgrading to v1.5.x**

If you're upgrading from an earlier version:

1. **Update your installation**:
   ```bash
   pip install --upgrade sb-sync
   ```

2. **Run new migrations**:
   ```bash
   python manage.py migrate
   ```

3. **Setup audit trails** (recommended):
   ```bash
   python manage.py setup_audit_trails --action setup
   ```

4. **Access new web interface**:
   - Navigate to: `http://your-domain/api/sync/config/`
   - Login with admin/staff credentials

### **Breaking Changes**

- **v1.4.0**: Removed dynamic data sources - migrate to model-based sync
- **v1.5.0**: Added new dependencies (`django-simple-history`) - run `pip install --upgrade sb-sync`

### **New Features Guide**

- **Web Interface**: Access at `/api/sync/config/` for visual management
- **Audit Trails**: Use management command to setup and manage historical records
- **Django 5.2.x**: Full compatibility with latest Django versions 