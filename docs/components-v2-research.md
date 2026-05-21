# Components V2 Research

## Sources checked
- Official Discord component reference: https://docs.discord.com/developers/components/reference
- Official Discord components overview: https://docs.discord.com/developers/components/overview
- discord.py interactions/api docs (LayoutView + edit rules): https://discordpy.readthedocs.io/en/stable/interactions/api.html
- discord.py API docs (message editing + LayoutView note): https://discordpy.readthedocs.io/en/stable/api.html
- notpatdev/rob-the-bot reference: https://github.com/notpatdev/rob-the-bot
- Local archive reference: `legacy/single-process-bot/`

## What the current installed discord.py supports
Environment check in this repo reports:
- `discord.py==2.7.1`
- `discord.ui.LayoutView`: available
- `discord.ui.Container`: available
- `discord.ui.Section`: available
- `discord.ui.TextDisplay`: available
- `discord.ui.Separator`: available
- `discord.ui.MediaGallery`: available
- `discord.ui.Thumbnail`: available

The discord.py docs also explicitly state that when editing a message to use `LayoutView`, if previous content/embed/embeds/attachments were present, they must be explicitly cleared (`None`/empty as appropriate).

## How Rob now renders V2 cards
- Rob now performs runtime capability checks for Bot UI Kit classes in `rob/ui/render.py`.
- If available, Rob renders cards through `discord.ui.LayoutView` + `discord.ui.Container` + `discord.ui.TextDisplay` + `discord.ui.Separator`, and attempts `discord.ui.MediaGallery` for image URLs.
- Interactive button views are preserved by promoting classic `View` children into a `LayoutView` container in V2 mode.
- Cogs that use the card renderer send/edit via `RenderedMessage.send_kwargs()` and `RenderedMessage.edit_kwargs()`.

## Fallback behaviour
- If required V2 classes are missing, Rob falls back to classic embed rendering.
- Fallback mode logs that embed rendering is active.
- In V2 edit mode, Rob explicitly sends `content=None`, `embed=None`, `embeds=None`, `attachments=None` to avoid stale embed/content artifacts.

## Manual testing checklist
- `/register domme` shows the public registration card.
- The full webhook URL appears only in DM setup flow.
- DM setup flow uses `LayoutView` on environments with V2 support.
- Continue Setup edits the same DM message.
- Editing into V2 clears old embed/content fields.
- `Yes` verifies setup for the exact creator row only.
- Throne test webhook marks setup verification without creating/posting sends.
- `/leaderboard` uses the shared card renderer.
- If V2 support is absent, embed fallback still works and logs explain fallback mode.
