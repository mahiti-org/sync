"""
Migration utilities for automatic migration detection and execution.
Handles version gaps and schema changes gracefully.
"""

import logging
from django.db import connection
from django.apps import apps
from django.core.management import call_command
from django.db.migrations.executor import MigrationExecutor
from django.db import migrations
from django.conf import settings

logger = logging.getLogger('sb_sync')

class MigrationDetector:
    """Detects current migration state and determines upgrade path."""
    
    def __init__(self):
        self.connection = connection
    
    def detect_current_version(self):
        """Detect the current version based on database schema."""
        try:
            with connection.cursor() as cursor:
                # Check for old organization-based schema
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='sb_sync_user_organization'
                """)
                has_old_org = cursor.fetchone() is not None
                
                # Check for new site-based schema
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='sb_sync_user_site'
                """)
                has_new_site = cursor.fetchone() is not None
                
                # Check migration history
                cursor.execute("""
                    SELECT name FROM django_migrations 
                    WHERE app='sb_sync' 
                    ORDER BY applied DESC LIMIT 1
                """)
                last_migration = cursor.fetchone()
                
                if has_old_org and not has_new_site:
                    return '1.x'  # Old organization-based version
                elif has_new_site:
                    return '2.x'  # New site-based version
                else:
                    return 'fresh'  # Fresh installation
                    
        except Exception as e:
            logger.warning(f"Error detecting version: {e}")
            return 'unknown'
    
    def detect_schema_changes(self):
        """Detect what schema changes are needed."""
        changes = {
            'organization_to_site': False,
            'field_renames': [],
            'table_creates': [],
            'table_drops': []
        }
        
        try:
            with connection.cursor() as cursor:
                # Check for organization to site migration
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='sb_sync_user_organization'
                """)
                if cursor.fetchone():
                    changes['organization_to_site'] = True
                
                # Check for other schema changes
                # Add more detection logic as needed
                
        except Exception as e:
            logger.warning(f"Error detecting schema changes: {e}")
        
        return changes

class AutoMigrator:
    """Handles automatic migration execution."""
    
    def __init__(self):
        self.detector = MigrationDetector()
    
    def needs_migration(self):
        """Check if migration is needed."""
        current_version = self.detector.detect_current_version()
        return current_version in ['1.x', 'unknown']
    
    def migrate_organization_to_site(self):
        """Migrate from organization-based to site-based schema."""
        try:
            with connection.cursor() as cursor:
                # Create default site if none exists
                cursor.execute("""
                    INSERT OR IGNORE INTO django_site (id, name, domain)
                    VALUES (1, 'Default Organization', 'example.com')
                """)
                
                # Create user and group if they don't exist (for testing)
                cursor.execute("""
                    INSERT OR IGNORE INTO auth_user (id, username, password, is_superuser, is_staff, is_active, date_joined)
                    VALUES (1, 'testuser', 'dummy', 1, 1, 1, datetime('now'))
                """)
                
                cursor.execute("""
                    INSERT OR IGNORE INTO auth_group (id, name)
                    VALUES (1, 'Test Group')
                """)
                
                # Migrate user_organization to user_site
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sb_sync_user_site (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        site_id INTEGER NOT NULL,
                        group_id INTEGER,
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES auth_user (id),
                        FOREIGN KEY (site_id) REFERENCES django_site (id),
                        FOREIGN KEY (group_id) REFERENCES auth_group (id)
                    )
                """)
                
                # Copy data from old table to new table
                cursor.execute("""
                    INSERT INTO sb_sync_user_site (user_id, site_id, group_id, is_active, created_at, updated_at)
                    SELECT user_id, organization_id, group_id, is_active, created_at, updated_at
                    FROM sb_sync_user_organization
                """)
                
                # Drop old table
                cursor.execute("DROP TABLE IF EXISTS sb_sync_user_organization")
                
                logger.info("Successfully migrated organization to site schema")
                
        except Exception as e:
            logger.error(f"Error migrating organization to site: {e}")
            raise
    
    def migrate_model_permissions(self):
        """Migrate model permissions from organization to site."""
        try:
            with connection.cursor() as cursor:
                # Check if old table exists
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='sb_sync_model_permission_old'
                """)
                if cursor.fetchone():
                    # Copy data from old table to new table
                    cursor.execute("""
                        INSERT INTO sb_sync_model_permission 
                        (model_name, can_push, can_pull, site_id, group_id, created_at, updated_at)
                        SELECT model_name, can_push, can_pull, organization_id, group_id, created_at, updated_at
                        FROM sb_sync_model_permission_old
                    """)
                    
                    # Drop old table
                    cursor.execute("DROP TABLE IF EXISTS sb_sync_model_permission_old")
                    
                    logger.info("Successfully migrated model permissions")
                    
        except Exception as e:
            logger.error(f"Error migrating model permissions: {e}")
            raise
    
    def auto_migrate(self):
        """Perform automatic migration based on detected state."""
        try:
            current_version = self.detector.detect_current_version()
            schema_changes = self.detector.detect_schema_changes()
            
            logger.info(f"Current version detected: {current_version}")
            logger.info(f"Schema changes needed: {schema_changes}")
            
            if current_version == '1.x':
                logger.info("Migrating from v1.x to v2.x...")
                
                # Step 1: Migrate organization to site
                if schema_changes['organization_to_site']:
                    self.migrate_organization_to_site()
                
                # Step 2: Migrate model permissions
                self.migrate_model_permissions()
                
                # Step 3: Apply Django migrations
                call_command('migrate', 'sb_sync', verbosity=0)
                
                logger.info("Automatic migration completed successfully")
                return True
                
            elif current_version == 'fresh':
                logger.info("Fresh installation detected, applying migrations...")
                call_command('migrate', 'sb_sync', verbosity=0)
                return True
                
            elif current_version == '2.x':
                logger.info("Already on v2.x, no migration needed")
                return True
                
            else:
                logger.warning("Unknown version state, manual intervention may be required")
                return False
                
        except Exception as e:
            logger.error(f"Auto-migration failed: {e}")
            return False

def setup_auto_migration():
    """Setup automatic migration on app startup."""
    try:
        migrator = AutoMigrator()
        if migrator.needs_migration():
            logger.info("Auto-migration needed, starting migration...")
            success = migrator.auto_migrate()
            if success:
                logger.info("Auto-migration completed successfully")
            else:
                logger.warning("Auto-migration failed, manual intervention may be required")
        else:
            logger.debug("No migration needed")
    except Exception as e:
        logger.error(f"Error in auto-migration setup: {e}")
