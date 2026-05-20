# Deployment: Bot Dev

## Target

- App path: `/opt/rob-bot/app`
- Service: `rob-bot-dev.service`

## Setup

1. Create a runtime user such as `rob`.
2. Clone the repo into `/opt/rob-bot/app`.
3. Copy `.env.example` to `/opt/rob-bot/app/.env` and fill the bot values.
4. Create `.venv` and install `requirements.txt`.
5. Copy `deploy/systemd/rob-bot-dev.service` to `/etc/systemd/system/rob-bot-dev.service`.
6. Copy or symlink `deploy/scripts/deploy-bot-dev.sh` to `/opt/rob-bot/deploy-bot-dev.sh`.
7. Enable the service with `sudo systemctl enable --now rob-bot-dev.service`.
8. Verify startup with `PYTHONPATH=. python -m apps.bot.main`.

## GitHub Actions

Add these secrets:

- `BOT_DEV_HOST`
- `BOT_DEV_USER`
- `BOT_DEV_SSH_KEY`
- `BOT_DEV_PORT`

Then run the manual workflow `Deploy Bot Dev`.
