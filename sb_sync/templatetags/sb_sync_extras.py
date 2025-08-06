from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """Look up a value in a dictionary by key"""
    if dictionary is None:
        return False
    
    # Handle boolean values (they don't have .get method)
    if isinstance(dictionary, bool):
        return dictionary
    
    # Handle dictionary-like objects
    if hasattr(dictionary, 'get'):
        return dictionary.get(key, False)
    
    # Handle list/tuple with integer keys
    if isinstance(dictionary, (list, tuple)) and isinstance(key, int):
        try:
            return dictionary[key]
        except (IndexError, TypeError):
            return False
    
    # Handle object attributes
    if hasattr(dictionary, key):
        return getattr(dictionary, key)
    
    return False

@register.filter
def slugify(value):
    """Convert a string to a slug format"""
    if value is None:
        return ""
    return value.replace('.', '_').replace(' ', '_').lower() 