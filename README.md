# SB Sync - Django Data Synchronization Package

A robust Django package for data synchronization with PUSH/PULL APIs, featuring JWT authentication, comprehensive logging, performance optimizations, and **multi-tenant, role-based access control**.

## 🚀 Features

- **PUSH/PULL API Endpoints**: Bidirectional data synchronization
- **JWT Authentication**: Secure token-based authentication
- **Multi-Tenant Support**: Organization-based data isolation
- **Role-Based Access Control**: Granular permissions per user role
- **Comprehensive Logging**: Detailed sync operation tracking
- **Performance Optimizations**: Bulk operations and caching
- **Health Monitoring**: Built-in health check endpoints
- **Background Tasks**: Celery integration for maintenance tasks
- **Data Validation**: Automatic model structure validation
- **Error Handling**: Robust error handling and reporting

## 📋 Requirements

- Python >= 3.8
- Django >= 3.2
- Django REST Framework >= 3.14.0
- PyJWT >= 2.6.0
- Celery (for background tasks)

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

### URL Configuration

Include the sync URLs in your main `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    # ... other URLs
    path('api/sync/', include('sb_sync.urls')),
]
```

## 🏥 Multi-Tenant Setup

### 1. Create Organizations

```bash
# Create healthcare organizations
python manage.py setup_organizations --action create_org --org-name "City General Hospital" --org-slug city-general
python manage.py setup_organizations --action create_org --org-name "Riverside Medical Center" --org-slug riverside-medical
python manage.py setup_organizations --action create_org --org-name "Community Health Clinic" --org-slug community-health
```

### 2. Add Users to Organizations

```bash
# Add users with specific roles
python manage.py setup_organizations --action add_user --username dr_smith --org-slug city-general --role DOCTOR
python manage.py setup_organizations --action add_user --username nurse_wilson --org-slug riverside-medical --role NURSE
python manage.py setup_organizations --action add_user --username lab_tech_garcia --org-slug community-health --role LAB_TECH
```

### 3. Setup Complete Healthcare System

```bash
# Setup all healthcare organizations with permissions
python manage.py setup_organizations --action setup_healthcare
```

## 👥 User Roles and Permissions

### Available Roles

1. **ADMIN** - Full access to all data (create, read, update, delete)
2. **DOCTOR** - Can push/pull patient data, treatments (no delete)
3. **NURSE** - Can push/pull patient visits, treatments (limited access)
4. **LAB_TECH** - Can push/pull lab investigations only
5. **PHARMACIST** - Can push/pull medicine disbursed data
6. **READ_ONLY** - Can only pull data, no push access

### Permission Matrix

| Role | Patient | Visit | Treatment | Lab | Medicine | Delete |
|------|---------|-------|-----------|-----|----------|--------|
| ADMIN | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ✅ Yes |
| DOCTOR | ✅ Push/Pull | ✅ Push/Pull | ✅ Push/Pull | ❌ None | ❌ None | ❌ No |
| NURSE | ❌ Read | ✅ Push/Pull | ✅ Push/Pull | ❌ None | ❌ None | ❌ No |
| LAB_TECH | ❌ Read | ❌ Read | ❌ Read | ✅ Push/Pull | ❌ None | ❌ No |
| PHARMACIST | ❌ Read | ❌ Read | ❌ Read | ❌ Read | ✅ Push/Pull | ❌ No |
| READ_ONLY | ✅ Pull | ✅ Pull | ✅ Pull | ✅ Pull | ✅ Pull | ❌ No |

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
            "name": "City General Hospital",
            "slug": "city-general",
            "role": "DOCTOR"
        }
    ]
}
```

### PUSH API

**POST** `/api/sync/push/`

Push data to Django models (now with multi-tenant permissions):

```json
{
    "data": [
        {
            "_model": "healthcare.Patient",
            "name": "John Doe",
            "age": 45,
            "department": "CARDIOLOGY",
            "assigned_doctor_id": 1
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
        "healthcare.Patient": {
            "created": 1,
            "updated": 0
        }
    },
    "processing_time": 0.045
}
```

### PULL API

**POST** `/api/sync/pull/`

Pull data from Django models (now with role-based filtering):

```json
{
    "models": {
        "healthcare.Patient": "2024-01-14T10:00:00Z",
        "healthcare.PatientVisit": "2024-01-14T10:00:00Z"
    },
    "batch_size": 100
}
```

Headers:
```
Authorization: Bearer <your_jwt_token>
```

Response (with role-based filtering):
```json
{
    "data": [
        {
            "_model": "healthcare.Patient",
            "id": 1,
            "name": "John Doe",
            "age": 45,
            "department": "CARDIOLOGY",
            "assigned_doctor_id": 1,
            "organization": 1
        }
    ],
    "metadata": {
        "healthcare.Patient": {
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

Represents hospitals, clinics, or healthcare organizations:

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
        ('DOCTOR', 'Doctor'),
        ('NURSE', 'Nurse'),
        ('LAB_TECH', 'Lab Technician'),
        ('PHARMACIST', 'Pharmacist'),
        ('READ_ONLY', 'Read Only'),
    ], db_index=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### ModelPermission

Defines which models each role can access:

```python
class ModelPermission(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, db_index=True)
    role = models.CharField(max_length=50, db_index=True)
    model_name = models.CharField(max_length=100, db_index=True)
    can_push = models.BooleanField(default=False)
    can_pull = models.BooleanField(default=False)
    can_create = models.BooleanField(default=False)
    can_update = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_read = models.BooleanField(default=True)
    filters = models.JSONField(blank=True, null=True)
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
2024-01-01 12:00:00 - sb_sync - INFO - PUSH request from user dr_smith in City General Hospital: {"data": [...]}
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
python manage.py setup_organizations --action create_org --org-name "Hospital Name" --org-slug hospital-slug

# Add user to organization
python manage.py setup_organizations --action add_user --username username --org-slug hospital-slug --role DOCTOR

# Set permissions from config file
python manage.py setup_organizations --action set_permissions --org-slug hospital-slug --config-file permissions.json

# Setup complete healthcare system
python manage.py setup_organizations --action setup_healthcare
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
            '_model': 'healthcare.Patient',
            'name': 'John Doe',
            'department': 'CARDIOLOGY',
            'assigned_doctor_id': 1
        }
    ]
}
response = requests.post('http://localhost:8000/api/sync/push/', 
                        json=push_data, headers=headers)
print(response.json())

# Pull data (with role-based filtering)
pull_data = {
    'models': {
        'healthcare.Patient': '2024-01-14T10:00:00Z',
        'healthcare.PatientVisit': '2024-01-14T10:00:00Z'
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

## 🏥 Healthcare Use Case

### Scenario: Multiple Hospitals

The system supports complex healthcare scenarios with multiple hospitals:

```python
# Hospital A (City General) - Dr. Smith
POST /api/sync/push/
{
    "data": [
        {
            "_model": "healthcare.Patient",
            "name": "John Doe",
            "department": "CARDIOLOGY",
            "assigned_doctor_id": 1
        }
    ]
}
# ✅ Success - Dr. Smith has permission

# Hospital B (Riverside) - Nurse Wilson  
POST /api/sync/pull/
{
    "models": {"healthcare.Patient": "2024-01-14T10:00:00Z"}
}
# ✅ Success - Nurse Wilson gets only her assigned patients

# Hospital C (Community) - Lab Tech Garcia
POST /api/sync/push/
{
    "data": [
        {
            "_model": "healthcare.LabInvestigation",
            "patient_id": 5,
            "test_type": "BLOOD_TEST",
            "results": "Normal"
        }
    ]
}
# ✅ Success - Lab Tech has permission for lab investigations
```

### Key Benefits for Healthcare:

1. **🔒 Data Isolation**: Each hospital only sees their own data
2. **👥 Role-Based Access**: Different roles have appropriate permissions
3. **📊 Granular Control**: Filter by department, assigned staff, etc.
4. **🔄 Per-User Sync Tracking**: Each user has their own sync history
5. **⚡ Performance**: Optimized for high-volume healthcare data
6. **🛡️ Security**: Meets healthcare data privacy requirements

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

## 🔄 Version History

- **v1.2.0**: Multi-tenant, role-based access control, organization management, healthcare use cases, enhanced performance optimizations, and comprehensive permission system
- **v1.1.0**: Enhanced configuration system, performance optimizations, and improved error handling
- **v1.0.0**: Initial release with PUSH/PULL APIs, JWT authentication, and comprehensive logging 