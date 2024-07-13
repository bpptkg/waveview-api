import logging
from typing import Any, Mapping, Optional

import pytz
from django.http import HttpRequest, HttpResponse
from django.template import loader
from django.utils import timezone

logger = logging.getLogger(__name__)


def render_to_string(
    template: str,
    context: Optional[Mapping[str, Any]] = None,
    request: Optional[HttpRequest] = None,
) -> str:
    if context is None:
        context = dict()
    else:
        context = dict(context)

    if "timezone" in context and context["timezone"] in pytz.all_timezones_set:
        timezone.activate(context["timezone"])

    rendered = loader.render_to_string(template, context=context, request=request)
    timezone.deactivate()

    return rendered


def render_to_response(
    template: str,
    context: Optional[Mapping[str, Any]] = None,
    request: Optional[HttpRequest] = None,
    status: int = 200,
    content_type: str = "text/html",
) -> HttpResponse:
    response = HttpResponse(render_to_string(template, context, request))
    response.status_code = status
    response["Content-Type"] = content_type
    return response
