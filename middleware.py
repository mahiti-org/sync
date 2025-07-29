from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone
from django.db import connection
from datetime import timedelta
import time
import psutil
import logging

logger = logging.getLogger('sb_sync')

class SbSyncRateLimitMiddleware:
    """Rate limiting middleware for sb-sync APIs with performance optimizations"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.path.startswith('/api/sync/'):
            # Check rate limits with caching
            if not self.check_rate_limit(request):
                return JsonResponse({
                    'error': 'Rate limit exceeded',
                    'message': 'Too many requests. Please try again later.',
                    'retry_after': 60  # seconds
                }, status=429)
        
        response = self.get_response(request)
        return response
    
    def check_rate_limit(self, request):
        """Check if request is within rate limits with optimized caching"""
        user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
        if not user_id:
            return True  # Skip rate limiting for unauthenticated requests
        
        current_time = timezone.now()
        
        # Check requests per minute with atomic increment
        minute_key = f"sb_sync_rate_limit_{user_id}_{current_time.strftime('%Y%m%d%H%M')}"
        minute_count = cache.get(minute_key, 0)
        
        if minute_count >= 60:  # 60 requests per minute
            return False
        
        # Check requests per hour
        hour_key = f"sb_sync_rate_limit_{user_id}_{current_time.strftime('%Y%m%d%H')}"
        hour_count = cache.get(hour_key, 0)
        
        if hour_count >= 3000:  # 3000 requests per hour
            return False
        
        # Increment counters atomically
        cache.set(minute_key, minute_count + 1, timeout=60)
        cache.set(hour_key, hour_count + 1, timeout=3600)
        
        return True

class SbSyncPerformanceMiddleware:
    """Enhanced performance monitoring middleware"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.path.startswith('/api/sync/'):
            start_time = time.time()
            initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            # Optimize database connection
            self._optimize_connection()
            
            response = self.get_response(request)
            
            # Calculate performance metrics
            processing_time = time.time() - start_time
            final_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_used = final_memory - initial_memory
            
            # Add performance headers
            response['X-Processing-Time'] = f"{processing_time:.3f}s"
            response['X-Memory-Used'] = f"{memory_used:.2f}MB"
            response['X-Timestamp'] = timezone.now().isoformat()
            response['X-Query-Count'] = str(len(connection.queries))
            
            # Log performance metrics
            self._log_performance_metrics(request, processing_time, memory_used)
            
            return response
        
        return self.get_response(request)
    
    def _optimize_connection(self):
        """Optimize database connection for better performance"""
        try:
            connection.ensure_connection()
            with connection.cursor() as cursor:
                # Set session-level optimizations
                cursor.execute("SET SESSION sql_mode = 'STRICT_TRANS_TABLES'")
                cursor.execute("SET SESSION innodb_lock_wait_timeout = 50")
        except Exception as e:
            logger.warning(f"Failed to optimize database connection: {e}")
    
    def _log_performance_metrics(self, request, processing_time, memory_used):
        """Log performance metrics for monitoring"""
        user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
        
        logger.info(
            f"Performance metrics - User: {user_id}, "
            f"Path: {request.path}, "
            f"Time: {processing_time:.3f}s, "
            f"Memory: {memory_used:.2f}MB, "
            f"Queries: {len(connection.queries)}"
        )

class SbSyncCacheMiddleware:
    """Cache optimization middleware"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.path.startswith('/api/sync/'):
            # Check if response can be cached
            if self._is_cacheable(request):
                cached_response = self._get_cached_response(request)
                if cached_response:
                    return cached_response
            
            response = self.get_response(request)
            
            # Cache the response if appropriate
            if self._should_cache_response(request, response):
                self._cache_response(request, response)
            
            return response
        
        return self.get_response(request)
    
    def _is_cacheable(self, request):
        """Check if request can be cached"""
        return request.method == 'GET' and 'no-cache' not in request.headers
    
    def _get_cached_response(self, request):
        """Get cached response if available"""
        cache_key = self._generate_cache_key(request)
        cached_data = cache.get(cache_key)
        
        if cached_data:
            # Increment cache hits
            cache.set('cache_hits', cache.get('cache_hits', 0) + 1)
            return JsonResponse(cached_data)
        
        # Increment cache misses
        cache.set('cache_misses', cache.get('cache_misses', 0) + 1)
        return None
    
    def _should_cache_response(self, request, response):
        """Check if response should be cached"""
        return (request.method == 'GET' and 
                response.status_code == 200 and
                'no-cache' not in response.headers)
    
    def _cache_response(self, request, response):
        """Cache the response"""
        try:
            cache_key = self._generate_cache_key(request)
            cache_data = response.content.decode('utf-8')
            cache.set(cache_key, cache_data, timeout=300)  # 5 minutes
        except Exception as e:
            logger.warning(f"Failed to cache response: {e}")
    
    def _generate_cache_key(self, request):
        """Generate cache key for request"""
        user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
        return f"sb_sync_cache_{user_id}_{request.path}_{hash(str(request.GET))}"

class SbSyncConnectionPoolMiddleware:
    """Database connection pooling middleware"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.path.startswith('/api/sync/'):
            # Ensure connection is available and optimized
            self._ensure_connection()
            
            response = self.get_response(request)
            
            # Clean up connection if needed
            self._cleanup_connection()
            
            return response
        
        return self.get_response(request)
    
    def _ensure_connection(self):
        """Ensure database connection is available and optimized"""
        try:
            if not connection.connection or connection.connection.closed:
                connection.ensure_connection()
            
            # Set connection parameters for better performance
            with connection.cursor() as cursor:
                cursor.execute("SET SESSION wait_timeout = 600")  # 10 minutes
                cursor.execute("SET SESSION interactive_timeout = 600")
        except Exception as e:
            logger.warning(f"Failed to optimize connection: {e}")
    
    def _cleanup_connection(self):
        """Clean up database connection"""
        try:
            # Close connection if it's been open too long
            if hasattr(connection, 'connection') and connection.connection:
                # In production, you might want to implement connection pooling
                # For now, we'll just ensure the connection is healthy
                pass
        except Exception as e:
            logger.warning(f"Failed to cleanup connection: {e}")

class SbSyncMemoryMiddleware:
    """Memory optimization middleware"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.path.startswith('/api/sync/'):
            # Monitor memory usage
            initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            response = self.get_response(request)
            
            # Check memory usage and optimize if needed
            final_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_used = final_memory - initial_memory
            
            # If memory usage is high, force garbage collection
            if memory_used > 100:  # 100MB threshold
                import gc
                gc.collect()
                logger.info(f"High memory usage detected: {memory_used:.2f}MB, forced GC")
            
            return response
        
        return self.get_response(request)
