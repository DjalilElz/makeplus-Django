from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """
    Custom template filter to look up a value in a dictionary.
    Usage: {{ dict|lookup:key }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''
