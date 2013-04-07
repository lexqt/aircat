# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import template
from django.utils.http import urlencode
from django.utils.safestring import mark_safe

from locations.models import Airport, City, Country


register = template.Library()


@register.filter(is_safe=True)
def alpha_range(lang):
    if lang == 'ru':
        # skip ЁЪЫЬ
        return 'АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЭЮЯ'
    elif lang == 'en':
        return 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return ''


@register.simple_tag
def gmaps_url(location):
    lat, lon = location.latitude, location.longitude
    params = {
        'll': '{0},{1}'.format(lat, lon)
    }
    if isinstance(location, Airport):
        z = 15
    elif isinstance(location, City):
        z = 9
    else:
        z = 5
    params['z'] = z
    return mark_safe('http://maps.google.ru/?' + urlencode(params))
