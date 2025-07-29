from celery import shared_task
from django.utils import timezone
from django.db import connection
from django.core.cache import cache
from datetime import timedelta
from .models import SyncLog, SyncMetadata, PerformanceMetrics
from .optimizations import (
    BulkOperations, MemoryOptimizer, PerformanceMonitor,
    DatabaseOptimizer, CacheOptimizer
)
import logging
import psutil
import gc
import time
from django.db import models

logger = logging.getLogger('sb_sync')

@shared_task(bind=True, max_retries=3)
def cleanup_old_sync_logs(self):
    """Clean up sync logs older than 90 days with bulk operations"""
    try:
        cutoff_date = timezone.now() - timedelta(days=90)
        
        # Use bulk delete for better performance
        deleted_count = SyncLog.objects.filter(timestamp__lt=cutoff_date).delete()[0]
        
        # Clear related caches
        cache.delete_pattern('sb_sync_sync_log_*')
        
        logger.info(f"Cleaned up {deleted_count} old sync log entries")
        
        # Track performance
        PerformanceMonitor.track_performance(
            operation_type='CLEANUP',
            model_name='SyncLog',
            batch_size=deleted_count,
            processing_time=0.0,  # Will be calculated by decorator
            query_count=1
        )
        
        return deleted_count
        
    except Exception as exc:
        logger.error(f"Cleanup task failed: {exc}")
        raise self.retry(countdown=60, exc=exc)

@shared_task(bind=True, max_retries=3)
def generate_sync_report(self):
    """Generate daily sync report with optimized queries"""
    try:
        today = timezone.now().date()
        start_of_day = timezone.make_aware(timezone.datetime.combine(today, timezone.time.min))
        end_of_day = timezone.make_aware(timezone.datetime.combine(today, timezone.time.max))
        
        # Use optimized queries with select_related
        daily_logs = SyncLog.objects.filter(
            timestamp__range=[start_of_day, end_of_day]
        ).select_related('user')
        
        # Calculate statistics efficiently
        stats = {
            'total_operations': daily_logs.count(),
            'push_operations': daily_logs.filter(operation='PUSH').count(),
            'pull_operations': daily_logs.filter(operation='PULL').count(),
            'successful_operations': daily_logs.filter(status='SUCCESS').count(),
            'failed_operations': daily_logs.filter(status='ERROR').count(),
            'total_objects_processed': daily_logs.aggregate(
                total=models.Sum('object_count')
            )['total'] or 0,
            'average_processing_time': daily_logs.aggregate(
                avg_time=models.Avg('processing_time')
            )['avg_time'] or 0,
        }
        
        # Cache the report
        cache_key = f"sync_report_{today.strftime('%Y%m%d')}"
        cache.set(cache_key, stats, timeout=86400)  # 24 hours
        
        logger.info(f"Daily sync report generated: {stats}")
        return stats
        
    except Exception as exc:
        logger.error(f"Report generation failed: {exc}")
        raise self.retry(countdown=300, exc=exc)

@shared_task(bind=True, max_retries=3)
def optimize_database_tables(self):
    """Optimize database tables for better performance"""
    try:
        # Analyze table performance
        table_stats = DatabaseOptimizer.analyze_table_performance()
        
        # Optimize indexes
        index_stats = DatabaseOptimizer.optimize_indexes()
        
        # Clean up old performance metrics
        cutoff_date = timezone.now() - timedelta(days=30)
        deleted_metrics = PerformanceMetrics.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"Database optimization completed. Deleted {deleted_metrics} old metrics")
        
        return {
            'table_stats': table_stats,
            'index_stats': index_stats,
            'deleted_metrics': deleted_metrics
        }
        
    except Exception as exc:
        logger.error(f"Database optimization failed: {exc}")
        raise self.retry(countdown=3600, exc=exc)

@shared_task(bind=True, max_retries=3)
def bulk_sync_operation(self, model_name, operation_type, data_batch):
    """Perform bulk sync operations asynchronously"""
    try:
        from django.apps import apps
        
        model_class = apps.get_model(model_name)
        start_time = time.time()
        
        if operation_type == 'CREATE':
            # Bulk create
            objects_to_create = [model_class(**item) for item in data_batch]
            created_count = len(model_class.objects.bulk_create(
                objects_to_create, 
                batch_size=1000,
                ignore_conflicts=True
            ))
            
        elif operation_type == 'UPDATE':
            # Bulk update
            updated_count = 0
            for item in data_batch:
                obj_id = item.pop('id')
                model_class.objects.filter(id=obj_id).update(**item)
                updated_count += 1
            created_count = updated_count
            
        else:
            raise ValueError(f"Invalid operation type: {operation_type}")
        
        processing_time = time.time() - start_time
        
        # Track performance
        PerformanceMonitor.track_performance(
            operation_type=f'BULK_{operation_type}',
            model_name=model_name,
            batch_size=len(data_batch),
            processing_time=processing_time,
            query_count=1
        )
        
        logger.info(f"Bulk {operation_type} completed for {model_name}: {created_count} records")
        
        return {
            'operation_type': operation_type,
            'model_name': model_name,
            'processed_count': created_count,
            'processing_time': processing_time
        }
        
    except Exception as exc:
        logger.error(f"Bulk sync operation failed: {exc}")
        raise self.retry(countdown=60, exc=exc)

@shared_task(bind=True, max_retries=3)
def cache_warmup(self):
    """Warm up cache with frequently accessed data"""
    try:
        from django.apps import apps
        
        # Cache model field information
        for app_config in apps.get_app_configs():
            for model in app_config.get_models():
                if model._meta.app_label == 'sb_sync':
                    ModelIntrospector.get_model_fields(model._meta.model_name)
        
        # Cache recent sync logs
        recent_logs = SyncLog.objects.select_related('user').order_by('-timestamp')[:100]
        cache.set('recent_sync_logs', list(recent_logs.values()), timeout=1800)
        
        # Cache sync metadata
        metadata = SyncMetadata.objects.all()
        cache.set('sync_metadata', list(metadata.values()), timeout=3600)
        
        logger.info("Cache warmup completed successfully")
        
        return {
            'cached_models': len(apps.get_app_configs()),
            'cached_logs': len(recent_logs),
            'cached_metadata': len(metadata)
        }
        
    except Exception as exc:
        logger.error(f"Cache warmup failed: {exc}")
        raise self.retry(countdown=300, exc=exc)

@shared_task(bind=True, max_retries=3)
def memory_optimization(self):
    """Perform memory optimization tasks"""
    try:
        initial_memory = MemoryOptimizer.get_memory_usage()
        
        # Force garbage collection
        gc.collect()
        
        # Clear old cache entries
        cache.delete_pattern('sb_sync_temp_*')
        
        # Optimize memory
        final_memory = MemoryOptimizer.optimize_memory()
        memory_freed = initial_memory - final_memory
        
        logger.info(f"Memory optimization completed. Freed {memory_freed:.2f}MB")
        
        return {
            'initial_memory': initial_memory,
            'final_memory': final_memory,
            'memory_freed': memory_freed
        }
        
    except Exception as exc:
        logger.error(f"Memory optimization failed: {exc}")
        raise self.retry(countdown=1800, exc=exc)

@shared_task(bind=True, max_retries=3)
def performance_analysis(self):
    """Analyze performance metrics and generate recommendations"""
    try:
        # Get performance statistics
        stats = PerformanceMonitor.get_performance_stats(days=7)
        
        # Analyze memory usage
        memory_usage = MemoryOptimizer.get_memory_usage()
        
        # Get cache statistics
        cache_hits = cache.get('cache_hits', 0)
        cache_misses = cache.get('cache_misses', 0)
        total_cache_requests = cache_hits + cache_misses
        cache_hit_rate = cache_hits / total_cache_requests if total_cache_requests > 0 else 0
        
        # Generate recommendations
        recommendations = []
        
        if memory_usage > 500:  # 500MB threshold
            recommendations.append("High memory usage detected. Consider reducing batch sizes.")
        
        if cache_hit_rate < 0.7:  # 70% threshold
            recommendations.append("Low cache hit rate. Consider adjusting cache TTL or keys.")
        
        if stats.get('avg_processing_time', 0) > 5.0:  # 5 seconds threshold
            recommendations.append("High processing times detected. Consider optimizing queries.")
        
        analysis_result = {
            'performance_stats': stats,
            'memory_usage': memory_usage,
            'cache_hit_rate': cache_hit_rate,
            'recommendations': recommendations,
            'timestamp': timezone.now().isoformat()
        }
        
        # Cache the analysis
        cache.set('performance_analysis', analysis_result, timeout=3600)
        
        logger.info(f"Performance analysis completed. Generated {len(recommendations)} recommendations")
        
        return analysis_result
        
    except Exception as exc:
        logger.error(f"Performance analysis failed: {exc}")
        raise self.retry(countdown=3600, exc=exc)

# Import the ModelIntrospector class
from .utils import ModelIntrospector
