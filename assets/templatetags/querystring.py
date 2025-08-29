from urllib.parse import urlencode

from django import template

register = template.Library()


@register.simple_tag
def querystring(get_params, **kwargs):
    """
    Replaces or adds specific query parameters to the current GET params.
    Example usage:
        {% querystring request.GET 'page'=2 %}
    """
    updated = get_params.copy()

    for key, value in kwargs.items():
        if value is None:
            updated.pop(key, None)
        else:
            updated[key] = value

    return updated.urlencode()
