# 🔄 Dynamic Permission Configuration Example

This document demonstrates how to use the dynamic permission configuration system to automatically discover and configure permissions for any Django models in your project.

## 🎯 Overview

The dynamic permission configuration system allows you to:

1. **Discover Models**: Automatically find all Django models in your project
2. **Generate Configurations**: Create permission configurations using templates
3. **Apply Permissions**: Set up permissions for organizations and groups
4. **Export/Import**: Save and load permission configurations
5. **Validate**: Ensure configurations are correct before applying

## 🚀 Quick Start

### 1. Discover Your Models

```bash
# Discover all models in your project
python manage.py dynamic_permissions --action discover

# Output example:
# Discovered 15 models:
#   - auth.User
#   - auth.Group
#   - contenttypes.ContentType
#   - sessions.Session
#   - myapp.Product
#   - myapp.Customer
#   - myapp.Order
#   - myapp.Invoice
#   - healthcare.Patient
#   - healthcare.Appointment
#   - healthcare.Prescription
```

### 2. Generate Permission Configuration

```bash
# Generate configuration for all models
python manage.py dynamic_permissions --action generate \
    --org-slug acme-corp \
    --permission-template read_write \
    --output-file permissions.json
```

This creates a `permissions.json` file like:

```json
{
  "Administrators": {
    "auth.User": {
      "can_push": true,
      "can_pull": true,
      "can_create": true,
      "can_update": true,
      "can_delete": true,
      "can_read": true
    },
    "myapp.Product": {
      "can_push": true,
      "can_pull": true,
      "can_create": true,
      "can_update": true,
      "can_delete": true,
      "can_read": true
    }
  },
  "Managers": {
    "auth.User": {
      "can_push": true,
      "can_pull": true,
      "can_create": true,
      "can_update": true,
      "can_delete": false,
      "can_read": true
    },
    "myapp.Product": {
      "can_push": true,
      "can_pull": true,
      "can_create": true,
      "can_update": true,
      "can_delete": false,
      "can_read": true
    }
  },
  "Sales": {
    "auth.User": {
      "can_push": true,
      "can_pull": true,
      "can_create": true,
      "can_update": true,
      "can_delete": false,
      "can_read": true
    },
    "myapp.Product": {
      "can_push": true,
      "can_pull": true,
      "can_create": true,
      "can_update": true,
      "can_delete": false,
      "can_read": true
    }
  }
}
```

### 3. Apply the Configuration

```bash
# Apply the generated configuration
python manage.py dynamic_permissions --action apply \
    --org-slug acme-corp \
    --config-file permissions.json

# Output:
# Applied configuration: 45 created, 0 updated
```

## 📋 Available Permission Templates

### Show Available Templates

```bash
python manage.py dynamic_permissions --action template
```

### Template Options

1. **full_access**: Complete control (create, read, update, delete, push, pull)
2. **read_write**: Standard access (create, read, update, push, pull, no delete)
3. **read_only**: Read-only access (pull, read only)
4. **write_only**: Write-only access (push, create, update, no read/pull)
5. **custom**: Custom access (push, pull, update, no create/delete)

## 🔧 Advanced Usage

### Discover Models from Specific App

```bash
# Discover models from a specific app
python manage.py dynamic_permissions --action discover --app-label myapp

# Exclude specific models
python manage.py dynamic_permissions --action discover --exclude-models "auth.User,auth.Group"
```

### Generate Configuration for Specific Groups

```bash
# Generate configuration for specific groups only
python manage.py dynamic_permissions --action generate \
    --org-slug acme-corp \
    --groups "Managers,Sales" \
    --permission-template read_write \
    --output-file managers_sales_permissions.json
```

### Export Current Permissions

```bash
# Export current permissions for an organization
python manage.py dynamic_permissions --action export \
    --org-slug acme-corp \
    --output-file current_permissions.json
```

### Validate Configuration

```bash
# Validate a configuration file before applying
python manage.py dynamic_permissions --action validate \
    --config-file permissions.json
```

## 🏥 Healthcare Example

### Discover Healthcare Models

```bash
python manage.py dynamic_permissions --action discover --app-label healthcare

# Output:
# Discovered 6 models:
#   - healthcare.Patient
#   - healthcare.Appointment
#   - healthcare.Prescription
#   - healthcare.LabResult
#   - healthcare.Billing
#   - healthcare.Insurance
```

### Generate Healthcare Permissions

```bash
python manage.py dynamic_permissions --action generate \
    --org-slug city-hospital \
    --app-label healthcare \
    --permission-template read_write \
    --output-file healthcare_permissions.json
```

### Custom Healthcare Configuration

```json
{
  "Doctors": {
    "healthcare.Patient": {
      "can_push": true,
      "can_pull": true,
      "can_create": true,
      "can_update": true,
      "can_delete": false,
      "can_read": true
    },
    "healthcare.Appointment": {
      "can_push": true,
      "can_pull": true,
      "can_create": true,
      "can_update": true,
      "can_delete": false,
      "can_read": true
    },
    "healthcare.Prescription": {
      "can_push": true,
      "can_pull": true,
      "can_create": true,
      "can_update": true,
      "can_delete": false,
      "can_read": true
    }
  },
  "Nurses": {
    "healthcare.Patient": {
      "can_push": false,
      "can_pull": true,
      "can_create": false,
      "can_update": true,
      "can_delete": false,
      "can_read": true
    },
    "healthcare.Appointment": {
      "can_push": true,
      "can_pull": true,
      "can_create": true,
      "can_update": true,
      "can_delete": false,
      "can_read": true
    }
  },
  "Lab Technicians": {
    "healthcare.LabResult": {
      "can_push": true,
      "can_pull": true,
      "can_create": true,
      "can_update": true,
      "can_delete": false,
      "can_read": true
    }
  }
}
```

## 🛒 E-commerce Example

### Discover E-commerce Models

```bash
python manage.py dynamic_permissions --action discover --app-label store

# Output:
# Discovered 8 models:
#   - store.Product
#   - store.Category
#   - store.Customer
#   - store.Order
#   - store.OrderItem
#   - store.Invoice
#   - store.Shipping
#   - store.Review
```

### Generate E-commerce Permissions

```bash
python manage.py dynamic_permissions --action generate \
    --org-slug online-store \
    --app-label store \
    --permission-template read_write \
    --output-file store_permissions.json
```

## 🏫 Educational Institution Example

### Discover Education Models

```bash
python manage.py dynamic_permissions --action discover --app-label education

# Output:
# Discovered 7 models:
#   - education.Student
#   - education.Course
#   - education.Enrollment
#   - education.Grade
#   - education.Teacher
#   - education.Department
#   - education.Schedule
```

## 🔍 Validation Examples

### Valid Configuration

```json
{
  "Managers": {
    "auth.User": {
      "can_push": true,
      "can_pull": true,
      "can_create": true,
      "can_update": true,
      "can_delete": false,
      "can_read": true
    }
  }
}
```

### Invalid Configuration (Missing Fields)

```json
{
  "Managers": {
    "auth.User": {
      "can_push": true,
      "can_pull": true
      // Missing required fields
    }
  }
}
```

Validation Error:
```
Configuration validation failed:
  - Missing "can_create" in Managers.auth.User
  - Missing "can_update" in Managers.auth.User
  - Missing "can_delete" in Managers.auth.User
  - Missing "can_read" in Managers.auth.User
```

## 🚀 Programmatic Usage

### Using the DynamicPermissionConfigurator

```python
from sb_sync.utils import DynamicPermissionConfigurator, ModelIntrospector
from sb_sync.models import Organization

# Get organization
org = Organization.objects.get(slug='acme-corp')

# Discover models
models = ModelIntrospector.discover_all_models()

# Generate configuration
config = DynamicPermissionConfigurator.generate_permission_config(
    organization=org,
    models=models,
    template='read_write'
)

# Apply configuration
result = DynamicPermissionConfigurator.apply_permission_config(org, config)
print(f"Created: {result['created']}, Updated: {result['updated']}")

# Export current configuration
current_config = DynamicPermissionConfigurator.export_permission_config(org)
```

## 📊 Performance Considerations

### Large Projects

For projects with many models and groups:

1. **Batch Processing**: The system processes permissions in batches
2. **Caching**: Model discovery and field information is cached
3. **Validation**: Configuration validation prevents invalid setups
4. **Incremental Updates**: Only changed permissions are updated

### Memory Usage

- Model discovery is cached for 1 hour
- Field information is cached per model
- Large configurations are processed in chunks

## 🔧 Troubleshooting

### Common Issues

1. **Model Not Found**: Ensure the app is in INSTALLED_APPS
2. **Group Not Found**: Create groups before generating permissions
3. **Organization Not Found**: Create organization before applying permissions
4. **Invalid JSON**: Use the validate action to check configuration

### Debug Commands

```bash
# Check if models exist
python manage.py shell
>>> from django.apps import apps
>>> apps.get_model('myapp.Product')

# Check if groups exist
python manage.py shell
>>> from django.contrib.auth.models import Group
>>> Group.objects.all()

# Check if organization exists
python manage.py shell
>>> from sb_sync.models import Organization
>>> Organization.objects.all()
```

## 🎯 Best Practices

1. **Start Small**: Begin with a few models and groups
2. **Use Templates**: Leverage predefined templates for consistency
3. **Validate First**: Always validate configurations before applying
4. **Export Backups**: Export current permissions before making changes
5. **Test Incrementally**: Apply permissions to test organizations first
6. **Document Changes**: Keep track of permission changes for audit trails

## 🔄 Workflow Example

### Complete Setup Workflow

```bash
# 1. Create organization
python manage.py setup_organizations --action create_org \
    --org-name "Acme Corp" --org-slug acme-corp

# 2. Create groups
python manage.py setup_organizations --action create_groups

# 3. Discover models
python manage.py dynamic_permissions --action discover

# 4. Generate configuration
python manage.py dynamic_permissions --action generate \
    --org-slug acme-corp --permission-template read_write \
    --output-file permissions.json

# 5. Validate configuration
python manage.py dynamic_permissions --action validate \
    --config-file permissions.json

# 6. Apply configuration
python manage.py dynamic_permissions --action apply \
    --org-slug acme-corp --config-file permissions.json

# 7. Add users to organization
python manage.py setup_organizations --action add_user \
    --username john --org-slug acme-corp --group-name Managers
```

This dynamic permission configuration system makes it easy to set up comprehensive, role-based access control for any Django project, regardless of the domain or complexity! 🎉 