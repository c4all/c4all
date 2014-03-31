from django import template
from django.conf import settings

import random

register = template.Library()


@register.filter(name='randomize_avatar')
def randomize_avatar(value):
    random.seed(value)
    avatar_num = str(random.randint(1, 28)).zfill(2)

    return "%s.png" % avatar_num


@register.filter(name='visible_comments_count')
def visible_comments_count(value):
    return value.filter(hidden=False).count()


@register.filter(name='comment_number_filter')
def comment_number_filter(value, all):
    return value if all else value.filter(hidden=False)[:settings.WIDGET_COMMENTS_DEFAULT_NUMBER]
