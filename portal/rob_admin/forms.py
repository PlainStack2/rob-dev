from __future__ import annotations

from django import forms


class ServiceLogForm(forms.Form):
    service = forms.ChoiceField(choices=())
    lines = forms.IntegerField(min_value=1, max_value=500, initial=200)

    def __init__(self, *args, allowed_services: tuple[str, ...], **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].choices = [(name, name) for name in allowed_services]
        if allowed_services and not self.is_bound:
            self.initial.setdefault("service", allowed_services[0])


class GuildActionForm(forms.Form):
    guild_id = forms.IntegerField(min_value=1)


class PublicLeaderboardCreateForm(forms.Form):
    guild_id = forms.IntegerField(min_value=1)
    title = forms.CharField(max_length=160)
    theme = forms.CharField(max_length=40, initial="goth_red")


class PublicLeaderboardUpdateForm(forms.Form):
    row_id = forms.IntegerField(min_value=1)
    action = forms.ChoiceField(
        choices=(
            ("enable", "Enable"),
            ("disable", "Disable"),
            ("rotate", "Rotate token"),
        )
    )


class MaintenanceToggleForm(forms.Form):
    enabled = forms.BooleanField(required=False)
    reason = forms.CharField(max_length=200, required=False)

