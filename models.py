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

# Multi-tenant and Role-based Access Control Models

class Organization(models.Model):
    """Represents a hospital, clinic, or healthcare organization"""
    name = models.CharField(max_length=200, unique=True)
    slug = models.CharField(max_length=50, unique=True, db_index=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sb_sync_organization'
        indexes = [
            models.Index(fields=['slug', 'is_active']),
        ]
    
    def __str__(self):
        return self.name

class UserOrganization(models.Model):
    """Links users to organizations with roles"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, db_index=True)
    role = models.CharField(max_length=50, choices=[
        ('ADMIN', 'Administrator'),
        ('DOCTOR', 'Doctor'),
        ('NURSE', 'Nurse'),
        ('LAB_TECH', 'Lab Technician'),
        ('PHARMACIST', 'Pharmacist'),
        ('READ_ONLY', 'Read Only'),
    ], db_index=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sb_sync_user_organization'
        unique_together = ['user', 'organization']
        indexes = [
            models.Index(fields=['user', 'organization']),
            models.Index(fields=['organization', 'role']),
            models.Index(fields=['role', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.organization.name} ({self.role})"

class ModelPermission(models.Model):
    """Defines which models each role can access"""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, db_index=True)
    role = models.CharField(max_length=50, db_index=True)
    model_name = models.CharField(max_length=100, db_index=True)
    can_push = models.BooleanField(default=False)
    can_pull = models.BooleanField(default=False)
    can_create = models.BooleanField(default=False)
    can_update = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_read = models.BooleanField(default=True)
    filters = models.JSONField(blank=True, null=True)  # Custom filters for data access
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sb_sync_model_permission'
        unique_together = ['organization', 'role', 'model_name']
        indexes = [
            models.Index(fields=['organization', 'role']),
            models.Index(fields=['model_name', 'can_push']),
            models.Index(fields=['model_name', 'can_pull']),
        ]
    
    def __str__(self):
        return f"{self.organization.name} - {self.role} - {self.model_name}"

class UserSyncMetadata(models.Model):
    """Track last sync timestamps for models per user/organization"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, db_index=True)
    model_name = models.CharField(max_length=100, db_index=True)
    last_sync = models.DateTimeField(default=timezone.now, db_index=True)
    total_synced = models.BigIntegerField(default=0)
    
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
    """Custom data filters for role-based access"""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, db_index=True)
    role = models.CharField(max_length=50, db_index=True)
    model_name = models.CharField(max_length=100, db_index=True)
    filter_name = models.CharField(max_length=100)
    filter_condition = models.JSONField()  # e.g., {"field": "patient_id", "operator": "in", "value": [1,2,3]}
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sb_sync_data_filter'
        indexes = [
            models.Index(fields=['organization', 'role', 'model_name']),
            models.Index(fields=['model_name', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.organization.name} - {self.role} - {self.model_name} - {self.filter_name}"
