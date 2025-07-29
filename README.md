# SB Sync - Django Data Synchronization Package

A robust Django package for data synchronization with PUSH/PULL APIs, featuring JWT authentication, comprehensive logging, and performance optimizations.

## 🚀 Features

- **PUSH/PULL API Endpoints**: Bidirectional data synchronization
- **JWT Authentication**: Secure token-based authentication
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

Response:
```json
{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### PUSH API

**POST** `/api/sync/push/`

Push data to Django models:

```json
{
    "data": [
        {
            "_model": "app.ModelName",
            "id": 1,
            "field1": "value1",
            "field2": "value2"
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
    "processed": 1,
    "errors": 0,
    "details": {
        "app.ModelName": {
            "created": 0,
            "updated": 1
        }
    },
    "processing_time": 0.123
}
```

### PULL API

**POST** `/api/sync/pull/`

Pull data from Django models:

```json
{
    "models": ["app.ModelName"],
    "since": "2024-01-01T00:00:00Z",
    "limit": 100
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
            "_model": "app.ModelName",
            "id": 1,
            "field1": "value1",
            "field2": "value2"
        }
    ],
    "metadata": {
        "total_count": 1,
        "has_more": false
    }
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

### SyncLog

Tracks all synchronization operations:

```python
class SyncLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    operation = models.CharField(max_length=10, choices=[('PUSH', 'Pull'), ('PULL', 'Pull')])
    status = models.CharField(max_length=10, choices=[('SUCCESS', 'Success'), ('ERROR', 'Error'), ('WARNING', 'Warning')])
    model_name = models.CharField(max_length=100, blank=True)
    object_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    request_data = models.JSONField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    processing_time = models.FloatField(default=0.0)
```

### SyncMetadata

Tracks last sync timestamps for models:

```python
class SyncMetadata(models.Model):
    model_name = models.CharField(max_length=100, unique=True)
    last_sync = models.DateTimeField(default=timezone.now)
    total_synced = models.BigIntegerField(default=0)
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
- **User Validation**: All operations are tied to authenticated users
- **Input Validation**: Comprehensive data validation against Django models

## 📊 Monitoring & Logging

### Log Files

Sync operations are logged to `logs/sb_sync.log` with daily rotation and 30-day retention.

### Log Format

```
2024-01-01 12:00:00 - sb_sync - INFO - PUSH request from user admin: {"data": [...]}
```

### Health Monitoring

Use the health check endpoint to monitor:
- Database connectivity
- Cache functionality
- Log directory accessibility

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

## 🔧 Management Commands

### Cleanup Sync Logs

```bash
python manage.py cleanup_sync_logs
```

## 🧪 Testing

### Example Usage

```python
import requests
import json

# Get authentication token
auth_response = requests.post('http://localhost:8000/api/sync/auth/token/', {
    'username': 'admin',
    'password': 'password'
})
token = auth_response.json()['token']

# Push data
headers = {'Authorization': f'Bearer {token}'}
push_data = {
    'data': [
        {
            '_model': 'app.User',
            'id': 1,
            'username': 'testuser',
            'email': 'test@example.com'
        }
    ]
}
response = requests.post('http://localhost:8000/api/sync/push/', 
                        json=push_data, headers=headers)
print(response.json())
```

## 📝 Error Handling

The package provides comprehensive error handling:

- **Validation Errors**: Detailed field validation messages
- **Model Errors**: Clear error messages for missing or invalid models
- **Authentication Errors**: Proper JWT token validation
- **Database Errors**: Transaction rollback on errors

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

## 🔄 Version History

- **v1.1.0**: Enhanced configuration system, performance optimizations, and improved error handling
- **v1.0.0**: Initial release with PUSH/PULL APIs, JWT authentication, and comprehensive logging 