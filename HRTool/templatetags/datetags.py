import re
from datetime import timedelta

from django import template
from django.urls import reverse, NoReverseMatch
from django.utils.translation import get_language
from django.conf import settings

register = template.Library()


@register.filter
def add_hours(dt, hours):
    return dt + timedelta(hours=int(hours))


@register.simple_tag(takes_context=True)
def selected(context, pattern_or_urlname):
    path = context['request'].path
    try:
        pattern = '^' + reverse(pattern_or_urlname)
        if re.search(pattern, path):
            return 'selected'
        # print pattern

    except NoReverseMatch:
        pattern = pattern_or_urlname

        if getattr(settings, 'USE_I18N', False):
            # print pattern
            if pattern[0] == '^':
                pattern = '^/' + get_language() + pattern.replace("^",'')
            # print pattern

        if re.search(pattern, path):
            return 'selected'
    return ''
