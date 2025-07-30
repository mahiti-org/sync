from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Index
from simple_history.models import HistoricalRecords
from simple_history import register

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

class Organization(models.Model):
    """Represents any type of organization (company, hospital, school, etc.)"""
    name = models.CharField(max_length=200, unique=True)
    slug = models.CharField(max_length=50, unique=True, db_index=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # History tracking
    history = HistoricalRecords(
        table_name='sb_sync_organization_history',
        verbose_name='Organization History',
        related_name='organization_history'
    )
    
    class Meta:
        db_table = 'sb_sync_organization'
        indexes = [
            models.Index(fields=['slug', 'is_active']),
        ]
    
    def __str__(self):
        return self.name

class UserOrganization(models.Model):
    """Links users to organizations with Django Groups as roles"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, db_index=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, db_index=True, help_text="Django auth group representing the user's role")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # History tracking
    history = HistoricalRecords(
        table_name='sb_sync_user_organization_history',
        verbose_name='User Organization History',
        related_name='user_organization_history'
    )
    
    class Meta:
        db_table = 'sb_sync_user_organization'
        unique_together = ['user', 'organization']
        indexes = [
            models.Index(fields=['user', 'organization']),
            models.Index(fields=['organization', 'group']),
            models.Index(fields=['group', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.organization.name} ({self.group.name})"

class ModelPermission(models.Model):
    """Defines which models each group can access"""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, db_index=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, db_index=True, help_text="Django auth group")
    model_name = models.CharField(max_length=100, db_index=True)
    can_push = models.BooleanField(default=False)
    can_pull = models.BooleanField(default=False)
    can_create = models.BooleanField(default=False)
    can_update = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_read = models.BooleanField(default=True)
    filters = models.JSONField(blank=True, null=True)  # Custom filters for data access
    created_at = models.DateTimeField(auto_now_add=True)
    
    # History tracking
    history = HistoricalRecords(
        table_name='sb_sync_model_permission_history',
        verbose_name='Model Permission History',
        related_name='model_permission_history'
    )
    
    class Meta:
        db_table = 'sb_sync_model_permission'
        unique_together = ['organization', 'group', 'model_name']
        indexes = [
            models.Index(fields=['organization', 'group']),
            models.Index(fields=['model_name', 'can_push']),
            models.Index(fields=['model_name', 'can_pull']),
        ]
    
    def __str__(self):
        return f"{self.organization.name} - {self.group.name} - {self.model_name}"

class UserSyncMetadata(models.Model):
    """Track last sync timestamps for models per user/organization"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, db_index=True)
    model_name = models.CharField(max_length=100, db_index=True)
    last_sync = models.DateTimeField(default=timezone.now, db_index=True)
    total_synced = models.BigIntegerField(default=0)
    
    # History tracking
    history = HistoricalRecords(
        table_name='sb_sync_user_sync_metadata_history',
        verbose_name='User Sync Metadata History',
        related_name='user_sync_metadata_history'
    )
    
    class Meta:
        db_table = 'sb_sync_user_sync_metadata'
        unique_together = ['user', 'organization', 'model_name']
        indexes = [
            models.Index(fields=['user', 'organization', 'model_name']),
            models.Index(fields=['organization', 'model_name', 'last_sync']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.organization.name} - {self.model_name}"

class DataFilter(models.Model):
    """Custom data filters for group-based access"""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, db_index=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, db_index=True, help_text="Django auth group")
    model_name = models.CharField(max_length=100, db_index=True)
    filter_name = models.CharField(max_length=100)
    filter_condition = models.JSONField()  # e.g., {"field": "department", "operator": "exact", "value": "SALES"}
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # History tracking
    history = HistoricalRecords(
        table_name='sb_sync_data_filter_history',
        verbose_name='Data Filter History',
        related_name='data_filter_history'
    )
    
    class Meta:
        db_table = 'sb_sync_data_filter'
        indexes = [
            models.Index(fields=['organization', 'group', 'model_name']),
            models.Index(fields=['model_name', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.organization.name} - {self.group.name} - {self.model_name} - {self.filter_name}"
