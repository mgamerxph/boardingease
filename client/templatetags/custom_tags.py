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
