# Deployment: Webhook Dev

## Target

- App path: `/opt/rob-webhook/app`
- Service: `rob-webhook-dev.service`
- Public URL: `https://rob-dev.barecoding.com`
- Local bind: `127.0.0.1:8080`

## Setup

1. Create a runtime user such as `rob`.
2. Clone the repo into `/opt/rob-webhook/app`.
3. Copy `.env.example` to `/opt/rob-webhook/app/.env` and fill the webhook values.
4. Create `.venv` and install `requirements.txt`.
5. Copy `deploy/systemd/rob-webhook-dev.service` to `/etc/systemd/system/rob-webhook-dev.service`.
6. Copy or symlink `deploy/scripts/deploy-webhook-dev.sh` to `/opt/rob-webhook/deploy-webhook-dev.sh`.
7. Enable the service with `sudo systemctl enable --now rob-webhook-dev.service`.
8. Verify `curl http://127.0.0.1:8080/health` returns `OK`.

## GitHub Actions

Add these secrets:

- `WEBHOOK_DEV_HOST`
- `WEBHOOK_DEV_USER`
- `WEBHOOK_DEV_SSH_KEY`
- `WEBHOOK_DEV_PORT`

Then run the manual workflow `Deploy Webhook Dev`.
