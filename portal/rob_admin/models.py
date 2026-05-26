from __future__ import annotations

from django.db import models


class GuildSettings(models.Model):
    guild_id = models.BigIntegerField(primary_key=True)
    registration_channel_id = models.BigIntegerField(null=True, blank=True)
    leaderboard_channel_id = models.BigIntegerField(null=True, blank=True)
    send_track_channel_id = models.BigIntegerField(null=True, blank=True)
    counting_channel_id = models.BigIntegerField(null=True, blank=True)
    report_channel_id = models.BigIntegerField(null=True, blank=True)
    domme_role_id = models.BigIntegerField(null=True, blank=True)
    sub_role_id = models.BigIntegerField(null=True, blank=True)
    mod_role_id = models.BigIntegerField(null=True, blank=True)
    inactive_role_id = models.BigIntegerField(null=True, blank=True)
    warn_log_channel_id = models.BigIntegerField(null=True, blank=True)
    carlbot_user_id = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "guild_settings"
        verbose_name = "Guild Settings"
        verbose_name_plural = "Guild Settings"


class Domme(models.Model):
    id = models.BigAutoField(primary_key=True)
    guild_id = models.BigIntegerField()
    discord_user_id = models.BigIntegerField()
    throne_url = models.TextField()
    public_display_name = models.TextField(null=True, blank=True)
    public_display_name_updated_at = models.DateTimeField(null=True, blank=True)
    registered_at = models.DateTimeField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "dommes"
        verbose_name = "Dom/me"
        verbose_name_plural = "Dom/mes"


class Sub(models.Model):
    id = models.BigAutoField(primary_key=True)
    guild_id = models.BigIntegerField()
    discord_user_id = models.BigIntegerField()
    send_name = models.TextField()
    registered_at = models.DateTimeField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "subs"


class Send(models.Model):
    id = models.BigAutoField(primary_key=True)
    guild_id = models.BigIntegerField()
    domme_id = models.BigIntegerField(null=True, blank=True)
    domme_user_id = models.BigIntegerField()
    sub_id = models.BigIntegerField(null=True, blank=True)
    sub_user_id = models.BigIntegerField(null=True, blank=True)
    sub_name = models.TextField(null=True, blank=True)
    amount_cents = models.IntegerField()
    currency = models.TextField()
    method = models.TextField(null=True, blank=True)
    source = models.TextField()
    item_name = models.TextField(null=True, blank=True)
    item_image_url = models.TextField(null=True, blank=True)
    external_id = models.TextField(null=True, blank=True)
    event_id = models.TextField(null=True, blank=True)
    fallback_event_hash = models.TextField(null=True, blank=True)
    is_private = models.BooleanField(default=False)
    seeded = models.BooleanField(default=False)
    sent_at = models.DateTimeField()
    received_at = models.DateTimeField()
    discord_post_status = models.TextField()
    discord_posted_at = models.DateTimeField(null=True, blank=True)
    discord_message_id = models.BigIntegerField(null=True, blank=True)
    discord_post_error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField()
    is_test_send = models.BooleanField(default=False)
    public_send_id = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "sends"


class SendRequest(models.Model):
    id = models.BigAutoField(primary_key=True)
    guild_id = models.BigIntegerField()
    sub_user_id = models.BigIntegerField()
    domme_user_id = models.BigIntegerField()
    amount_cents = models.IntegerField()
    currency = models.TextField()
    method = models.TextField()
    note = models.TextField(null=True, blank=True)
    status = models.TextField()
    created_at = models.DateTimeField()
    resolved_at = models.DateTimeField(null=True, blank=True)
    denial_reason = models.TextField(null=True, blank=True)
    resolved_by_user_id = models.BigIntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "send_requests"


class ThroneCreator(models.Model):
    id = models.BigAutoField(primary_key=True)
    guild_id = models.BigIntegerField()
    domme_id = models.BigIntegerField(null=True, blank=True)
    discord_user_id = models.BigIntegerField()
    throne_handle = models.TextField()
    throne_creator_id = models.TextField()
    hide_own_purchases = models.BooleanField(null=True, blank=True)
    tracking_mode = models.TextField()
    webhook_secret = models.TextField(null=True, blank=True)
    webhook_secret_hash = models.TextField(null=True, blank=True)
    webhook_connected_at = models.DateTimeField(null=True, blank=True)
    overlay_detected = models.BooleanField(default=False)
    last_overlay_check_at = models.DateTimeField(null=True, blank=True)
    last_successful_event_at = models.DateTimeField(null=True, blank=True)
    last_test_webhook_at = models.DateTimeField(null=True, blank=True)
    setup_verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "throne_creators"


class PublicLeaderboard(models.Model):
    id = models.BigAutoField(primary_key=True)
    guild_id = models.BigIntegerField()
    public_token = models.TextField()
    title = models.TextField()
    enabled = models.BooleanField(default=True)
    theme = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "public_leaderboards"

    @property
    def public_url(self) -> str:
        from django.conf import settings

        base = (settings.ROB_PORTAL_BASE_URL or "").rstrip("/")
        return f"{base}/public/leaderboard/{self.public_token}"


class LeaderboardMessage(models.Model):
    id = models.BigAutoField(primary_key=True)
    guild_id = models.BigIntegerField()
    message_key = models.TextField()
    leaderboard_type = models.TextField(null=True, blank=True)
    channel_id = models.BigIntegerField()
    message_id = models.BigIntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "leaderboard_message"


class BotState(models.Model):
    key = models.TextField(primary_key=True)
    value = models.TextField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "bot_state"
        verbose_name = "Bot State"
        verbose_name_plural = "Bot State"


class CountingState(models.Model):
    guild_id = models.BigIntegerField(primary_key=True)
    channel_id = models.BigIntegerField(null=True, blank=True)
    current_number = models.BigIntegerField()
    last_user_id = models.BigIntegerField(null=True, blank=True)
    is_enabled = models.BooleanField(default=False)
    pending_restore = models.BooleanField(default=False)
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "counting_state"


class Blacklist(models.Model):
    discord_user_id = models.BigIntegerField(primary_key=True)
    reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField()
    created_by = models.BigIntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "blacklist"


class SchemaMigration(models.Model):
    version = models.TextField(primary_key=True)
    applied_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "schema_migrations"
        verbose_name = "Schema Migration"
        verbose_name_plural = "Schema Migrations"


class LegacyLeaderboardMessage(models.Model):
    id = models.BigAutoField(primary_key=True)
    guild_id = models.BigIntegerField()
    message_key = models.TextField()
    leaderboard_type = models.TextField(null=True, blank=True)
    channel_id = models.BigIntegerField()
    message_id = models.BigIntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "leaderboard_messages"
        verbose_name = "Legacy Leaderboard Message"
        verbose_name_plural = "Legacy Leaderboard Messages"


class LegacyThroneWishlistItem(models.Model):
    id = models.BigAutoField(primary_key=True)
    creator_id = models.TextField()
    wishlist_item_id = models.TextField()
    item_name = models.TextField(null=True, blank=True)
    item_image_url = models.TextField(null=True, blank=True)
    amount_cents = models.IntegerField()
    currency = models.TextField(null=True, blank=True)
    is_available = models.BooleanField(null=True, blank=True)
    last_seen_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "throne_wishlist_items"
        verbose_name = "Legacy Throne Wishlist Item"
        verbose_name_plural = "Legacy Throne Wishlist Items"


class PortalAuditLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    actor_discord_user_id = models.BigIntegerField()
    actor_username = models.TextField(null=True, blank=True)
    action = models.TextField()
    target_type = models.TextField(null=True, blank=True)
    target_id = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "portal_audit_log"
        verbose_name = "Portal Audit Log"
        verbose_name_plural = "Portal Audit Log"
