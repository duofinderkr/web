from django.middleware.csrf import get_token
from django.template.backends.jinja2 import jinja2
from jinja2 import Environment
from django.urls import reverse
from project import settings
import datetime


def _n_days_ago(target_date: datetime.datetime):
    timezone = datetime.timezone(datetime.timedelta(hours=9))
    today = datetime.datetime.now().astimezone(timezone)

    diff = today - target_date.astimezone(timezone)

    if diff.days == 0 and diff.seconds < 3600:
        return f"{diff.seconds // 60}분 전"

    if diff.days == 0:
        return f"{diff.seconds // 3600}시간 전"

    if diff.days < 7:
        return f"{diff.days}일 전"

    return f"{diff.days}일 전"


def environment(**options):
    env = Environment(**options)
    env.globals.update(
        {
            "static": settings.STATIC_URL,
            "csrf_input": csrf_input,
            "url": reverse,
            "n_days_ago": _n_days_ago,
        }
    )
    return env


def csrf_input(request):
    return jinja2.Markup(
        f'<input type="hidden" name="csrfmiddlewaretoken" value="{get_token(request)}">'
    )
