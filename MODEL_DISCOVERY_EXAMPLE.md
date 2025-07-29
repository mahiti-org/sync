# 🔍 Model Discovery Configuration Examples

This document shows how to configure model discovery using the **include-based approach** where you specify which apps to include and only exclude specific models that shouldn't be synced.

## 🎯 Overview

The new approach is much simpler and more intuitive:

- ✅ **`INCLUDE_APPS`**: List of apps whose models will be synced
- ✅ **`EXCLUDE_MODELS`**: Models within those included apps that will be excluded
- ✅ **All models from included apps** are discovered unless explicitly excluded
- ✅ **No complex exclusion lists** needed

## 📋 Configuration Examples

### 1. Default Configuration (All Apps)

```python
# config.py or settings.py
MODEL_DISCOVERY = {
    'AUTO_DISCOVER_MODELS': True,
    'INCLUDE_APPS': [
        # Empty list = include all apps
    ],
    'EXCLUDE_MODELS': [
        # Models within included apps that will be excluded from sync
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
}
```

**Result:** All models from all apps are discovered and available for sync, except the excluded ones.

### 2. Specific Apps Only

```python
MODEL_DISCOVERY = {
    'AUTO_DISCOVER_MODELS': True,
    'INCLUDE_APPS': [
        'myapp',
        'healthcare',
        'ecommerce',
    ],
    'EXCLUDE_MODELS': [
        'sb_sync.SyncLog',
        'sb_sync.SyncMetadata',
        'myapp.InternalModel',  # Exclude specific model from myapp
        'healthcare.SensitiveData',  # Exclude specific model from healthcare
    ],
    'INCLUDE_CUSTOM_MODELS': True,
}
```

**Result:** All models from `myapp`, `healthcare`, and `ecommerce` are discovered and available for sync, except the excluded ones.

### 3. Healthcare Application

```python
MODEL_DISCOVERY = {
    'AUTO_DISCOVER_MODELS': True,
    'INCLUDE_APPS': [
        'healthcare',
        'patients',
        'appointments',
        'prescriptions',
    ],
    'EXCLUDE_MODELS': [
        'sb_sync.SyncLog',
        'sb_sync.SyncMetadata',
        'healthcare.InternalAuditLog',  # Exclude audit logs from healthcare app
        'patients.SensitiveData',        # Exclude sensitive data from patients app
        'appointments.InternalNotes',    # Exclude internal notes from appointments app
    ],
    'INCLUDE_CUSTOM_MODELS': True,
}
```

**Result:** All models from `healthcare`, `patients`, `appointments`, and `prescriptions` apps are available for sync, except the excluded ones.

### 4. E-commerce Application

```python
MODEL_DISCOVERY = {
    'AUTO_DISCOVER_MODELS': True,
    'INCLUDE_APPS': [
        'products',
        'orders',
        'customers',
        'inventory',
        'shipping',
    ],
    'EXCLUDE_MODELS': [
        'sb_sync.SyncLog',
        'sb_sync.SyncMetadata',
        'orders.PaymentInfo',     # Exclude payment data from orders app
        'customers.PasswordHash',  # Exclude sensitive data from customers app
        'inventory.InternalStock', # Exclude internal data from inventory app
        'products.InternalPricing', # Exclude internal pricing from products app
    ],
    'INCLUDE_CUSTOM_MODELS': True,
}
```

**Result:** All models from `products`, `orders`, `customers`, `inventory`, and `shipping` apps are available for sync, except the excluded ones.

## 🚀 Management Commands

### Check Current Configuration

```bash
# Show model discovery summary
python manage.py show_models --action summary

# Output:
# 📊 Model Discovery Summary
# ==================================================
# 🔍 Total Models Discovered: 25
# ✅ Enabled Models: 22
# ❌ Excluded Models: 3
# ⚙️  Auto Discovery: Enabled
# 📦 Include Apps Count: 0 (All apps included)
# 🚫 Exclude Models Count: 8
```

### Show All Discovered Models

```bash
# Show all models
python manage.py show_models --action all

# Output:
# 📋 All Discovered Models
# ==================================================
# ✅ myapp.Product
# ✅ myapp.Customer
# ✅ myapp.Order
# ✅ healthcare.Patient
# ✅ healthcare.Appointment
# ❌ sb_sync.SyncLog (excluded)
# ❌ sb_sync.SyncMetadata (excluded)
```

### Show Enabled Models Only

```bash
# Show only enabled models
python manage.py show_models --action enabled

# Output:
# ✅ Enabled Models
# ==================================================
# ✅ myapp.Product
# ✅ myapp.Customer
# ✅ myapp.Order
# ✅ healthcare.Patient
# ✅ healthcare.Appointment
```

### Show Default Models for Push/Pull

```bash
# Show default models for sync operations
python manage.py show_models --action default

# Output:
# 🎯 Default Models for Push/Pull Operations
# ==================================================
# ✅ myapp.Product
# ✅ myapp.Customer
# ✅ myapp.Order
# ✅ healthcare.Patient
# ✅ healthcare.Appointment
```

## 🔧 Configuration Options

### INCLUDE_APPS
- **Empty list**: Include all apps (default behavior)
- **Specific apps**: Only include models from listed apps
- **Example**: `['myapp', 'healthcare']` - only sync models from these apps

### EXCLUDE_MODELS
- **Models within included apps**: Only exclude specific models from the included apps
- **Internal models**: Exclude audit logs, sensitive data, etc.
- **Example**: `['sb_sync.SyncLog', 'myapp.InternalModel', 'healthcare.SensitiveData']`

### AUTO_DISCOVER_MODELS
- **True**: Enable automatic model discovery (default)
- **False**: Disable automatic discovery

### INCLUDE_CUSTOM_MODELS
- **True**: Include custom models from your apps (default)
- **False**: Exclude custom models

## 🎯 Benefits of Include-Based Approach

### 1. **Simpler Configuration**
```python
# Before (exclude-based)
'EXCLUDE_APPS': [
    'admin', 'auth', 'sessions', 'contenttypes', 'sites',
    'flatpages', 'redirects', 'sitemaps', 'messages',
    'staticfiles', 'humanize', 'django.contrib.admin',
    'django.contrib.auth', 'django.contrib.contenttypes',
    # ... many more exclusions
]

# After (include-based)
'INCLUDE_APPS': [
    'myapp', 'healthcare', 'ecommerce'
]
'EXCLUDE_MODELS': [
    'sb_sync.SyncLog', 'myapp.InternalModel', 'healthcare.SensitiveData'
]
```

### 2. **More Intuitive**
- ✅ **Include apps** whose models you want to sync
- ✅ **Exclude specific models** within those apps that shouldn't be synced
- ✅ **No complex exclusion lists** needed
- ✅ **Clear and simple** configuration

### 3. **Flexible and Scalable**
- ✅ **Easy to add new apps** - just add to `INCLUDE_APPS`
- ✅ **Easy to exclude specific models** - just add to `EXCLUDE_MODELS`
- ✅ **Works with any Django project** structure
- ✅ **No maintenance of exclusion lists**

### 4. **Production Ready**
- ✅ **Secure by default** - only sync what you explicitly include
- ✅ **Performance optimized** - only discover included apps
- ✅ **Easy to audit** - clear list of what's being synced
- ✅ **Easy to maintain** - simple configuration

## 🔄 Migration from Exclude-Based

If you were using the old exclude-based approach:

### Old Configuration (Exclude-Based)
```python
'EXCLUDE_APPS': ['admin', 'auth', 'sessions', ...],
'EXCLUDE_MODELS': ['auth.User', 'auth.Group', ...],
```

### New Configuration (Include-Based)
```python
'INCLUDE_APPS': [
    'myapp', 'healthcare', 'ecommerce'  # Apps whose models will be synced
],
'EXCLUDE_MODELS': [
    'sb_sync.SyncLog', 'sb_sync.SyncMetadata',  # Models within included apps to exclude
    'myapp.InternalModel', 'healthcare.SensitiveData'
],
```

## 🎉 Result

The new **include-based approach** makes model discovery much simpler and more intuitive:

- ✅ **`INCLUDE_APPS`**: List of apps whose models will be synced
- ✅ **`EXCLUDE_MODELS`**: Models within those included apps that will be excluded
- ✅ **All models from included apps** are discovered unless explicitly excluded
- ✅ **No complex configuration** required
- ✅ **Works with any Django project** out of the box

This approach is much more user-friendly and requires minimal configuration! 🚀 