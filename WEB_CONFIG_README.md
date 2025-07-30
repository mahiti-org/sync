# 🌐 Web-Based Configuration Interface

The SB Sync package now includes a comprehensive web-based configuration interface that allows you to manage model permissions, monitor sync operations, and configure model discovery through an intuitive web interface.

## 🚀 Features

### 📊 Dashboard
- **Overview Statistics**: View total models, organizations, and user groups
- **Quick Actions**: Easy access to all configuration sections
- **Recent Activity**: Monitor system status and recent operations

### 🔐 Permission Matrix
- **Visual Matrix Interface**: See all models vs permissions in a matrix format
- **Checkbox Controls**: Grant or revoke permissions with simple checkboxes
- **Organization Selection**: Switch between different organizations
- **Real-time Updates**: Changes are saved immediately via AJAX
- **Bulk Operations**: Select all/deselect all functionality

### 🔍 Model Discovery Configuration
- **Auto Discovery Settings**: Enable/disable automatic model discovery
- **App Filtering**: Include specific apps or all apps
- **Model Exclusion**: Exclude specific models from sync operations
- **Live Preview**: See which models are discovered in real-time

### 📋 Sync Logs
- **Operation History**: View all sync operations with timestamps
- **Performance Data**: See processing times and record counts
- **Export Functionality**: Download logs as CSV
- **Auto-refresh**: Logs update automatically every 30 seconds

### 📈 Performance Metrics
- **Performance Charts**: Visual charts showing processing time trends
- **Detailed Metrics**: View batch sizes, memory usage, and query counts
- **Performance Analysis**: Automatic suggestions for optimization
- **Export Data**: Download performance data as CSV

## 🛠️ Installation & Setup

### 1. Add to Django Settings

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    'sb_sync',
]

# Optional: Custom log directory
SB_SYNC_LOG_DIR = 'logs'
```

### 2. Include URLs

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    # ... other URLs
    path('api/sync/', include('sb_sync.urls')),
]
```

### 3. Run Migrations

```bash
python manage.py migrate
```

### 4. Create Organizations and Groups

```bash
# Create organizations
python manage.py setup_organizations --action create_org --org-name "My Company" --org-slug my-company

# Create groups
python manage.py setup_organizations --action create_groups
```

## 🎯 Usage Guide

### Accessing the Interface

1. **Navigate to the configuration dashboard**:
   ```
   http://your-domain/api/sync/config/
   ```

2. **Login with admin credentials** (staff members only)

### Managing Permissions

1. **Go to Permission Matrix**:
   ```
   http://your-domain/api/sync/config/permissions/
   ```

2. **Select Organization**: Choose the organization you want to configure

3. **Configure Permissions**:
   - Check/uncheck boxes to grant/revoke permissions
   - Permissions include: Push, Pull, Create, Update, Delete, Read
   - Changes are saved automatically

4. **Use Bulk Operations**:
   - "Select All" to grant all permissions
   - "Deselect All" to revoke all permissions
   - "Save Changes" to apply pending changes

### Configuring Model Discovery

1. **Go to Model Discovery**:
   ```
   http://your-domain/api/sync/config/model-discovery/
   ```

2. **Configure Settings**:
   - Enable/disable auto discovery
   - Select apps to include
   - Exclude specific models
   - Save configuration

### Monitoring Operations

1. **View Sync Logs**:
   ```
   http://your-domain/api/sync/config/logs/
   ```

2. **Check Performance Metrics**:
   ```
   http://your-domain/api/sync/config/metrics/
   ```

## 🔧 Configuration Options

### Permission Types

- **Push**: Allow pushing data to this model
- **Pull**: Allow pulling data from this model
- **Create**: Allow creating new records
- **Update**: Allow updating existing records
- **Delete**: Allow deleting records
- **Read**: Allow reading/viewing records

### Model Discovery Settings

- **Auto Discover Models**: Automatically discover models from Django apps
- **Include Custom Models**: Include custom models from your applications
- **Include Apps**: Specify which apps to include (empty = all apps)
- **Exclude Models**: Specify models to exclude from sync operations

## 🎨 Interface Features

### Modern Design
- **Bootstrap 5**: Modern, responsive design
- **Font Awesome Icons**: Beautiful, consistent icons
- **Gradient Backgrounds**: Professional visual appeal
- **Hover Effects**: Interactive elements with smooth transitions

### User Experience
- **Real-time Updates**: Changes saved immediately
- **Status Messages**: Clear feedback for all actions
- **Loading Indicators**: Visual feedback during operations
- **Auto-refresh**: Data updates automatically

### Responsive Design
- **Mobile Friendly**: Works on all device sizes
- **Sidebar Navigation**: Easy navigation between sections
- **Table Responsiveness**: Horizontal scrolling for large tables
- **Touch-friendly**: Optimized for touch devices

## 🔒 Security

### Access Control
- **Staff Members Only**: Only Django staff members can access
- **CSRF Protection**: All forms protected against CSRF attacks
- **Permission Validation**: Server-side validation of all changes

### Data Protection
- **Organization Isolation**: Data is isolated by organization
- **Audit Trail**: All changes are logged
- **Input Validation**: All inputs are validated server-side

## 📊 Performance

### Optimization Features
- **Caching**: Model metadata is cached for performance
- **Bulk Operations**: Efficient bulk permission updates
- **Lazy Loading**: Data loaded only when needed
- **Query Optimization**: Optimized database queries

### Monitoring
- **Performance Metrics**: Track processing times and throughput
- **Memory Usage**: Monitor memory consumption
- **Query Counts**: Track database query efficiency
- **Error Tracking**: Comprehensive error logging

## 🚀 Advanced Features

### AJAX Integration
- **Real-time Updates**: No page refreshes needed
- **Bulk Operations**: Efficient mass updates
- **Error Handling**: Graceful error handling with user feedback

### Export Functionality
- **CSV Export**: Download logs and metrics as CSV
- **Chart.js Integration**: Interactive performance charts
- **Data Visualization**: Visual representation of performance data

### Customization
- **Template System**: Easy to customize templates
- **CSS Customization**: Modify styles as needed
- **JavaScript Extensions**: Add custom functionality

## 🔧 Troubleshooting

### Common Issues

1. **Permission Denied**:
   - Ensure user is a staff member
   - Check Django admin permissions

2. **No Models Discovered**:
   - Check model discovery configuration
   - Verify apps are properly installed

3. **Changes Not Saving**:
   - Check browser console for JavaScript errors
   - Verify CSRF token is present

4. **Performance Issues**:
   - Check database indexes
   - Monitor memory usage
   - Review query optimization

### Debug Mode

Enable Django debug mode for detailed error messages:

```python
# settings.py
DEBUG = True
```

## 📝 API Endpoints

The web interface uses these API endpoints:

- `GET /api/sync/config/` - Dashboard
- `GET /api/sync/config/permissions/` - Permission matrix
- `POST /api/sync/config/permissions/update/` - Update single permission
- `POST /api/sync/config/permissions/bulk-update/` - Bulk update permissions
- `GET /api/sync/config/model-discovery/` - Model discovery config
- `GET /api/sync/config/logs/` - Sync logs
- `GET /api/sync/config/metrics/` - Performance metrics

## 🎉 Benefits

### For Administrators
- **Easy Management**: No need to edit configuration files
- **Visual Interface**: Intuitive checkbox-based permissions
- **Real-time Monitoring**: Live view of sync operations
- **Bulk Operations**: Efficient mass updates

### For Developers
- **RESTful API**: Clean, consistent API design
- **Extensible**: Easy to add new features
- **Well-documented**: Clear code structure and comments
- **Testable**: Comprehensive test coverage

### For Users
- **User-friendly**: Intuitive interface design
- **Responsive**: Works on all devices
- **Fast**: Optimized for performance
- **Reliable**: Robust error handling

The web-based configuration interface provides a powerful, user-friendly way to manage your SB Sync system without needing to edit configuration files or use command-line tools. 