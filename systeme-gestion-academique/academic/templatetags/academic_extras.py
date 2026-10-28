from django import template
register = template.Library()

@register.filter
def lookup(obj, attribute):
    value = obj
    for part in str(attribute).split("."):
        value = getattr(value, part, "")
        if callable(value):
            try:
                value = value()
            except TypeError:
                return ""
    return value
