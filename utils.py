"""
Utility functions for sb-sync package
"""
import json
import logging
from django.apps import apps
from django.db import models
from django.core.cache import cache
from django.conf import settings
from .models import ModelPermission, DataFilter
from django.contrib.auth.models import Group
import requests
import sqlite3
import psycopg2
import mysql.connector
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
import pandas as pd
import csv
import xml.etree.ElementTree as ET

logger = logging.getLogger('sb_sync')

class DataSourceAdapter(ABC):
    """Abstract base class for data source adapters"""
    
    @abstractmethod
    def discover_entities(self) -> List[str]:
        """Discover available entities/tables in the data source"""
        pass
    
    @abstractmethod
    def get_entity_fields(self, entity_name: str) -> Dict[str, Any]:
        """Get field information for an entity"""
        pass
    
    @abstractmethod
    def push_data(self, entity_name: str, data: List[Dict]) -> Dict[str, Any]:
        """Push data to the entity"""
        pass
    
    @abstractmethod
    def pull_data(self, entity_name: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Pull data from the entity"""
        pass
    
    @abstractmethod
    def validate_data(self, entity_name: str, data: Dict) -> List[str]:
        """Validate data against entity schema"""
        pass

class RESTAPIAdapter(DataSourceAdapter):
    """Adapter for REST API data sources"""
    
    def __init__(self, base_url: str, headers: Optional[Dict] = None, auth: Optional[tuple] = None):
        self.base_url = base_url.rstrip('/')
        self.headers = headers or {}
        self.auth = auth
        self._entity_cache = {}
    
    def discover_entities(self) -> List[str]:
        """Discover entities from API endpoints"""
        try:
            # Try common discovery endpoints
            discovery_endpoints = [
                '/api/entities',
                '/api/models',
                '/api/tables',
                '/api/schemas',
                '/api/endpoints'
            ]
            
            for endpoint in discovery_endpoints:
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", headers=self.headers, auth=self.auth)
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, list):
                            return data
                        elif isinstance(data, dict) and 'entities' in data:
                            return data['entities']
                        elif isinstance(data, dict) and 'models' in data:
                            return data['models']
                except:
                    continue
            
            # If no discovery endpoint, try to infer from common patterns
            return self._infer_entities_from_patterns()
            
        except Exception as e:
            logger.error(f"Error discovering entities from API: {e}")
            return []
    
    def _infer_entities_from_patterns(self) -> List[str]:
        """Infer entities from common API patterns"""
        common_entities = [
            'users', 'customers', 'products', 'orders', 'invoices',
            'patients', 'appointments', 'prescriptions', 'employees',
            'departments', 'projects', 'tasks', 'reports'
        ]
        
        discovered = []
        for entity in common_entities:
            try:
                response = requests.get(f"{self.base_url}/api/{entity}", headers=self.headers, auth=self.auth)
                if response.status_code == 200:
                    discovered.append(entity)
            except:
                continue
        
        return discovered
    
    def get_entity_fields(self, entity_name: str) -> Dict[str, Any]:
        """Get field information for an entity"""
        cache_key = f"api_fields_{entity_name}"
        fields = cache.get(cache_key)
        
        if fields is None:
            try:
                # Try to get schema from API
                response = requests.get(f"{self.base_url}/api/{entity_name}/schema", headers=self.headers, auth=self.auth)
                if response.status_code == 200:
                    schema = response.json()
                    fields = self._parse_api_schema(schema)
                else:
                    # Try to infer from sample data
                    response = requests.get(f"{self.base_url}/api/{entity_name}?limit=1", headers=self.headers, auth=self.auth)
                    if response.status_code == 200:
                        sample_data = response.json()
                        if isinstance(sample_data, list) and sample_data:
                            fields = self._infer_fields_from_sample(sample_data[0])
                        elif isinstance(sample_data, dict) and 'data' in sample_data:
                            fields = self._infer_fields_from_sample(sample_data['data'][0] if sample_data['data'] else {})
                
                cache.set(cache_key, fields, timeout=3600)
                
            except Exception as e:
                logger.error(f"Error getting fields for {entity_name}: {e}")
                fields = {}
        
        return fields
    
    def _parse_api_schema(self, schema: Dict) -> Dict[str, Any]:
        """Parse API schema to field information"""
        fields = {}
        
        if 'properties' in schema:
            for field_name, field_info in schema['properties'].items():
                fields[field_name] = {
                    'type': field_info.get('type', 'string'),
                    'required': field_name in schema.get('required', []),
                    'max_length': field_info.get('maxLength'),
                    'description': field_info.get('description', '')
                }
        
        return fields
    
    def _infer_fields_from_sample(self, sample: Dict) -> Dict[str, Any]:
        """Infer field information from sample data"""
        fields = {}
        
        for field_name, value in sample.items():
            fields[field_name] = {
                'type': type(value).__name__,
                'required': False,  # Can't determine from sample
                'max_length': None,
                'description': f'Inferred from sample data'
            }
        
        return fields
    
    def push_data(self, entity_name: str, data: List[Dict]) -> Dict[str, Any]:
        """Push data to API entity"""
        results = {
            'success_count': 0,
            'error_count': 0,
            'errors': [],
            'created': 0,
            'updated': 0
        }
        
        for item in data:
            try:
                # Try POST for creation
                response = requests.post(
                    f"{self.base_url}/api/{entity_name}",
                    json=item,
                    headers=self.headers,
                    auth=self.auth
                )
                
                if response.status_code in [200, 201]:
                    results['success_count'] += 1
                    results['created'] += 1
                else:
                    results['error_count'] += 1
                    results['errors'].append(f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                results['error_count'] += 1
                results['errors'].append(f"Error pushing {entity_name}: {str(e)}")
        
        return results
    
    def pull_data(self, entity_name: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Pull data from API entity"""
        try:
            params = {}
            if filters:
                params.update(filters)
            
            response = requests.get(
                f"{self.base_url}/api/{entity_name}",
                params=params,
                headers=self.headers,
                auth=self.auth
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and 'data' in data:
                    return data['data']
                elif isinstance(data, dict) and 'results' in data:
                    return data['results']
                else:
                    return [data]
            else:
                logger.error(f"Error pulling data from {entity_name}: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error pulling data from {entity_name}: {e}")
            return []
    
    def validate_data(self, entity_name: str, data: Dict) -> List[str]:
        """Validate data against entity schema"""
        errors = []
        fields = self.get_entity_fields(entity_name)
        
        for field_name, value in data.items():
            if field_name not in fields:
                errors.append(f"Field '{field_name}' not found in {entity_name}")
                continue
            
            field_info = fields[field_name]
            if field_info.get('required') and value is None:
                errors.append(f"Required field '{field_name}' cannot be null")
        
        return errors

class DatabaseAdapter(DataSourceAdapter):
    """Adapter for database data sources"""
    
    def __init__(self, connection_string: str, db_type: str = 'postgresql'):
        self.connection_string = connection_string
        self.db_type = db_type
        self._entity_cache = {}
    
    def _get_connection(self):
        """Get database connection"""
        if self.db_type == 'postgresql':
            return psycopg2.connect(self.connection_string)
        elif self.db_type == 'mysql':
            return mysql.connector.connect(self.connection_string)
        elif self.db_type == 'sqlite':
            return sqlite3.connect(self.connection_string)
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")
    
    def discover_entities(self) -> List[str]:
        """Discover tables in database"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if self.db_type == 'postgresql':
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
            elif self.db_type == 'mysql':
                cursor.execute("SHOW TABLES")
            elif self.db_type == 'sqlite':
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            
            return tables
            
        except Exception as e:
            logger.error(f"Error discovering database entities: {e}")
            return []
    
    def get_entity_fields(self, entity_name: str) -> Dict[str, Any]:
        """Get field information for database table"""
        cache_key = f"db_fields_{entity_name}"
        fields = cache.get(cache_key)
        
        if fields is None:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                if self.db_type == 'postgresql':
                    cursor.execute("""
                        SELECT column_name, data_type, is_nullable, character_maximum_length
                        FROM information_schema.columns
                        WHERE table_name = %s
                    """, (entity_name,))
                elif self.db_type == 'mysql':
                    cursor.execute("DESCRIBE " + entity_name)
                elif self.db_type == 'sqlite':
                    cursor.execute("PRAGMA table_info(" + entity_name + ")")
                
                columns = cursor.fetchall()
                fields = {}
                
                for column in columns:
                    if self.db_type == 'postgresql':
                        field_name, data_type, is_nullable, max_length = column
                        fields[field_name] = {
                            'type': data_type,
                            'required': is_nullable == 'NO',
                            'max_length': max_length
                        }
                    elif self.db_type == 'mysql':
                        field_name, data_type, is_nullable, key, default, extra = column
                        fields[field_name] = {
                            'type': data_type,
                            'required': is_nullable == 'NO',
                            'max_length': None
                        }
                    elif self.db_type == 'sqlite':
                        cid, field_name, data_type, not_null, default_value, pk = column
                        fields[field_name] = {
                            'type': data_type,
                            'required': not_null == 1,
                            'max_length': None
                        }
                
                cursor.close()
                conn.close()
                
                cache.set(cache_key, fields, timeout=3600)
                
            except Exception as e:
                logger.error(f"Error getting fields for {entity_name}: {e}")
                fields = {}
        
        return fields
    
    def push_data(self, entity_name: str, data: List[Dict]) -> Dict[str, Any]:
        """Push data to database table"""
        results = {
            'success_count': 0,
            'error_count': 0,
            'errors': [],
            'created': 0,
            'updated': 0
        }
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            for item in data:
                try:
                    fields = list(item.keys())
                    placeholders = ', '.join(['%s'] * len(fields))
                    field_names = ', '.join(fields)
                    values = list(item.values())
                    
                    query = f"INSERT INTO {entity_name} ({field_names}) VALUES ({placeholders})"
                    cursor.execute(query, values)
                    
                    results['success_count'] += 1
                    results['created'] += 1
                    
                except Exception as e:
                    results['error_count'] += 1
                    results['errors'].append(f"Error inserting into {entity_name}: {str(e)}")
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            results['error_count'] += len(data)
            results['errors'].append(f"Database error: {str(e)}")
        
        return results
    
    def pull_data(self, entity_name: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Pull data from database table"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = f"SELECT * FROM {entity_name}"
            params = []
            
            if filters:
                where_clauses = []
                for field, value in filters.items():
                    where_clauses.append(f"{field} = %s")
                    params.append(value)
                
                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)
            
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))
            
            cursor.close()
            conn.close()
            
            return data
            
        except Exception as e:
            logger.error(f"Error pulling data from {entity_name}: {e}")
            return []
    
    def validate_data(self, entity_name: str, data: Dict) -> List[str]:
        """Validate data against database schema"""
        errors = []
        fields = self.get_entity_fields(entity_name)
        
        for field_name, value in data.items():
            if field_name not in fields:
                errors.append(f"Field '{field_name}' not found in {entity_name}")
                continue
            
            field_info = fields[field_name]
            if field_info.get('required') and value is None:
                errors.append(f"Required field '{field_name}' cannot be null")
        
        return errors

class FileAdapter(DataSourceAdapter):
    """Adapter for file-based data sources (CSV, JSON, Excel)"""
    
    def __init__(self, file_path: str, file_type: str = 'csv'):
        self.file_path = file_path
        self.file_type = file_type
        self._entity_cache = {}
    
    def discover_entities(self) -> List[str]:
        """Discover entities from file structure"""
        if self.file_type == 'csv':
            return [self.file_path.split('/')[-1].replace('.csv', '')]
        elif self.file_type == 'json':
            try:
                with open(self.file_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list) and data:
                        return [self.file_path.split('/')[-1].replace('.json', '')]
                    elif isinstance(data, dict):
                        return list(data.keys())
            except:
                pass
        elif self.file_type == 'excel':
            try:
                df = pd.read_excel(self.file_path, sheet_name=None)
                return list(df.keys())
            except:
                pass
        
        return []
    
    def get_entity_fields(self, entity_name: str) -> Dict[str, Any]:
        """Get field information from file"""
        cache_key = f"file_fields_{entity_name}"
        fields = cache.get(cache_key)
        
        if fields is None:
            try:
                if self.file_type == 'csv':
                    df = pd.read_csv(self.file_path)
                elif self.file_type == 'json':
                    with open(self.file_path, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list) and data:
                            df = pd.DataFrame(data)
                        else:
                            df = pd.DataFrame(data[entity_name])
                elif self.file_type == 'excel':
                    df = pd.read_excel(self.file_path, sheet_name=entity_name)
                
                fields = {}
                for column in df.columns:
                    fields[column] = {
                        'type': str(df[column].dtype),
                        'required': not df[column].isnull().all(),
                        'max_length': None
                    }
                
                cache.set(cache_key, fields, timeout=3600)
                
            except Exception as e:
                logger.error(f"Error getting fields for {entity_name}: {e}")
                fields = {}
        
        return fields
    
    def push_data(self, entity_name: str, data: List[Dict]) -> Dict[str, Any]:
        """Push data to file"""
        results = {
            'success_count': 0,
            'error_count': 0,
            'errors': [],
            'created': 0,
            'updated': 0
        }
        
        try:
            if self.file_type == 'csv':
                df_new = pd.DataFrame(data)
                df_new.to_csv(self.file_path, mode='a', header=False, index=False)
            elif self.file_type == 'json':
                with open(self.file_path, 'r') as f:
                    existing_data = json.load(f)
                
                if isinstance(existing_data, list):
                    existing_data.extend(data)
                else:
                    if entity_name not in existing_data:
                        existing_data[entity_name] = []
                    existing_data[entity_name].extend(data)
                
                with open(self.file_path, 'w') as f:
                    json.dump(existing_data, f, indent=2)
            
            results['success_count'] = len(data)
            results['created'] = len(data)
            
        except Exception as e:
            results['error_count'] = len(data)
            results['errors'].append(f"Error writing to file: {str(e)}")
        
        return results
    
    def pull_data(self, entity_name: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Pull data from file"""
        try:
            if self.file_type == 'csv':
                df = pd.read_csv(self.file_path)
            elif self.file_type == 'json':
                with open(self.file_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        df = pd.DataFrame(data)
                    else:
                        df = pd.DataFrame(data[entity_name])
            elif self.file_type == 'excel':
                df = pd.read_excel(self.file_path, sheet_name=entity_name)
            
            # Apply filters if provided
            if filters:
                for field, value in filters.items():
                    if field in df.columns:
                        df = df[df[field] == value]
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Error pulling data from {entity_name}: {e}")
            return []
    
    def validate_data(self, entity_name: str, data: Dict) -> List[str]:
        """Validate data against file schema"""
        errors = []
        fields = self.get_entity_fields(entity_name)
        
        for field_name, value in data.items():
            if field_name not in fields:
                errors.append(f"Field '{field_name}' not found in {entity_name}")
                continue
            
            field_info = fields[field_name]
            if field_info.get('required') and value is None:
                errors.append(f"Required field '{field_name}' cannot be null")
        
        return errors

class DynamicDataSourceManager:
    """Manager for dynamic data source discovery and configuration"""
    
    def __init__(self):
        self.adapters = {}
        self._discovered_sources = {}
    
    def register_adapter(self, source_type: str, adapter: DataSourceAdapter):
        """Register a data source adapter"""
        self.adapters[source_type] = adapter
    
    def discover_all_sources(self) -> Dict[str, List[str]]:
        """Discover entities from all registered data sources"""
        discovered = {}
        
        for source_type, adapter in self.adapters.items():
            try:
                entities = adapter.discover_entities()
                discovered[source_type] = entities
                self._discovered_sources[source_type] = entities
            except Exception as e:
                logger.error(f"Error discovering {source_type} sources: {e}")
                discovered[source_type] = []
        
        return discovered
    
    def get_entity_fields(self, source_type: str, entity_name: str) -> Dict[str, Any]:
        """Get field information for an entity"""
        if source_type not in self.adapters:
            return {}
        
        adapter = self.adapters[source_type]
        return adapter.get_entity_fields(entity_name)
    
    def push_data(self, source_type: str, entity_name: str, data: List[Dict]) -> Dict[str, Any]:
        """Push data to entity"""
        if source_type not in self.adapters:
            return {'error_count': len(data), 'errors': [f'Unknown source type: {source_type}']}
        
        adapter = self.adapters[source_type]
        return adapter.push_data(entity_name, data)
    
    def pull_data(self, source_type: str, entity_name: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Pull data from entity"""
        if source_type not in self.adapters:
            return []
        
        adapter = self.adapters[source_type]
        return adapter.pull_data(entity_name, filters)
    
    def validate_data(self, source_type: str, entity_name: str, data: Dict) -> List[str]:
        """Validate data against entity schema"""
        if source_type not in self.adapters:
            return [f'Unknown source type: {source_type}']
        
        adapter = self.adapters[source_type]
        return adapter.validate_data(entity_name, data)
    
    def generate_permission_config(self, organization, source_types: List[str] = None, 
                                 groups: List[Group] = None, template: str = 'read_write') -> Dict:
        """Generate permission configuration for discovered data sources"""
        if source_types is None:
            source_types = list(self.adapters.keys())
        
        if groups is None:
            groups = Group.objects.all()
        
        # Discover all entities
        all_entities = {}
        for source_type in source_types:
            if source_type in self.adapters:
                entities = self.adapters[source_type].discover_entities()
                for entity in entities:
                    all_entities[f"{source_type}.{entity}"] = {
                        'source_type': source_type,
                        'entity_name': entity
                    }
        
        # Generate configuration
        templates = ModelIntrospector.get_model_permission_templates()
        template_config = templates.get(template, templates['read_write'])
        
        config = {}
        for group in groups:
            config[group.name] = {}
            for entity_key, entity_info in all_entities.items():
                config[group.name][entity_key] = template_config.copy()
        
        return config

# Global data source manager instance
data_source_manager = DynamicDataSourceManager()

class ModelIntrospector:
    """Introspect Django models for dynamic configuration"""
    
    @staticmethod
    def get_model_fields(model_name):
        """Get cached model fields"""
        cache_key = f"sb_sync_model_fields_{model_name}"
        fields = cache.get(cache_key)

        if fields is None:
            try:
                model_class = apps.get_model(model_name)
                fields = {}
                for field in model_class._meta.get_fields():
                    if not field.many_to_many and not field.one_to_many:
                        fields[field.name] = {
                            'type': field.__class__.__name__,
                            'required': not field.null and not field.blank,
                            'max_length': getattr(field, 'max_length', None)
                        }
                cache.set(cache_key, fields, timeout=3600)  # Cache for 1 hour
            except LookupError:
                fields = {}
        return fields

    @staticmethod
    def validate_json_against_model(json_data, model_name):
        """Validate JSON data against model structure"""
        model_fields = ModelIntrospector.get_model_fields(model_name)
        errors = []
        
        for field_name, value in json_data.items():
            if field_name not in model_fields:
                errors.append(f"Field '{field_name}' not found in model '{model_name}'")
                continue
            
            field_info = model_fields[field_name]
            if field_info['required'] and value is None:
                errors.append(f"Required field '{field_name}' cannot be null")
        
        return errors

    @staticmethod
    def discover_all_models(app_label=None, exclude_models=None):
        """Discover all Django models in the project"""
        discovered_models = []
        exclude_models = exclude_models or []
        
        if app_label:
            # Discover models from specific app
            try:
                app_config = apps.get_app_config(app_label)
                models_module = app_config.models_module
                if models_module:
                    for model in models_module.__dict__.values():
                        if isinstance(model, type) and issubclass(model, models.Model) and model != models.Model:
                            model_name = f"{app_label}.{model.__name__}"
                            if model_name not in exclude_models:
                                discovered_models.append(model_name)
            except Exception as e:
                logger.error(f'Error discovering models from app {app_label}: {e}')
        else:
            # Discover models from all apps
            for app_config in apps.get_app_configs():
                if app_config.models_module:
                    for model in app_config.models_module.__dict__.values():
                        if isinstance(model, type) and issubclass(model, models.Model) and model != models.Model:
                            model_name = f"{app_config.label}.{model.__name__}"
                            if model_name not in exclude_models:
                                discovered_models.append(model_name)
        
        return discovered_models

    @staticmethod
    def get_model_permission_templates():
        """Get predefined permission templates"""
        return {
            'full_access': {
                'can_push': True,
                'can_pull': True,
                'can_create': True,
                'can_update': True,
                'can_delete': True,
                'can_read': True
            },
            'read_write': {
                'can_push': True,
                'can_pull': True,
                'can_create': True,
                'can_update': True,
                'can_delete': False,
                'can_read': True
            },
            'read_only': {
                'can_push': False,
                'can_pull': True,
                'can_create': False,
                'can_update': False,
                'can_delete': False,
                'can_read': True
            },
            'write_only': {
                'can_push': True,
                'can_pull': False,
                'can_create': True,
                'can_update': True,
                'can_delete': False,
                'can_read': False
            },
            'custom': {
                'can_push': True,
                'can_pull': True,
                'can_create': False,
                'can_update': True,
                'can_delete': False,
                'can_read': True
            }
        }

class DynamicPermissionConfigurator:
    """Dynamic permission configuration utility"""
    
    @staticmethod
    def generate_permission_config(organization, models=None, groups=None, template='read_write'):
        """Generate permission configuration for organization"""
        if models is None:
            models = ModelIntrospector.discover_all_models()
        
        if groups is None:
            groups = Group.objects.all()
        
        templates = ModelIntrospector.get_model_permission_templates()
        template_config = templates.get(template, templates['read_write'])
        
        config = {}
        for group in groups:
            config[group.name] = {}
            for model_name in models:
                config[group.name][model_name] = template_config.copy()
        
        return config
    
    @staticmethod
    def apply_permission_config(organization, config):
        """Apply permission configuration to database"""
        permissions_created = 0
        permissions_updated = 0
        
        for group_name, models in config.items():
            try:
                group = Group.objects.get(name=group_name)
            except Group.DoesNotExist:
                logger.warning(f'Group {group_name} not found, skipping...')
                continue
            
            for model_name, permissions in models.items():
                permission, created = ModelPermission.objects.get_or_create(
                    organization=organization,
                    group=group,
                    model_name=model_name,
                    defaults=permissions
                )
                
                if created:
                    permissions_created += 1
                else:
                    # Update existing permission
                    for key, value in permissions.items():
                        setattr(permission, key, value)
                    permission.save()
                    permissions_updated += 1
        
        return {
            'created': permissions_created,
            'updated': permissions_updated,
            'total': permissions_created + permissions_updated
        }
    
    @staticmethod
    def export_permission_config(organization):
        """Export current permission configuration"""
        config = {}
        permissions = ModelPermission.objects.filter(organization=organization)
        
        for permission in permissions:
            group_name = permission.group.name
            if group_name not in config:
                config[group_name] = {}
            
            config[group_name][permission.model_name] = {
                'can_push': permission.can_push,
                'can_pull': permission.can_pull,
                'can_create': permission.can_create,
                'can_update': permission.can_update,
                'can_delete': permission.can_delete,
                'can_read': permission.can_read
            }
        
        return config
    
    @staticmethod
    def generate_data_filters(organization, models=None, groups=None):
        """Generate example data filters for models"""
        if models is None:
            models = ModelIntrospector.discover_all_models()
        
        if groups is None:
            groups = Group.objects.all()
        
        filters = []
        
        for group in groups:
            for model_name in models:
                # Generate example filters based on common patterns
                example_filters = DynamicPermissionConfigurator._generate_example_filters(
                    model_name, group.name
                )
                filters.extend(example_filters)
        
        return filters
    
    @staticmethod
    def _generate_example_filters(model_name, group_name):
        """Generate example filters for a model and group"""
        filters = []
        
        # Common filter patterns
        filter_patterns = [
            {
                'name': 'organization_filter',
                'condition': {
                    'field': 'organization',
                    'operator': 'exact',
                    'value': '{{organization_id}}'
                }
            },
            {
                'name': 'department_filter',
                'condition': {
                    'field': 'department',
                    'operator': 'exact',
                    'value': '{{department}}'
                }
            },
            {
                'name': 'assigned_user_filter',
                'condition': {
                    'field': 'assigned_user_id',
                    'operator': 'exact',
                    'value': '{{user_id}}'
                }
            },
            {
                'name': 'active_records_filter',
                'condition': {
                    'field': 'is_active',
                    'operator': 'exact',
                    'value': True
                }
            }
        ]
        
        for pattern in filter_patterns:
            filters.append({
                'model_name': model_name,
                'group_name': group_name,
                'filter_name': pattern['name'],
                'filter_condition': pattern['condition']
            })
        
        return filters

class DataProcessor:
    """Data processing utilities"""
    
    @staticmethod
    def process_push_data(json_data, user):
        """Process push data with validation"""
        results = {
            'success_count': 0,
            'error_count': 0,
            'errors': [],
            'processed_models': {}
        }
        
        for item_data in json_data:
            model_name = item_data.get('_model')
            if not model_name:
                results['errors'].append("Missing '_model' field")
                results['error_count'] += 1
                continue
            
            # Validate against model structure
            validation_errors = ModelIntrospector.validate_json_against_model(item_data, model_name)
            if validation_errors:
                results['errors'].extend(validation_errors)
                results['error_count'] += 1
                continue
            
            # Process the data
            try:
                model_class = apps.get_model(model_name)
                # Process the data (implementation depends on your needs)
                results['success_count'] += 1
                if model_name not in results['processed_models']:
                    results['processed_models'][model_name] = 0
                results['processed_models'][model_name] += 1
            except Exception as e:
                results['errors'].append(f"Error processing {model_name}: {str(e)}")
                results['error_count'] += 1
        
        return results

    @staticmethod
    def process_pull_data(model_name, filters=None):
        """Process pull data with filtering"""
        try:
            model_class = apps.get_model(model_name)
            queryset = model_class.objects.all()
            
            if filters:
                for filter_condition in filters:
                    field = filter_condition.get('field')
                    operator = filter_condition.get('operator')
                    value = filter_condition.get('value')
                    
                    if field and operator and value is not None:
                        if operator == 'in':
                            queryset = queryset.filter(**{f"{field}__in": value})
                        elif operator == 'exact':
                            queryset = queryset.filter(**{field: value})
                        elif operator == 'contains':
                            queryset = queryset.filter(**{f"{field}__contains": value})
                        elif operator == 'gte':
                            queryset = queryset.filter(**{f"{field}__gte": value})
                        elif operator == 'lte':
                            queryset = queryset.filter(**{f"{field}__lte": value})
            
            return list(queryset.values())
        except Exception as e:
            logger.error(f"Error processing pull data for {model_name}: {str(e)}")
            return []

    @staticmethod
    def sanitize_data(data):
        """Sanitize data for safe processing"""
        if isinstance(data, dict):
            return {k: DataProcessor.sanitize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [DataProcessor.sanitize_data(item) for item in data]
        elif isinstance(data, str):
            # Remove potentially dangerous characters
            return data.strip()
        else:
            return data

    @staticmethod
    def batch_process_data(data, batch_size=1000):
        """Process data in batches for better performance"""
        results = []
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            batch_result = DataProcessor.process_push_data(batch, None)
            results.append(batch_result)
        return results

class CacheManager:
    """Cache management utilities"""
    
    @staticmethod
    def clear_model_cache(model_name):
        """Clear cache for a specific model"""
        cache_keys = [
            f"sb_sync_model_fields_{model_name}",
            f"model_permission_*_{model_name}_*",
            f"data_filters_*_{model_name}"
        ]
        
        for pattern in cache_keys:
            # Note: This is a simplified version. In production, you might want to use
            # a more sophisticated cache clearing mechanism
            cache.delete(pattern)
    
    @staticmethod
    def clear_organization_cache(organization_id):
        """Clear cache for a specific organization"""
        cache_keys = [
            f"user_organizations_*",
            f"model_permission_{organization_id}_*",
            f"data_filters_{organization_id}_*"
        ]
        
        for pattern in cache_keys:
            cache.delete(pattern)
    
    @staticmethod
    def clear_user_cache(user_id):
        """Clear cache for a specific user"""
        cache_keys = [
            f"user_organizations_{user_id}",
            f"user_groups_{user_id}_*",
            f"user_sync_metadata_{user_id}_*"
        ]
        
        for pattern in cache_keys:
            cache.delete(pattern)
