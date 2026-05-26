from __future__ import annotations

from django.conf import settings
from django.http import HttpResponseNotFound


class PortalEnabledMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/portal/") and not getattr(settings, "ROB_PORTAL_ENABLED", False):
            return HttpResponseNotFound("Rob portal is disabled.")
        return self.get_response(request)

