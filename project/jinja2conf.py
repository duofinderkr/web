from django.middleware.csrf import get_token
from django.template.backends.jinja2 import jinja2
from jinja2 import Environment
from django.urls import reverse
from project import settings


def environment(**options):
    env = Environment(**options)
    env.globals.update(
        {
            "static": settings.STATIC_URL,
            "csrf_input": csrf_input,
            "url": reverse,
        }
    )
    return env


def csrf_input(request):
    return jinja2.Markup(
        f'<input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">'
    )
