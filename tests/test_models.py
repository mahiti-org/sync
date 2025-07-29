from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from sb_sync.models import SyncLog, SyncMetadata
from datetime import timedelta


class SyncLogModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_sync_log_creation(self):
        """Test creating a sync log entry"""
        sync_log = SyncLog.objects.create(
            user=self.user,
            operation='PUSH',
            status='SUCCESS',
            model_name='test.Model',
            object_count=5,
            processing_time=1.5
        )
        
        self.assertEqual(sync_log.user, self.user)
        self.assertEqual(sync_log.operation, 'PUSH')
        self.assertEqual(sync_log.status, 'SUCCESS')
        self.assertEqual(sync_log.object_count, 5)
        self.assertEqual(sync_log.processing_time, 1.5)
        self.assertIsNotNone(sync_log.timestamp)

    def test_sync_log_with_error(self):
        """Test creating a sync log entry with error"""
        sync_log = SyncLog.objects.create(
            user=self.user,
            operation='PULL',
            status='ERROR',
            model_name='test.Model',
            error_message='Test error message',
            processing_time=0.5
        )
        
        self.assertEqual(sync_log.status, 'ERROR')
        self.assertEqual(sync_log.error_message, 'Test error message')
        self.assertEqual(sync_log.object_count, 0)

    def test_sync_log_choices(self):
        """Test sync log choice fields"""
        # Test valid operations
        valid_operations = ['PUSH', 'PULL']
        for operation in valid_operations:
            sync_log = SyncLog.objects.create(
                user=self.user,
                operation=operation,
                status='SUCCESS'
            )
            self.assertEqual(sync_log.operation, operation)

        # Test valid statuses
        valid_statuses = ['SUCCESS', 'ERROR', 'WARNING']
        for status in valid_statuses:
            sync_log = SyncLog.objects.create(
                user=self.user,
                operation='PUSH',
                status=status
            )
            self.assertEqual(sync_log.status, status)

    def test_sync_log_json_field(self):
        """Test sync log request_data JSON field"""
        test_data = {'key': 'value', 'number': 123}
        sync_log = SyncLog.objects.create(
            user=self.user,
            operation='PUSH',
            status='SUCCESS',
            request_data=test_data
        )
        
        self.assertEqual(sync_log.request_data, test_data)


class SyncMetadataModelTest(TestCase):
    def test_sync_metadata_creation(self):
        """Test creating sync metadata"""
        metadata = SyncMetadata.objects.create(
            model_name='test.Model',
            total_synced=100
        )
        
        self.assertEqual(metadata.model_name, 'test.Model')
        self.assertEqual(metadata.total_synced, 100)
        self.assertIsNotNone(metadata.last_sync)

    def test_sync_metadata_unique_constraint(self):
        """Test that model_name is unique"""
        SyncMetadata.objects.create(model_name='test.Model')
        
        # Should raise IntegrityError for duplicate
        with self.assertRaises(Exception):
            SyncMetadata.objects.create(model_name='test.Model')

    def test_sync_metadata_update(self):
        """Test updating sync metadata"""
        metadata = SyncMetadata.objects.create(
            model_name='test.Model',
            total_synced=50
        )
        
        # Update metadata
        metadata.total_synced += 25
        metadata.save()
        
        updated_metadata = SyncMetadata.objects.get(model_name='test.Model')
        self.assertEqual(updated_metadata.total_synced, 75) 