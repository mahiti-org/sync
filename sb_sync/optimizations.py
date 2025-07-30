from django.db import connection
from django.core.cache import cache
from django.apps import apps
from django.db.models import Prefetch, Q
from django.conf import settings
import json
import time
import psutil
import gc
from typing import Dict, List, Any, Tuple
from functools import wraps
import logging

logger = logging.getLogger('sb_sync')

class ModelMetadataCache:
    """Cache model metadata for better performance"""
    
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
    def invalidate_model_cache(model_name):
        """Invalidate model field cache"""
        cache_key = f"sb_sync_model_fields_{model_name}"
        cache.delete(cache_key)

class QueryOptimizer:
    """Optimize database queries for better performance"""
    
    @staticmethod
    def optimize_queryset(queryset, select_related=None, prefetch_related=None):
        """Apply select_related and prefetch_related optimizations"""
        if select_related:
            queryset = queryset.select_related(*select_related)
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)
        return queryset
    
    @staticmethod
    def get_optimized_sync_logs(user_id=None, operation=None, limit=100):
        """Get optimized sync logs with proper joins"""
        from .models import SyncLog
        
        queryset = SyncLog.objects.select_related('user')
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if operation:
            queryset = queryset.filter(operation=operation)
        
        return queryset.order_by('-timestamp')[:limit]
    
    @staticmethod
    def count_queries(func):
        """Decorator to count database queries"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            initial_queries = len(connection.queries)
            result = func(*args, **kwargs)
            final_queries = len(connection.queries)
            query_count = final_queries - initial_queries
            logger.info(f"Function {func.__name__} executed {query_count} queries")
            return result
        return wrapper

class BulkOperations:
    """Optimized bulk operations for high volume processing"""
    
    @staticmethod
    def bulk_create_or_update(model_class, data_list, batch_size=1000):
        """Perform bulk create/update operations"""
        creates = []
        updates = []
        
        # Separate creates and updates
        for item_data in data_list:
            obj_id = item_data.get('id')
            if obj_id:
                updates.append(item_data)
            else:
                creates.append(item_data)
        
        results = {'created': 0, 'updated': 0}
        
        # Bulk create
        if creates:
            create_objects = []
            for batch_start in range(0, len(creates), batch_size):
                batch = creates[batch_start:batch_start + batch_size]
                for item in batch:
                    item.pop('id', None)  # Remove ID for creation
                    create_objects.append(model_class(**item))
                
                if create_objects:
                    model_class.objects.bulk_create(create_objects, batch_size=batch_size)
                    results['created'] += len(create_objects)
                    create_objects = []
        
        # Bulk update
        if updates:
            for batch_start in range(0, len(updates), batch_size):
                batch = updates[batch_start:batch_start + batch_size]
                for item in batch:
                    obj_id = item.pop('id')
                    model_class.objects.filter(id=obj_id).update(**item)
                    results['updated'] += 1
        
        return results

    @staticmethod
    def bulk_create_with_ignore_conflicts(model_class, data_list, batch_size=1000):
        """Bulk create with ignore conflicts for better performance"""
        results = {'created': 0, 'skipped': 0}
        
        for batch_start in range(0, len(data_list), batch_size):
            batch = data_list[batch_start:batch_start + batch_size]
            create_objects = []
            
            for item in batch:
                create_objects.append(model_class(**item))
            
            if create_objects:
                try:
                    model_class.objects.bulk_create(create_objects, batch_size=batch_size, ignore_conflicts=True)
                    results['created'] += len(create_objects)
                except Exception as e:
                    logger.warning(f"Bulk create error: {e}")
                    results['skipped'] += len(create_objects)
        
        return results

class MemoryOptimizer:
    """Memory optimization utilities"""
    
    @staticmethod
    def get_memory_usage():
        """Get current memory usage in MB"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    @staticmethod
    def optimize_memory():
        """Force garbage collection to free memory"""
        gc.collect()
        return MemoryOptimizer.get_memory_usage()
    
    @staticmethod
    def monitor_memory(func):
        """Decorator to monitor memory usage"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            initial_memory = MemoryOptimizer.get_memory_usage()
            result = func(*args, **kwargs)
            final_memory = MemoryOptimizer.get_memory_usage()
            memory_used = final_memory - initial_memory
            
            logger.info(f"Function {func.__name__} used {memory_used:.2f}MB of memory")
            return result
        return wrapper

class CacheOptimizer:
    """Advanced caching strategies"""
    
    @staticmethod
    def get_or_set_cache(key, callback, timeout=3600):
        """Get from cache or set if not exists"""
        result = cache.get(key)
        if result is None:
            result = callback()
            cache.set(key, result, timeout=timeout)
        return result
    
    @staticmethod
    def cache_model_data(model_name, data, timeout=1800):
        """Cache model data with TTL"""
        cache_key = f"sb_sync_model_data_{model_name}"
        cache.set(cache_key, data, timeout=timeout)
    
    @staticmethod
    def get_cached_model_data(model_name):
        """Get cached model data"""
        cache_key = f"sb_sync_model_data_{model_name}"
        return cache.get(cache_key)
    
    @staticmethod
    def invalidate_model_cache(model_name):
        """Invalidate model cache"""
        cache_key = f"sb_sync_model_data_{model_name}"
        cache.delete(cache_key)

class PerformanceMonitor:
    """Monitor and track performance metrics"""
    
    @staticmethod
    def track_performance(operation_type, model_name, batch_size, processing_time, query_count):
        """Track performance metrics"""
        from .models import PerformanceMetrics
        
        memory_usage = MemoryOptimizer.get_memory_usage()
        
        PerformanceMetrics.objects.create(
            operation_type=operation_type,
            model_name=model_name,
            batch_size=batch_size,
            processing_time=processing_time,
            memory_usage=memory_usage,
            query_count=query_count
        )
    
    @staticmethod
    def get_performance_stats(days=7):
        """Get performance statistics"""
        from django.utils import timezone
        from datetime import timedelta
        from .models import PerformanceMetrics
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        return PerformanceMetrics.objects.filter(
            timestamp__gte=cutoff_date
        ).aggregate(
            avg_processing_time=models.Avg('processing_time'),
            avg_memory_usage=models.Avg('memory_usage'),
            avg_query_count=models.Avg('query_count'),
            total_operations=models.Count('id')
        )

class DatabaseOptimizer:
    """Database-specific optimizations"""
    
    @staticmethod
    def optimize_connection():
        """Optimize database connection settings"""
        # Set connection parameters for better performance
        connection.ensure_connection()
        
        # Set session-level optimizations
        with connection.cursor() as cursor:
            cursor.execute("SET SESSION sql_mode = 'STRICT_TRANS_TABLES'")
            cursor.execute("SET SESSION innodb_lock_wait_timeout = 50")
    
    @staticmethod
    def analyze_table_performance():
        """Analyze table performance and suggest optimizations"""
        with connection.cursor() as cursor:
            # Get table statistics
            cursor.execute("""
                SELECT 
                    table_name,
                    table_rows,
                    data_length,
                    index_length
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
                AND table_name LIKE 'sb_sync_%'
            """)
            
            return cursor.fetchall()
    
    @staticmethod
    def optimize_indexes():
        """Suggest index optimizations"""
        with connection.cursor() as cursor:
            # Analyze index usage
            cursor.execute("""
                SELECT 
                    table_name,
                    index_name,
                    cardinality
                FROM information_schema.statistics 
                WHERE table_schema = DATABASE()
                AND table_name LIKE 'sb_sync_%'
                ORDER BY cardinality DESC
            """)
            
            return cursor.fetchall()

class AsyncProcessor:
    """Async processing utilities"""
    
    @staticmethod
    def process_in_chunks(data_list, chunk_size=1000, processor_func=None):
        """Process data in chunks to avoid memory issues"""
        results = []
        
        for i in range(0, len(data_list), chunk_size):
            chunk = data_list[i:i + chunk_size]
            
            if processor_func:
                chunk_result = processor_func(chunk)
                results.append(chunk_result)
            else:
                results.append(chunk)
            
            # Force garbage collection after each chunk
            gc.collect()
        
        return results
    
    @staticmethod
    def batch_process_models(model_names, processor_func, batch_size=100):
        """Process multiple models in batches"""
        results = {}
        
        for model_name in model_names:
            try:
                model_class = apps.get_model(model_name)
                queryset = model_class.objects.all()
                
                # Process in batches
                for batch_start in range(0, queryset.count(), batch_size):
                    batch = queryset[batch_start:batch_start + batch_size]
                    batch_result = processor_func(batch, model_name)
                    
                    if model_name not in results:
                        results[model_name] = []
                    results[model_name].append(batch_result)
                
            except LookupError:
                logger.warning(f"Model {model_name} not found")
                results[model_name] = {'error': 'Model not found'}
        
        return results
