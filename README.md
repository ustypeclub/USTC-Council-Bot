# Votum Small‑Council Voting Bot

This repository contains a re‑implementation of Votum, a small‑council voting bot for Discord.  It provides an opinionated workflow for democratic decisions in private councils while preserving transparency through exports and archives.  In addition to the Discord bot, a web dashboard written with FastAPI exposes archives, configuration and live tallies.

## Overview

The project consists of two main components:

1. **Discord bot** – implemented with Python 3.11 and [`discord.py` v2.x](https://www.pythondiscord.com/pages/guides/python-guides/app-commands/).  All commands are exposed as **slash commands** using the app commands system.  The bot stores its state in SQLite using `aiosqlite` and supports schema migrations.  Votes, councils and motions are persisted so that archives can be exported with reasons and user IDs.
2. **Web dashboard** – built with FastAPI, Jinja2 templates and a small JavaScript front‑end.  The dashboard uses Discord OAuth 2 login (identify scope) and enforces per‑guild role checks.  Pages allow admins to manage councils, view motions, open/kill motions, edit configuration and inspect archives.  A WebSocket endpoint pushes live vote tallies to the UI.

## Features

- **Per‑guild councils:** multiple councils per guild can be created.  Channels can be marked/unmarked as councils with `/council create` and `/council remove`.  Statistics and current motion status are available through `/council stats`.
- **Private motions and threads:** use `/motion new` to propose a motion.  The bot automatically creates a private deliberation thread only visible to the proposer, councilors and admins.  Motions can be killed by their author or by admins with `/motion kill`.
- **Voting with weighted votes:** councilors vote using `/vote yes|no|abstain` or by clicking buttons.  Votes can carry custom weights set per user or role through `/setweight`.  Fractions and percentages for required majorities are parsed by the majority utility.
- **Queue and expiration:** if `motion.queue` is enabled, new motions will wait for the current one to end before starting automatically.  Motions can have an expiration time and will resolve when expired by majority of cast votes.  A dictator role may instantly resolve a motion.
- **Full archives:** every motion’s results, including individual vote reasons and user IDs, can be exported through `/archive export`.  The web dashboard provides filters by date and council and can produce JSON/CSV downloads.
- **Configurable:** a key/value configuration system allows admins to tweak behaviour, e.g. required roles, cooldowns, majority defaults, announcements, queueing, reason requirements and transcript retention.
- **Structured logging and graceful shutdown:** the bot uses a logging configuration file and handles cancellation to ensure the database is closed cleanly.

## Installation

The bot requires Python 3.11.  Clone the repository, install the dependencies, set up the database and run the bot:

```bash
git clone https://github.com/yourusername/votum-bot
cd votum-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then fill in your Discord token, client ID/secret and other secrets
python -m bot
```

By default the bot uses `bot/src/db/schema.sql` to create the SQLite schema.  Use `python bot/src/db/migrate.py` to apply migrations if you change the schema.  To run both bot and dashboard inside Docker, build and run the provided `Dockerfile`.

## Environment variables

The bot and dashboard read configuration from a `.env` file using `python-dotenv`.  Important variables include:

- `DISCORD_TOKEN` – bot token obtained from the Discord Developer Portal.
- `DISCORD_CLIENT_ID` / `DISCORD_CLIENT_SECRET` – credentials for OAuth 2 login.
- `DATABASE_URL` – path to the SQLite database (defaults to `bot.db` in the repository root).
- `OAUTH_REDIRECT_URI` – URL registered in the Discord application (for example `https://your.domain/api/auth/callback`).
- `SECRET_KEY` – secret used to sign JWT session cookies for the dashboard.
- `DEBUG` – set to `true` to enable debug logging.

See `.env.example` for a complete list.

## Commands

Below is a high‑level list of slash commands implemented by the bot.  All commands are namespaced as slash commands and require appropriate roles:

| Command | Description |
| --- | --- |
| `/council create name:<string>` | Mark the current channel as a council.  Creates or renames the council record. |
| `/council remove` | Unmark the current channel as a council.  All motions will be closed. |
| `/council stats` | Display a summary of the council: number of members, active motion, and recent results. |
| `/config set key:<enum> value:<string|number|bool|channel|role|json>` | Update a configuration key for the current council. |
| `/config unset key:<enum>` | Remove a configuration key, reverting to defaults. |
| `/setweight target:<user|role> weight:<int>` | Assign a vote weight to a user or role.  When casting votes, weights are summed. |
| `/voteweights show` | Show the current weight map for this council. |
| `/motion show` | Display the currently active motion and its status. |
| `/motion new text:<string> majority:<fraction|percent>=default unanimous:<bool>=false` | Propose a new motion.  A private deliberation thread is created automatically. |
| `/motion kill` | End the current motion early; only the proposer or an admin may do this. |
| `/vote yes|no|abstain reason:<string(optional)>` | Cast a vote.  Buttons are provided for convenience.  If a reason is required, a modal will prompt for it. |
| `/lazyvoters` | Mention councilors who have not yet voted on the active motion. |
| `/archive range:<string>` | List motion archives within a date range. |
| `/archive view id:<int>` | View the details of a specific archive entry. |
| `/archive export` | Download a JSON export of motion archives including user IDs and reasons. |
| `/voteweights show` | Show the current vote weight assignments. |

The bot uses Discord’s app commands API.  The `CommandTree` container holds slash commands and is synchronised on startup.  Each command is implemented inside a Cog.  For more information on how slash commands work in `discord.py`, see the [guide](https://www.pythondiscord.com/pages/guides/python-guides/app-commands/) which describes the `CommandTree` object and the requirement to call `sync()`【399622367516235†L52-L67】.

### Buttons and modals

When a user interacts with buttons or modals, Discord sends an **interaction**.  The bot responds using the `InteractionResponse` provided by `discord.py`.  Modals provide a form‑like structure for collecting text; they consist of a title, a custom ID and up to five input fields【955820251987877†L56-L64】.  The bot uses modals to collect vote reasons when they are required.  To send a modal, call `await interaction.response.send_modal(modal)` from a slash command or button callback【955820251987877†L92-L104】.

## Web dashboard

The dashboard exposes a separate FastAPI application under `dashboard/app.py`.  It authenticates users with Discord OAuth 2 and stores the resulting user ID in a JWT cookie.  Users must have either the **Manage Guild** permission or a custom “Votum Admin” role to access write operations.  Views included:

* **Home** – lists all councils in the guilds the user manages, shows the active motion and quick statistics.
* **Council page** – allows editing configuration, opening/killing motions and viewing the motion queue.
* **Motion page** – shows a live tally using a WebSocket.  A table lists votes with reasons, weights and user IDs.  Exports are available as JSON or CSV.
* **Archives** – filter archives by date or council, view details and download exports.

Routes under `/api` expose JSON endpoints for councils, motions, votes, configurations and archives.  All responses and requests are validated with Pydantic models.  CSRF tokens protect POST/PUT/PATCH/DELETE requests, and rate limiting is applied to write operations.

The frontend uses Jinja2 templates and Tailwind CSS for styling.  WebSocket support is provided via FastAPI’s `websocket` route.  When votes are cast, the bot publishes an event to the dashboard; connected clients update the tally in real time.

## Running the dashboard

Run the dashboard separately from the bot:

```bash
uvicorn dashboard.app:app --port 8000 --reload
```

Ensure that your `.env` contains the OAuth 2 credentials and the correct `OAUTH_REDIRECT_URI`.  When deploying behind a reverse proxy, configure TLS termination there and set `HTTPS=1` so the app knows to use secure cookies.

## Testing

Basic unit tests live under `tests/`.  To run the tests:

```bash
pytest -q
```

Tests cover majority calculations, configuration validation, repository functions and core API routes.  You can extend them as you implement additional behaviour.

## Sample configuration snippets

Below are example JSON structures for `vote.weights` and `on.finish.actions` configuration keys:

```json
{
  "vote.weights": {
    "123456789012345678": 3,
    "987654321098765432": 2,
    "role:112233445566778899": 5
  },
  "on.finish.actions": [
    {
      "action": "forward",
      "target_council_id": 42,
      "text_prefix": "[Forwarded] "
    },
    {
      "action": "announce",
      "channel_id": 1337
    }
  ]
}
```

## Limitations

This implementation aims for feature parity with the original Votum but may require further refinement.  The GitHub integration provided by the environment is **read‑only**, so creating or pushing to repositories via this bot is not supported.  You can, however, clone this repository, customise it and deploy it yourself.
