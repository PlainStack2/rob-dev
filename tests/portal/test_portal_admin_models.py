from __future__ import annotations

from types import SimpleNamespace

from django.contrib import admin
from django.utils import timezone

from rob_admin import admin as portal_admin
from rob_admin.models import BotState, Domme, SchemaMigration, Send


def test_portal_models_are_unmanaged():
    assert Domme._meta.managed is False
    assert Send._meta.managed is False
    assert SchemaMigration._meta.managed is False


def test_sends_admin_is_read_only_and_no_delete():
    send_admin = portal_admin.SendAdmin(Send, admin.site)
    assert send_admin.has_add_permission(SimpleNamespace()) is False
    assert send_admin.has_delete_permission(SimpleNamespace(), None) is False
    assert send_admin.has_change_permission(SimpleNamespace(method="POST"), None) is False


def test_schema_migrations_admin_is_read_only_and_no_delete():
    schema_admin = portal_admin.SchemaMigrationAdmin(SchemaMigration, admin.site)
    assert schema_admin.has_add_permission(SimpleNamespace()) is False
    assert schema_admin.has_delete_permission(SimpleNamespace(), None) is False
    assert schema_admin.has_change_permission(SimpleNamespace(method="POST"), None) is False


def test_sensitive_bot_state_values_are_masked():
    bot_admin = portal_admin.BotStateAdmin(BotState, admin.site)
    sensitive = BotState(key="rob_ops_secret", value="abc123", updated_at=timezone.now())
    non_sensitive = BotState(key="maintenance_mode", value="true", updated_at=timezone.now())
    assert bot_admin.masked_value(sensitive) == "***"
    assert bot_admin.masked_value(non_sensitive) == "true"
