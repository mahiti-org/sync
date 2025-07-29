# 🔄 Dynamic Data Sources Example

This document demonstrates how to use the dynamic data source system to work with **any external data source** (APIs, databases, files) without requiring Django models or configuration.

## 🎯 Overview

The dynamic data source system allows you to:

1. **Register Data Sources**: Connect to any external data source (API, database, file)
2. **Auto-Discover Entities**: Automatically find tables, endpoints, or files
3. **Dynamic Schema Detection**: Infer field structures automatically
4. **Universal Permissions**: Apply permissions to any data source
5. **Zero Configuration**: Works with any data source without pre-configuration

## 🚀 Quick Start

### 1. Register External Data Sources

```bash
# Register a REST API
python manage.py dynamic_sources --action register \
    --source-type api \
    --source-config '{"base_url": "https://api.example.com", "headers": {"Authorization": "Bearer token"}}'

# Register a PostgreSQL database
python manage.py dynamic_sources --action register \
    --source-type database \
    --source-config '{"connection_string": "postgresql://user:pass@localhost/db", "db_type": "postgresql"}'

# Register a CSV file
python manage.py dynamic_sources --action register \
    --source-type file \
    --source-config '{"file_path": "/path/to/data.csv", "file_type": "csv"}'
```

### 2. Discover Entities

```bash
# Discover all entities from all sources
python manage.py dynamic_sources --action discover

# Output example:
# Discovered entities from all sources:
# 
# API:
#   - users
#   - products
#   - orders
#   Fields: id, name, email, created_at
# 
# DATABASE:
#   - customers
#   - invoices
#   - shipments
#   Fields: customer_id, name, email, phone
# 
# FILE:
#   - sales_data
#   Fields: date, product, quantity, revenue
```

### 3. Generate Permissions

```bash
# Generate permissions for all discovered entities
python manage.py dynamic_sources --action generate \
    --org-slug acme-corp \
    --permission-template read_write \
    --output-file external_permissions.json
```

### 4. Apply Permissions

```bash
# Apply the generated permissions
python manage.py dynamic_sources --action apply \
    --org-slug acme-corp \
    --config-file external_permissions.json
```

## 📋 Supported Data Sources

### 1. REST APIs

```bash
# Register any REST API
python manage.py dynamic_sources --action register \
    --source-type api \
    --source-config '{
        "base_url": "https://api.salesforce.com",
        "headers": {
            "Authorization": "Bearer YOUR_TOKEN",
            "Content-Type": "application/json"
        }
    }'
```

**Auto-Discovery Features:**
- Tries common discovery endpoints (`/api/entities`, `/api/models`, etc.)
- Infers entities from common patterns (`users`, `customers`, `products`, etc.)
- Automatically detects field schemas from sample data
- Supports authentication (Basic Auth, Bearer Token, API Keys)

### 2. Databases

```bash
# PostgreSQL
python manage.py dynamic_sources --action register \
    --source-type database \
    --source-config '{
        "connection_string": "postgresql://user:pass@localhost/sales_db",
        "db_type": "postgresql"
    }'

# MySQL
python manage.py dynamic_sources --action register \
    --source-type database \
    --source-config '{
        "connection_string": "mysql://user:pass@localhost/inventory_db",
        "db_type": "mysql"
    }'

# SQLite
python manage.py dynamic_sources --action register \
    --source-type database \
    --source-config '{
        "connection_string": "/path/to/database.db",
        "db_type": "sqlite"
    }'
```

**Auto-Discovery Features:**
- Automatically discovers all tables
- Infers field types and constraints
- Supports all major database types
- Handles connection pooling and error recovery

### 3. Files

```bash
# CSV Files
python manage.py dynamic_sources --action register \
    --source-type file \
    --source-config '{
        "file_path": "/path/to/sales_data.csv",
        "file_type": "csv"
    }'

# JSON Files
python manage.py dynamic_sources --action register \
    --source-type file \
    --source-config '{
        "file_path": "/path/to/customer_data.json",
        "file_type": "json"
    }'

# Excel Files
python manage.py dynamic_sources --action register \
    --source-type file \
    --source-config '{
        "file_path": "/path/to/inventory.xlsx",
        "file_type": "excel"
    }'
```

**Auto-Discovery Features:**
- Automatically detects file structure
- Infers field types from data
- Supports multiple sheets (Excel)
- Handles nested JSON structures

## 🏥 Healthcare Example

### Register Healthcare Data Sources

```bash
# Register hospital API
python manage.py dynamic_sources --action register \
    --source-type api \
    --source-config '{
        "base_url": "https://hospital-api.com",
        "headers": {"Authorization": "Bearer HOSPITAL_TOKEN"}
    }'

# Register patient database
python manage.py dynamic_sources --action register \
    --source-type database \
    --source-config '{
        "connection_string": "postgresql://user:pass@localhost/patient_db",
        "db_type": "postgresql"
    }'

# Register lab results file
python manage.py dynamic_sources --action register \
    --source-type file \
    --source-config '{
        "file_path": "/data/lab_results.csv",
        "file_type": "csv"
    }'
```

### Discover Healthcare Entities

```bash
python manage.py dynamic_sources --action discover

# Output:
# API:
#   - patients
#   - appointments
#   - prescriptions
#   Fields: patient_id, name, dob, diagnosis
# 
# DATABASE:
#   - medical_records
#   - billing
#   - insurance
#   Fields: record_id, patient_id, treatment, cost
# 
# FILE:
#   - lab_results
#   Fields: test_id, patient_id, result, date
```

### Generate Healthcare Permissions

```bash
python manage.py dynamic_sources --action generate \
    --org-slug city-hospital \
    --permission-template read_write \
    --output-file healthcare_permissions.json
```

## 🛒 E-commerce Example

### Register E-commerce Data Sources

```bash
# Register Shopify API
python manage.py dynamic_sources --action register \
    --source-type api \
    --source-config '{
        "base_url": "https://your-store.myshopify.com/admin/api/2023-01",
        "headers": {"X-Shopify-Access-Token": "YOUR_TOKEN"}
    }'

# Register inventory database
python manage.py dynamic_sources --action register \
    --source-type database \
    --source-config '{
        "connection_string": "mysql://user:pass@localhost/inventory",
        "db_type": "mysql"
    }'

# Register sales data file
python manage.py dynamic_sources --action register \
    --source-type file \
    --source-config '{
        "file_path": "/data/daily_sales.json",
        "file_type": "json"
    }'
```

### Discover E-commerce Entities

```bash
python manage.py dynamic_sources --action discover

# Output:
# API:
#   - products
#   - orders
#   - customers
#   Fields: id, title, price, inventory_quantity
# 
# DATABASE:
#   - inventory
#   - suppliers
#   - shipping
#   Fields: product_id, quantity, supplier_id, cost
# 
# FILE:
#   - daily_sales
#   Fields: date, product_id, quantity, revenue
```

## 🔧 Advanced Usage

### Test Data Source Connectivity

```bash
# Test API connectivity
python manage.py dynamic_sources --action test \
    --source-type api \
    --test-entity users

# Test database connectivity
python manage.py dynamic_sources --action test \
    --source-type database \
    --test-entity customers

# Test file connectivity
python manage.py dynamic_sources --action test \
    --source-type file \
    --test-entity sales_data
```

### Validate Configuration

```bash
# Validate permission configuration
python manage.py dynamic_sources --action validate \
    --config-file permissions.json
```

### Export Current Configuration

```bash
# Export current permissions
python manage.py dynamic_sources --action export \
    --org-slug acme-corp \
    --output-file current_permissions.json
```

## 🚀 Programmatic Usage

### Using the DynamicDataSourceManager

```python
from sb_sync.utils import (
    DynamicDataSourceManager, RESTAPIAdapter, DatabaseAdapter, FileAdapter
)

# Create manager
manager = DynamicDataSourceManager()

# Register API source
api_adapter = RESTAPIAdapter(
    base_url="https://api.example.com",
    headers={"Authorization": "Bearer token"}
)
manager.register_adapter("api", api_adapter)

# Register database source
db_adapter = DatabaseAdapter(
    connection_string="postgresql://user:pass@localhost/db",
    db_type="postgresql"
)
manager.register_adapter("database", db_adapter)

# Discover all entities
discovered = manager.discover_all_sources()
print(f"Discovered: {discovered}")

# Get field information
fields = manager.get_entity_fields("api", "users")
print(f"User fields: {fields}")

# Push data
data = [{"name": "John", "email": "john@example.com"}]
result = manager.push_data("api", "users", data)
print(f"Push result: {result}")

# Pull data
users = manager.pull_data("api", "users", {"status": "active"})
print(f"Pulled {len(users)} users")
```

### Custom Data Source Adapter

```python
from sb_sync.utils import DataSourceAdapter
from typing import Dict, List, Any, Optional

class CustomAPIAdapter(DataSourceAdapter):
    """Custom adapter for specific API"""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
    
    def discover_entities(self) -> List[str]:
        """Discover entities from custom API"""
        # Custom discovery logic
        return ["custom_entity_1", "custom_entity_2"]
    
    def get_entity_fields(self, entity_name: str) -> Dict[str, Any]:
        """Get field information for entity"""
        # Custom field discovery
        return {
            "id": {"type": "integer", "required": True},
            "name": {"type": "string", "required": True},
            "created_at": {"type": "datetime", "required": False}
        }
    
    def push_data(self, entity_name: str, data: List[Dict]) -> Dict[str, Any]:
        """Push data to custom API"""
        # Custom push logic
        return {"success_count": len(data), "error_count": 0}
    
    def pull_data(self, entity_name: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Pull data from custom API"""
        # Custom pull logic
        return [{"id": 1, "name": "Example"}]
    
    def validate_data(self, entity_name: str, data: Dict) -> List[str]:
        """Validate data against custom schema"""
        # Custom validation logic
        return []

# Register custom adapter
custom_adapter = CustomAPIAdapter("your_api_key", "https://custom-api.com")
data_source_manager.register_adapter("custom", custom_adapter)
```

## 📊 Performance Considerations

### Large Data Sources

For large data sources with many entities:

1. **Caching**: Field information is cached for 1 hour
2. **Batch Processing**: Data operations are processed in batches
3. **Connection Pooling**: Database connections are reused
4. **Error Recovery**: Automatic retry for failed operations

### Memory Usage

- Entity discovery is cached per source
- Field information is cached per entity
- Large datasets are processed in chunks
- Connection pooling reduces memory overhead

## 🔍 Validation Examples

### Valid Data Source Configuration

```json
{
  "base_url": "https://api.example.com",
  "headers": {
    "Authorization": "Bearer token"
  },
  "auth": ["username", "password"]
}
```

### Valid Permission Configuration

```json
{
  "Managers": {
    "api.users": {
      "can_push": true,
      "can_pull": true,
      "can_create": true,
      "can_update": true,
      "can_delete": false,
      "can_read": true
    },
    "database.customers": {
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

## 🔧 Troubleshooting

### Common Issues

1. **Connection Failed**: Check connection strings and credentials
2. **Authentication Error**: Verify API tokens and headers
3. **Entity Not Found**: Ensure data source is properly registered
4. **Permission Denied**: Check file permissions for file-based sources

### Debug Commands

```bash
# Test specific source
python manage.py dynamic_sources --action test \
    --source-type api \
    --test-entity users

# Check discovered entities
python manage.py dynamic_sources --action discover

# Validate configuration
python manage.py dynamic_sources --action validate \
    --config-file permissions.json
```

## 🎯 Best Practices

1. **Start Small**: Begin with one data source and test thoroughly
2. **Use Caching**: Leverage built-in caching for better performance
3. **Validate First**: Always validate configurations before applying
4. **Monitor Performance**: Watch for large data operations
5. **Secure Credentials**: Store sensitive connection info securely
6. **Test Connectivity**: Test data sources before production use

## 🔄 Complete Workflow Example

### Complete Setup Workflow

```bash
# 1. Register data sources
python manage.py dynamic_sources --action register \
    --source-type api \
    --source-config '{"base_url": "https://api.example.com", "headers": {"Authorization": "Bearer token"}}'

python manage.py dynamic_sources --action register \
    --source-type database \
    --source-config '{"connection_string": "postgresql://user:pass@localhost/db", "db_type": "postgresql"}'

# 2. Discover entities
python manage.py dynamic_sources --action discover

# 3. Test connectivity
python manage.py dynamic_sources --action test --source-type api --test-entity users

# 4. Generate permissions
python manage.py dynamic_sources --action generate \
    --org-slug acme-corp --permission-template read_write \
    --output-file permissions.json

# 5. Validate configuration
python manage.py dynamic_sources --action validate --config-file permissions.json

# 6. Apply permissions
python manage.py dynamic_sources --action apply \
    --org-slug acme-corp --config-file permissions.json
```

This dynamic data source system makes it possible to work with **any external data source** without requiring Django models or pre-configuration! 🎉

## 🔄 Key Benefits

### 1. **Universal Compatibility**
- ✅ Works with any REST API
- ✅ Supports all major databases
- ✅ Handles any file format
- ✅ No Django model requirements

### 2. **Zero Configuration**
- ✅ Auto-discovers entities
- ✅ Auto-detects schemas
- ✅ Auto-generates permissions
- ✅ No manual setup required

### 3. **Dynamic Discovery**
- ✅ Discovers new entities automatically
- ✅ Adapts to schema changes
- ✅ Handles new data sources seamlessly
- ✅ No code changes needed

### 4. **Production Ready**
- ✅ Error handling and recovery
- ✅ Performance optimization
- ✅ Security and authentication
- ✅ Monitoring and logging

The system is now **100% dynamic** and can work with any external data source without requiring Django models or configuration! 🚀 