"""
Security features for sb-sync package
"""
import re
import html
import json
from typing import Dict, Any, List, Optional
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from django.utils.crypto import get_random_string
import bleach


class SecurityManager:
    """Security manager for input validation and sanitization"""
    
    # HTML tags and attributes that are allowed
    ALLOWED_TAGS = [
        'b', 'i', 'u', 'em', 'strong', 'a', 'p', 'br', 'div', 'span'
    ]
    
    ALLOWED_ATTRIBUTES = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title'],
    }
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r'(\b(union|select|insert|update|delete|drop|create|alter)\b)',
        r'(\b(or|and)\b\s+\d+\s*=\s*\d+)',
        r'(\b(union|select|insert|update|delete|drop|create|alter)\b\s+.*\b(union|select|insert|update|delete|drop|create|alter)\b)',
        r'(\b(union|select|insert|update|delete|drop|create|alter)\b\s+.*\b(union|select|insert|update|delete|drop|create|alter)\b\s+.*\b(union|select|insert|update|delete|drop|create|alter)\b)',
        r'(\b(union|select|insert|update|delete|drop|create|alter)\b\s+.*\b(union|select|insert|update|delete|drop|create|alter)\b\s+.*\b(union|select|insert|update|delete|drop|create|alter)\b\s+.*\b(union|select|insert|update|delete|drop|create|alter)\b)',
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
        r'<applet[^>]*>.*?</applet>',
        r'<form[^>]*>.*?</form>',
        r'<input[^>]*>',
        r'<textarea[^>]*>.*?</textarea>',
        r'<select[^>]*>.*?</select>',
        r'<button[^>]*>.*?</button>',
        r'<link[^>]*>',
        r'<meta[^>]*>',
        r'<style[^>]*>.*?</style>',
        r'<link[^>]*>',
        r'<base[^>]*>',
        r'<title[^>]*>.*?</title>',
        r'<head[^>]*>.*?</head>',
        r'<body[^>]*>.*?</body>',
        r'<html[^>]*>.*?</html>',
        r'<xml[^>]*>.*?</xml>',
        r'<xmp[^>]*>.*?</xmp>',
        r'<plaintext[^>]*>.*?</plaintext>',
        r'<listing[^>]*>.*?</listing>',
        r'<marquee[^>]*>.*?</marquee>',
        r'<blink[^>]*>.*?</blink>',
        r'<isindex[^>]*>',
        r'<keygen[^>]*>',
        r'<command[^>]*>',
        r'<menu[^>]*>.*?</menu>',
        r'<menuitem[^>]*>',
        r'<meter[^>]*>.*?</meter>',
        r'<progress[^>]*>.*?</progress>',
        r'<output[^>]*>.*?</output>',
        r'<canvas[^>]*>.*?</canvas>',
        r'<svg[^>]*>.*?</svg>',
        r'<math[^>]*>.*?</math>',
        r'<video[^>]*>.*?</video>',
        r'<audio[^>]*>.*?</audio>',
        r'<source[^>]*>',
        r'<track[^>]*>',
        r'<area[^>]*>',
        r'<map[^>]*>.*?</map>',
        r'<figure[^>]*>.*?</figure>',
        r'<figcaption[^>]*>.*?</figcaption>',
        r'<article[^>]*>.*?</article>',
        r'<aside[^>]*>.*?</aside>',
        r'<details[^>]*>.*?</details>',
        r'<summary[^>]*>.*?</summary>',
        r'<dialog[^>]*>.*?</dialog>',
        r'<data[^>]*>.*?</data>',
        r'<time[^>]*>.*?</time>',
        r'<mark[^>]*>.*?</mark>',
        r'<ruby[^>]*>.*?</ruby>',
        r'<rt[^>]*>.*?</rt>',
        r'<rp[^>]*>.*?</rp>',
        r'<bdi[^>]*>.*?</bdi>',
        r'<bdo[^>]*>.*?</bdo>',
        r'<wbr[^>]*>',
        r'<picture[^>]*>.*?</picture>',
        r'<template[^>]*>.*?</template>',
        r'<slot[^>]*>.*?</slot>',
        r'<shadow[^>]*>.*?</shadow>',
        r'<content[^>]*>.*?</content>',
        r'<element[^>]*>.*?</element>',
        r'<shim[^>]*>.*?</shim>',
        r'<import[^>]*>.*?</import>',
        r'<decorator[^>]*>.*?</decorator>',
        r'<pseudocode[^>]*>.*?</pseudocode>',
        r'<xmp[^>]*>.*?</xmp>',
        r'<plaintext[^>]*>.*?</plaintext>',
        r'<listing[^>]*>.*?</listing>',
        r'<marquee[^>]*>.*?</marquee>',
        r'<blink[^>]*>.*?</blink>',
        r'<isindex[^>]*>',
        r'<keygen[^>]*>',
        r'<command[^>]*>',
        r'<menu[^>]*>.*?</menu>',
        r'<menuitem[^>]*>',
        r'<meter[^>]*>.*?</meter>',
        r'<progress[^>]*>.*?</progress>',
        r'<output[^>]*>.*?</output>',
        r'<canvas[^>]*>.*?</canvas>',
        r'<svg[^>]*>.*?</svg>',
        r'<math[^>]*>.*?</math>',
        r'<video[^>]*>.*?</video>',
        r'<audio[^>]*>.*?</audio>',
        r'<source[^>]*>',
        r'<track[^>]*>',
        r'<area[^>]*>',
        r'<map[^>]*>.*?</map>',
        r'<figure[^>]*>.*?</figure>',
        r'<figcaption[^>]*>.*?</figcaption>',
        r'<article[^>]*>.*?</article>',
        r'<aside[^>]*>.*?</aside>',
        r'<details[^>]*>.*?</details>',
        r'<summary[^>]*>.*?</summary>',
        r'<dialog[^>]*>.*?</dialog>',
        r'<data[^>]*>.*?</data>',
        r'<time[^>]*>.*?</time>',
        r'<mark[^>]*>.*?</mark>',
        r'<ruby[^>]*>.*?</ruby>',
        r'<rt[^>]*>.*?</rt>',
        r'<rp[^>]*>.*?</rp>',
        r'<bdi[^>]*>.*?</bdi>',
        r'<bdo[^>]*>.*?</bdo>',
        r'<wbr[^>]*>',
        r'<picture[^>]*>.*?</picture>',
        r'<template[^>]*>.*?</template>',
        r'<slot[^>]*>.*?</slot>',
        r'<shadow[^>]*>.*?</shadow>',
        r'<content[^>]*>.*?</content>',
        r'<element[^>]*>.*?</element>',
        r'<shim[^>]*>.*?</shim>',
        r'<import[^>]*>.*?</import>',
        r'<decorator[^>]*>.*?</decorator>',
        r'<pseudocode[^>]*>.*?</pseudocode>',
    ]
    
    @classmethod
    def sanitize_input(cls, data: Any, field_type: str = 'text') -> Any:
        """Sanitize input data based on field type"""
        if data is None:
            return data
        
        if isinstance(data, str):
            return cls._sanitize_string(data, field_type)
        elif isinstance(data, dict):
            return cls._sanitize_dict(data)
        elif isinstance(data, list):
            return cls._sanitize_list(data)
        else:
            return data
    
    @classmethod
    def _sanitize_string(cls, value: str, field_type: str) -> str:
        """Sanitize string input"""
        if not value:
            return value
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Check for SQL injection
        if cls._detect_sql_injection(value):
            raise ValidationError("Potential SQL injection detected")
        
        # Check for XSS
        if cls._detect_xss(value):
            raise ValidationError("Potential XSS attack detected")
        
        # Sanitize based on field type
        if field_type == 'html':
            # Allow safe HTML
            return bleach.clean(
                value,
                tags=cls.ALLOWED_TAGS,
                attributes=cls.ALLOWED_ATTRIBUTES,
                strip=True
            )
        elif field_type == 'text':
            # Strip HTML tags
            return strip_tags(value)
        elif field_type == 'email':
            # Basic email validation
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
                raise ValidationError("Invalid email format")
            return value.lower()
        elif field_type == 'url':
            # Basic URL validation
            if not re.match(r'^https?://[^\s/$.?#].[^\s]*$', value):
                raise ValidationError("Invalid URL format")
            return value
        elif field_type == 'phone':
            # Basic phone validation
            value = re.sub(r'[^\d+\-\(\)\s]', '', value)
            return value
        elif field_type == 'date':
            # Basic date validation
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', value):
                raise ValidationError("Invalid date format (YYYY-MM-DD)")
            return value
        elif field_type == 'datetime':
            # Basic datetime validation
            if not re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', value):
                raise ValidationError("Invalid datetime format")
            return value
        else:
            # Default: strip HTML and escape
            return html.escape(strip_tags(value))
    
    @classmethod
    def _sanitize_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize dictionary input"""
        sanitized = {}
        for key, value in data.items():
            if isinstance(key, str):
                key = cls._sanitize_string(key, 'text')
            sanitized[key] = cls.sanitize_input(value)
        return sanitized
    
    @classmethod
    def _sanitize_list(cls, data: List[Any]) -> List[Any]:
        """Sanitize list input"""
        return [cls.sanitize_input(item) for item in data]
    
    @classmethod
    def _detect_sql_injection(cls, value: str) -> bool:
        """Detect potential SQL injection"""
        value_lower = value.lower()
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def _detect_xss(cls, value: str) -> bool:
        """Detect potential XSS attacks"""
        value_lower = value.lower()
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        return False


class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self, cache_backend=None):
        self.cache = cache_backend or settings.CACHES['default']['BACKEND']
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed within rate limit"""
        current_count = self.cache.get(key, 0)
        if current_count >= limit:
            return False
        
        self.cache.set(key, current_count + 1, timeout=window)
        return True
    
    def get_remaining(self, key: str, limit: int) -> int:
        """Get remaining requests allowed"""
        current_count = self.cache.get(key, 0)
        return max(0, limit - current_count)


class CSRFProtection:
    """CSRF protection for API endpoints"""
    
    @staticmethod
    def validate_token(request, token: str) -> bool:
        """Validate CSRF token"""
        if not token:
            return False
        
        # Check if token matches session token
        session_token = request.session.get('csrf_token')
        if not session_token:
            return False
        
        return token == session_token
    
    @staticmethod
    def generate_token(request) -> str:
        """Generate CSRF token"""
        token = get_random_string(32)
        request.session['csrf_token'] = token
        return token


class PermissionManager:
    """Permission management for sync operations"""
    
    def __init__(self):
        self.permissions = {
            'push': ['sync.push'],
            'pull': ['sync.pull'],
            'admin': ['sync.admin'],
            'read': ['sync.read'],
            'write': ['sync.write'],
        }
    
    def has_permission(self, user, operation: str) -> bool:
        """Check if user has permission for operation"""
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
        
        required_permissions = self.permissions.get(operation, [])
        if not required_permissions:
            return True
        
        return user.has_perms(required_permissions)
    
    def get_user_permissions(self, user) -> List[str]:
        """Get all permissions for user"""
        if not user.is_authenticated:
            return []
        
        if user.is_superuser:
            return list(self.permissions.keys())
        
        permissions = []
        for operation, perms in self.permissions.items():
            if user.has_perms(perms):
                permissions.append(operation)
        
        return permissions


class AuditLogger:
    """Audit logging for security events"""
    
    def __init__(self, logger_name: str = 'sb_sync.security'):
        self.logger = logging.getLogger(logger_name)
    
    def log_security_event(self, event_type: str, user, details: Dict[str, Any]):
        """Log security event"""
        log_data = {
            'event_type': event_type,
            'user_id': getattr(user, 'id', None),
            'username': getattr(user, 'username', 'anonymous'),
            'timestamp': timezone.now().isoformat(),
            'details': details,
        }
        
        self.logger.warning(f"Security event: {json.dumps(log_data)}")
    
    def log_failed_login(self, username: str, ip_address: str):
        """Log failed login attempt"""
        self.log_security_event('failed_login', None, {
            'username': username,
            'ip_address': ip_address,
        })
    
    def log_successful_login(self, user, ip_address: str):
        """Log successful login"""
        self.log_security_event('successful_login', user, {
            'ip_address': ip_address,
        })
    
    def log_suspicious_activity(self, user, activity_type: str, details: Dict[str, Any]):
        """Log suspicious activity"""
        self.log_security_event('suspicious_activity', user, {
            'activity_type': activity_type,
            'details': details,
        }) 