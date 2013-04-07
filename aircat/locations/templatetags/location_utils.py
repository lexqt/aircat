# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import template


register = template.Library()


@register.filter(is_safe=True)
def alpha_range(lang):
    if lang == 'ru':
        # skip ЁЪЫЬ
        return 'АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЭЮЯ'
    elif lang == 'en':
        return 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return ''
