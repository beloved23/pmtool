import re

from django import template
from django.urls import reverse, NoReverseMatch
from django.utils.translation import get_language
from django.conf import settings

register = template.Library()


@register.simple_tag(takes_context=True)
def active(context, pattern_or_urlname):
    path = context['request'].path
    try:
        pattern = '^' + reverse(pattern_or_urlname)
        if re.search(pattern, path):
            return 'active'
        # print pattern
    except NoReverseMatch:
        pass
    pattern = pattern_or_urlname

    if getattr(settings, 'USE_I18N', False):
        # print pattern
        if pattern[0] == '^':
            pattern = '^/' + get_language() + pattern.replace("^", '')
        # print pattern

    if re.search(pattern, path):
        return 'active'
    return ''


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
