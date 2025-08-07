from django.db import models
from django.contrib.auth.models import User, Group
from django.contrib.sites.models import Site
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Index
from simple_history.models import HistoricalRecords
from simple_history import register
import json
import logging

logger = logging.getLogger(__name__)

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
    
    # History tracking
    history = HistoricalRecords(
        table_name='sb_sync_log_history',
        verbose_name='Sync Log History',
        related_name='sync_log_history'
    )
    
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
    
    # History tracking
    history = HistoricalRecords(
        table_name='sb_sync_metadata_history',
        verbose_name='Sync Metadata History',
        related_name='sync_metadata_history'
    )
    
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
    
    # History tracking
    history = HistoricalRecords(
        table_name='sb_sync_performance_metrics_history',
        verbose_name='Performance Metrics History',
        related_name='performance_metrics_history'
    )
    
    class Meta:
        db_table = 'sb_sync_performance_metrics'
        indexes = [
            models.Index(fields=['operation_type', 'timestamp']),
            models.Index(fields=['model_name', 'timestamp']),
        ]
        ordering = ['-timestamp']

# Multi-tenant and Role-based Access Control Models

# Organization model removed - using Django Sites instead

class UserSite(models.Model):
    """Links users to Django Sites (sites) with Django Groups as roles"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    site = models.ForeignKey(Site, on_delete=models.CASCADE, db_index=True, help_text="Django Site representing the site")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Historical tracking
    history = HistoricalRecords()
    
    class Meta:
        db_table = 'sb_sync_user_site'
        verbose_name = 'User Site'
        verbose_name_plural = 'User Sites'
        unique_together = ['user', 'site']
        indexes = [
            models.Index(fields=['user', 'site']),
            models.Index(fields=['site', 'group']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.site.name} ({self.group.name})"

class ModelPermission(models.Model):
    """Define permissions for models per site/group"""
    
    site = models.ForeignKey(Site, on_delete=models.CASCADE, db_index=True, help_text="Django Site representing the site")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, db_index=True)
    model_name = models.CharField(max_length=255, db_index=True)
    can_push = models.BooleanField(default=False, db_index=True)
    can_pull = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Historical tracking
    history = HistoricalRecords()
    
    class Meta:
        db_table = 'sb_sync_model_permission'
        verbose_name = 'Model Permission'
        verbose_name_plural = 'Model Permissions'
        unique_together = ['site', 'group', 'model_name']
        indexes = [
            models.Index(fields=['site', 'group']),
            models.Index(fields=['model_name', 'site']),
        ]
    
    def __str__(self):
        return f"{self.site.name} - {self.group.name} - {self.model_name}"

class UserSyncMetadata(models.Model):
    """Track last sync timestamps for models per user/site"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    site = models.ForeignKey(Site, on_delete=models.CASCADE, db_index=True, help_text="Django Site representing the site")
    model_name = models.CharField(max_length=255, db_index=True)
    last_sync = models.DateTimeField(auto_now=True, db_index=True)
    total_synced = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Historical tracking
    history = HistoricalRecords()
    
    class Meta:
        db_table = 'sb_sync_user_sync_metadata'
        verbose_name = 'User Sync Metadata'
        verbose_name_plural = 'User Sync Metadata'
        unique_together = ['user', 'site', 'model_name']
        indexes = [
            models.Index(fields=['user', 'site', 'model_name']),
            models.Index(fields=['site', 'model_name', 'last_sync']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.site.name} - {self.model_name}"

class DataFilter(models.Model):
    """Define data filters for models per site/group"""
    
    site = models.ForeignKey(Site, on_delete=models.CASCADE, db_index=True, help_text="Django Site representing the site")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, db_index=True)
    model_name = models.CharField(max_length=255, db_index=True)
    filter_name = models.CharField(max_length=255, db_index=True)
    filter_condition = models.TextField(help_text="JSON filter condition")
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Historical tracking
    history = HistoricalRecords()
    
    class Meta:
        db_table = 'sb_sync_data_filter'
        verbose_name = 'Data Filter'
        verbose_name_plural = 'Data Filters'
        indexes = [
            models.Index(fields=['site', 'group', 'model_name']),
        ]
    
    def __str__(self):
        return f"{self.site.name} - {self.group.name} - {self.model_name} - {self.filter_name}"


class SyncConfiguration(models.Model):
    """Store configuration settings for the sync system"""
    
    key = models.CharField(max_length=255, unique=True, db_index=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sb_sync_configuration'
        verbose_name = 'Sync Configuration'
        verbose_name_plural = 'Sync Configurations'
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}..."
    
    @classmethod
    def get_value(cls, section, key, default=None):
        """Get configuration value from database"""
        try:
            config = cls.objects.get(section=section, key=key, is_active=True)
            return config.value
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_value(cls, section, key, value, description=""):
        """Set configuration value in database"""
        config, created = cls.objects.get_or_create(
            section=section,
            key=key,
            defaults={
                'value': value,
                'description': description,
                'is_active': True
            }
        )
        if not created:
            config.value = value
            config.description = description
            config.save()
        return config
    
    @classmethod
    def get_section(cls, section):
        """Get all configuration values for a section"""
        configs = cls.objects.filter(section=section, is_active=True)
        return {config.key: config.value for config in configs}
    
    @classmethod
    def delete_value(cls, section, key):
        """Delete a configuration value"""
        cls.objects.filter(section=section, key=key).update(is_active=False)
    
    def save(self, *args, **kwargs):
        # Invalidate cache on save
        cache_key = f"sync_config_{self.section}_{self.key}"
        cache.delete(cache_key)
        super().save(*args, **kwargs)
