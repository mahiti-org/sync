from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db import connection
from django.utils import timezone
from datetime import timedelta
import psutil
import gc
import time
from ...optimizations import (
    MemoryOptimizer, PerformanceMonitor, DatabaseOptimizer,
    CacheOptimizer, QueryOptimizer
)
from ...models import SyncLog, PerformanceMetrics
import logging

logger = logging.getLogger('sb_sync')

class Command(BaseCommand):
    help = 'Optimize performance and monitor system resources'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['analyze', 'optimize', 'cleanup', 'monitor'],
            default='analyze',
            help='Action to perform'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to analyze'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force optimization even if not needed'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        days = options['days']
        force = options['force']
        
        self.stdout.write(f"Starting performance {action}...")
        
        if action == 'analyze':
            self.analyze_performance(days)
        elif action == 'optimize':
            self.optimize_performance(force)
        elif action == 'cleanup':
            self.cleanup_old_data()
        elif action == 'monitor':
            self.monitor_resources()
    
    def analyze_performance(self, days):
        """Analyze current performance metrics"""
        self.stdout.write("Analyzing performance metrics...")
        
        # Get performance statistics
        stats = PerformanceMonitor.get_performance_stats(days)
        
        # Get memory usage
        memory_usage = MemoryOptimizer.get_memory_usage()
        
        # Get cache statistics
        cache_hits = cache.get('cache_hits', 0)
        cache_misses = cache.get('cache_misses', 0)
        total_cache_requests = cache_hits + cache_misses
        cache_hit_rate = cache_hits / total_cache_requests if total_cache_requests > 0 else 0
        
        # Get database statistics
        with connection.cursor() as cursor:
            cursor.execute("SHOW STATUS LIKE 'Questions'")
            total_queries = cursor.fetchone()[1]
            
            cursor.execute("SHOW STATUS LIKE 'Slow_queries'")
            slow_queries = cursor.fetchone()[1]
        
        # Display analysis results
        self.stdout.write(self.style.SUCCESS("=== Performance Analysis ==="))
        self.stdout.write(f"Memory Usage: {memory_usage:.2f}MB")
        self.stdout.write(f"Cache Hit Rate: {cache_hit_rate:.2%}")
        self.stdout.write(f"Average Processing Time: {stats.get('avg_processing_time', 0):.3f}s")
        self.stdout.write(f"Total Operations: {stats.get('total_operations', 0)}")
        self.stdout.write(f"Database Queries: {total_queries}")
        self.stdout.write(f"Slow Queries: {slow_queries}")
        
        # Generate recommendations
        recommendations = self._generate_recommendations(stats, memory_usage, cache_hit_rate)
        
        if recommendations:
            self.stdout.write(self.style.WARNING("=== Recommendations ==="))
            for rec in recommendations:
                self.stdout.write(f"- {rec}")
        else:
            self.stdout.write(self.style.SUCCESS("No optimization recommendations at this time."))
    
    def optimize_performance(self, force):
        """Perform performance optimizations"""
        self.stdout.write("Starting performance optimization...")
        
        # Memory optimization
        initial_memory = MemoryOptimizer.get_memory_usage()
        MemoryOptimizer.optimize_memory()
        final_memory = MemoryOptimizer.get_memory_usage()
        memory_freed = initial_memory - final_memory
        
        self.stdout.write(f"Memory optimization: Freed {memory_freed:.2f}MB")
        
        # Database optimization
        try:
            DatabaseOptimizer.optimize_connection()
            self.stdout.write("Database connection optimized")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Database optimization failed: {e}"))
        
        # Cache optimization
        cache.delete_pattern('sb_sync_temp_*')
        self.stdout.write("Cache cleaned")
        
        # Force garbage collection
        gc.collect()
        self.stdout.write("Garbage collection completed")
        
        self.stdout.write(self.style.SUCCESS("Performance optimization completed"))
    
    def cleanup_old_data(self):
        """Clean up old data and logs"""
        self.stdout.write("Cleaning up old data...")
        
        # Clean up old sync logs
        cutoff_date = timezone.now() - timedelta(days=90)
        deleted_logs = SyncLog.objects.filter(timestamp__lt=cutoff_date).delete()[0]
        self.stdout.write(f"Deleted {deleted_logs} old sync logs")
        
        # Clean up old performance metrics
        cutoff_date = timezone.now() - timedelta(days=30)
        deleted_metrics = PerformanceMetrics.objects.filter(timestamp__lt=cutoff_date).delete()[0]
        self.stdout.write(f"Deleted {deleted_metrics} old performance metrics")
        
        # Clear old cache entries
        cache.delete_pattern('sb_sync_old_*')
        self.stdout.write("Cleared old cache entries")
        
        self.stdout.write(self.style.SUCCESS("Cleanup completed"))
    
    def monitor_resources(self):
        """Monitor system resources"""
        self.stdout.write("Monitoring system resources...")
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # Database connections
        with connection.cursor() as cursor:
            cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
            db_connections = cursor.fetchone()[1]
        
        # Display resource usage
        self.stdout.write(self.style.SUCCESS("=== Resource Usage ==="))
        self.stdout.write(f"CPU Usage: {cpu_percent}%")
        self.stdout.write(f"Memory Usage: {memory.percent}% ({memory.used / 1024 / 1024 / 1024:.1f}GB / {memory.total / 1024 / 1024 / 1024:.1f}GB)")
        self.stdout.write(f"Disk Usage: {disk.percent}% ({disk.used / 1024 / 1024 / 1024:.1f}GB / {disk.total / 1024 / 1024 / 1024:.1f}GB)")
        self.stdout.write(f"Database Connections: {db_connections}")
        
        # Check for potential issues
        warnings = []
        if cpu_percent > 80:
            warnings.append("High CPU usage detected")
        if memory.percent > 85:
            warnings.append("High memory usage detected")
        if disk.percent > 90:
            warnings.append("High disk usage detected")
        if int(db_connections) > 100:
            warnings.append("High number of database connections")
        
        if warnings:
            self.stdout.write(self.style.WARNING("=== Warnings ==="))
            for warning in warnings:
                self.stdout.write(f"- {warning}")
        else:
            self.stdout.write(self.style.SUCCESS("All resources within normal ranges"))
    
    def _generate_recommendations(self, stats, memory_usage, cache_hit_rate):
        """Generate performance recommendations"""
        recommendations = []
        
        # Memory recommendations
        if memory_usage > 500:  # 500MB threshold
            recommendations.append("High memory usage detected. Consider reducing batch sizes.")
        
        # Cache recommendations
        if cache_hit_rate < 0.7:  # 70% threshold
            recommendations.append("Low cache hit rate. Consider adjusting cache TTL or keys.")
        
        # Processing time recommendations
        avg_processing_time = stats.get('avg_processing_time', 0)
        if avg_processing_time > 5.0:  # 5 seconds threshold
            recommendations.append("High processing times detected. Consider optimizing queries.")
        
        # Database recommendations
        if stats.get('avg_query_count', 0) > 50:  # 50 queries threshold
            recommendations.append("High query count detected. Consider using select_related/prefetch_related.")
        
        return recommendations 