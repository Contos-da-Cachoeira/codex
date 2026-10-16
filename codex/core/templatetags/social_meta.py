"""Informações públicas de compartilhamento, entregues no HTML inicial."""
from django import template
from core.social import public_metadata

register = template.Library()


@register.inclusion_tag('core/includes/social_meta.html', takes_context=True)
def social_meta(context):
    return public_metadata(context)
