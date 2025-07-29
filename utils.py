import json
import logging
from django.apps import apps
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction, models
from django.utils import timezone
from django.core.cache import cache
from typing import Dict, List, Any, Tuple
import time
from .error_handling import (
    SyncError, ValidationError, DatabaseError, ConfigurationError,
    ErrorCategory, ErrorSeverity, retry_handler
)
from .optimizations import (
    BulkOperations, CacheOptimizer, MemoryOptimizer, 
    PerformanceMonitor, QueryOptimizer
)

logger = logging.getLogger('sb_sync')

class ModelIntrospector:
    """Utility class for model introspection and data validation"""
    
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
    def validate_json_against_model(json_data: Dict, model_name: str) -> Tuple[bool, List[str]]:
        """Validate JSON data against model structure with caching"""
        errors = []
        model_fields = ModelIntrospector.get_model_fields(model_name)
        
        if not model_fields:
            errors.append(f"Model '{model_name}' not found or has no fields")
            return False, errors
        
        # Check for extra fields in JSON
        for json_field in json_data.keys():
            if json_field not in model_fields and json_field not in ['_model', 'id']:
                errors.append(f"Field '{json_field}' not found in model {model_name}")
        
        # Check for required fields
        for field_name, field_info in model_fields.items():
            if field_info['required'] and field_name not in json_data:
                errors.append(f"Required field '{field_name}' missing in JSON data")
        
        return len(errors) == 0, errors

class DataProcessor:
    """Handle data processing for PUSH operations with optimizations"""
    
    @staticmethod
    @retry_handler.retry
    @QueryOptimizer.count_queries
    @MemoryOptimizer.monitor_memory
    def process_push_data(json_data: List[Dict], user) -> Dict[str, Any]:
        """Process incoming JSON data for PUSH operation with bulk operations"""
        start_time = time.time()
        results = {
            'success_count': 0,
            'error_count': 0,
            'errors': [],
            'processed_models': {},
            'query_count': 0
        }
        
        try:
            # Group data by model for bulk processing
            model_groups = {}
            for item_data in json_data:
                model_name = item_data.get('_model')
                if model_name:
                    if model_name not in model_groups:
                        model_groups[model_name] = []
                    model_groups[model_name].append(item_data)
            
            # Process each model group with bulk operations
            for model_name, model_data in model_groups.items():
                try:
                    model_class = apps.get_model(model_name)
                    
                    # Validate data structure
                    validation_errors = []
                    for item_data in model_data:
                        is_valid, errors = ModelIntrospector.validate_json_against_model(
                            item_data, model_name
                        )
                        if not is_valid:
                            validation_errors.extend(errors)
                    
                    if validation_errors:
                        results['errors'].extend(validation_errors)
                        results['error_count'] += len(model_data)
                        continue
                    
                    # Use bulk operations for better performance
                    bulk_results = BulkOperations.bulk_create_or_update(
                        model_class, model_data, batch_size=1000
                    )
                    
                    results['success_count'] += bulk_results['created'] + bulk_results['updated']
                    results['processed_models'][model_name] = bulk_results
                    
                    # Invalidate model cache
                    CacheOptimizer.invalidate_model_cache(model_name)
                    
                except Exception as e:
                    results['errors'].append(f"Error processing model {model_name}: {str(e)}")
                    results['error_count'] += len(model_data)
                    logger.error(f"Error processing model {model_name}: {str(e)}", exc_info=True)
        
        except Exception as e:
            raise SyncError(
                f"Data processing failed: {str(e)}",
                category=ErrorCategory.UNKNOWN,
                severity=ErrorSeverity.HIGH,
                context={'user_id': user.id, 'data_count': len(json_data)}
            )
        
        results['processing_time'] = time.time() - start_time
        
        # Track performance metrics
        PerformanceMonitor.track_performance(
            operation_type='PUSH',
            model_name='multiple',
            batch_size=len(json_data),
            processing_time=results['processing_time'],
            query_count=results.get('query_count', 0)
        )
        
        return results

    @staticmethod
    @retry_handler.retry
    @QueryOptimizer.count_queries
    def process_pull_data(model_name: str, filters: Dict = None, 
                         limit: int = None, user = None) -> Dict[str, Any]:
        """Process data for PULL operations with caching and optimization"""
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = f"pull_data_{model_name}_{hash(str(filters))}_{limit}"
            cached_data = CacheOptimizer.get_cached_model_data(cache_key)
            
            if cached_data:
                return cached_data
            
            # Get model class
            model_class = apps.get_model(model_name)
            
            # Build optimized query
            queryset = model_class.objects.all()
            
            # Apply filters
            if filters:
                queryset = queryset.filter(**filters)
            
            # Apply limit
            if limit:
                queryset = queryset[:limit]
            
            # Use values() for better performance
            data = []
            for obj in queryset.values():
                obj_data = {'_model': model_name}
                obj_data.update(obj)
                data.append(obj_data)
            
            result = {
                'data': data,
                'count': len(data),
                'model_name': model_name,
                'filters': filters,
                'limit': limit,
                'processing_time': time.time() - start_time
            }
            
            # Cache the result
            CacheOptimizer.cache_model_data(cache_key, result, timeout=1800)  # 30 minutes
            
            return result
            
        except LookupError:
            raise ConfigurationError(
                f"Model '{model_name}' not found",
                context={'model_name': model_name}
            )
        except DatabaseError as e:
            raise DatabaseError(
                f"Database error during pull operation: {str(e)}",
                context={'model_name': model_name, 'user_id': getattr(user, 'id', None)}
            )
        except Exception as e:
            raise SyncError(
                f"Pull operation failed: {str(e)}",
                category=ErrorCategory.UNKNOWN,
                severity=ErrorSeverity.MEDIUM,
                context={'model_name': model_name, 'user_id': getattr(user, 'id', None)}
            )

    @staticmethod
    def validate_data_integrity(data: List[Dict]) -> Tuple[bool, List[str]]:
        """Validate data integrity before processing with caching"""
        errors = []
        
        for i, item in enumerate(data):
            # Check for required fields
            if '_model' not in item:
                errors.append(f"Item {i}: Missing '_model' field")
            
            # Check for valid model names
            model_name = item.get('_model')
            if model_name:
                try:
                    apps.get_model(model_name)
                except LookupError:
                    errors.append(f"Item {i}: Invalid model name '{model_name}'")
            
            # Check for valid JSON structure
            if not isinstance(item, dict):
                errors.append(f"Item {i}: Invalid data structure (expected dict)")
        
        return len(errors) == 0, errors

    @staticmethod
    def sanitize_data(data: List[Dict]) -> List[Dict]:
        """Sanitize data before processing"""
        sanitized = []
        
        for item in data:
            if isinstance(item, dict):
                # Remove None values and empty strings
                sanitized_item = {k: v for k, v in item.items() 
                                if v is not None and v != ''}
                sanitized.append(sanitized_item)
        
        return sanitized

    @staticmethod
    def compress_data(data: List[Dict]) -> bytes:
        """Compress data for storage/transmission"""
        import gzip
        import json
        
        json_str = json.dumps(data)
        return gzip.compress(json_str.encode('utf-8'))

    @staticmethod
    def decompress_data(compressed_data: bytes) -> List[Dict]:
        """Decompress data"""
        import gzip
        import json
        
        json_str = gzip.decompress(compressed_data).decode('utf-8')
        return json.loads(json_str)

    @staticmethod
    def batch_process_data(data: List[Dict], batch_size: int = 1000, 
                          processor_func=None) -> List[Dict]:
        """Process data in batches to avoid memory issues"""
        results = []
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            
            if processor_func:
                batch_result = processor_func(batch)
                results.append(batch_result)
            else:
                results.append(batch)
            
            # Force garbage collection after each batch
            import gc
            gc.collect()
        
        return results

class CacheManager:
    """Advanced cache management for sync operations"""
    
    @staticmethod
    def get_model_cache_key(model_name: str, operation: str, **kwargs) -> str:
        """Generate cache key for model operations"""
        key_parts = [model_name, operation]
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}_{value}")
        return f"sb_sync_{'_'.join(key_parts)}"
    
    @staticmethod
    def invalidate_model_cache(model_name: str):
        """Invalidate all cache entries for a model"""
        # This is a simplified version - in production, you might want to use
        # cache versioning or pattern-based invalidation
        CacheOptimizer.invalidate_model_cache(model_name)
    
    @staticmethod
    def get_cache_stats() -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cache_hits': cache.get('cache_hits', 0),
            'cache_misses': cache.get('cache_misses', 0),
            'memory_usage': MemoryOptimizer.get_memory_usage()
        }
