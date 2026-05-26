from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_portal_deploy_script_runs_django_migrations():
    script = (REPO_ROOT / "deploy" / "scripts" / "deploy-portal-dev.sh").read_text(encoding="utf-8")
    assert "manage.py migrate --noinput" in script


def test_portal_deploy_script_collects_static_assets():
    script = (REPO_ROOT / "deploy" / "scripts" / "deploy-portal-dev.sh").read_text(encoding="utf-8")
    assert "manage.py collectstatic --noinput" in script


def test_portal_deploy_script_runs_django_check():
    script = (REPO_ROOT / "deploy" / "scripts" / "deploy-portal-dev.sh").read_text(encoding="utf-8")
    assert "manage.py check" in script
