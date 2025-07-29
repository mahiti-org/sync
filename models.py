from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Index

class SyncLog(models.Model):
    OPERATION_CHOICES = [
        ('PUSH', 'Push'),
        ('PULL', 'Pull'),
    ]
    
    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('ERROR', 'Error'),
        ('WARNING', 'Warning'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    operation = models.CharField(max_length=10, choices=OPERATION_CHOICES, db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, db_index=True)
    model_name = models.CharField(max_length=100, blank=True, db_index=True)
    object_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    request_data = models.JSONField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    processing_time = models.FloatField(default=0.0)  # in seconds
    
    class Meta:
        db_table = 'sb_sync_log'
        indexes = [
            models.Index(fields=['timestamp', 'operation']),
            models.Index(fields=['user', 'operation']),
            models.Index(fields=['status', 'timestamp']),
            models.Index(fields=['model_name', 'timestamp']),
            models.Index(fields=['user', 'status', 'timestamp']),
            # Composite index for common query patterns
            models.Index(fields=['operation', 'status', 'timestamp']),
        ]
        # Add ordering for better performance
        ordering = ['-timestamp']

    def save(self, *args, **kwargs):
        # Invalidate cache on save
        cache_key = f"sync_log_stats_{self.user.id}"
        cache.delete(cache_key)
        super().save(*args, **kwargs)

class SyncMetadata(models.Model):
    """Track last sync timestamps for models"""
    model_name = models.CharField(max_length=100, unique=True, db_index=True)
    last_sync = models.DateTimeField(default=timezone.now, db_index=True)
    total_synced = models.BigIntegerField(default=0)
    
    class Meta:
        db_table = 'sb_sync_metadata'
        indexes = [
            models.Index(fields=['model_name', 'last_sync']),
        ]

    def save(self, *args, **kwargs):
        # Invalidate cache on save
        cache_key = f"sync_metadata_{self.model_name}"
        cache.delete(cache_key)
        super().save(*args, **kwargs)

class PerformanceMetrics(models.Model):
    """Track performance metrics for optimization"""
    operation_type = models.CharField(max_length=20, db_index=True)
    model_name = models.CharField(max_length=100, db_index=True)
    batch_size = models.IntegerField()
    processing_time = models.FloatField()
    memory_usage = models.FloatField(null=True, blank=True)
    query_count = models.IntegerField()
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        db_table = 'sb_sync_performance_metrics'
        indexes = [
            models.Index(fields=['operation_type', 'timestamp']),
            models.Index(fields=['model_name', 'timestamp']),
        ]
        ordering = ['-timestamp']
