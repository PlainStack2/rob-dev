from __future__ import annotations

from django.apps import AppConfig


class RobAdminConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "rob_admin"
    verbose_name = "Rob Admin Portal"

