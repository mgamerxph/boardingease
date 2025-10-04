from django import template

register = template.Library()

@register.filter
def split(value, delimiter=","):
    """
    Splits a string by the given delimiter and returns a list.
    Example: "Curfew, Deposit" -> ["Curfew", "Deposit"]
    """
    if value:
        return [item.strip() for item in value.split(delimiter)]
    return []

@register.filter
def trim(value):
    """Remove leading and trailing spaces"""
    if isinstance(value, str):
        return value.strip()
    return value


register = template.Library()

@register.filter
def subtract(value, arg):
    """Subtracts arg from value"""
    return value - arg

@register.filter
def split(value, arg=","):
    """
    Splits the string by the given argument (default: comma).
    Usage: {{ value|split:"," }}
    """
    if value:
        return value.split(arg)
    return []