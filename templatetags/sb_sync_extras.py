from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """Look up a value in a dictionary by key"""
    if dictionary is None:
        return False
    return dictionary.get(key, False)

@register.filter
def slugify(value):
    """Convert a string to a slug format"""
    if value is None:
        return ""
    return value.replace('.', '_').replace(' ', '_').lower() 