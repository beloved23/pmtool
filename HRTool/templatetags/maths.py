from django import template
register = template.Library()


@register.filter
def div(value, arg):
    """
    Divides the value; argument is the divisor.
    Returns empty string on any error.
    """
    try:
        value = float(value)
        arg = float(arg)
        if arg:
            return value / arg
    except:
        pass
    return ''


@register.filter
def sub(value, arg):
    """
    Divides the value; argument is the divisor.
    Returns empty string on any error.
    """
    try:
        value = float(value)
        arg = float(arg)
        if arg:
            return value - arg
    except:
        pass
    return ''


@register.filter
def mul(value, arg):
    """
    Divides the value; argument is the divisor.
    Returns empty string on any error.
    """
    try:
        value = float(value)
        arg = float(arg)
        if arg:
            return value * arg
    except:
        pass
    return ''

