# CLAUDE.md — Horitas v2 Project Context

## What is Horitas?

A Discord bot that announces the current time via voice every hour on the hour. It connects to the voice channel with the most users, plays an audio sequence (intro → TTS announcement → outro), and disconnects.

## Tech Stack

- **Python 3.12** with `discord.py[voice]` (>=2.3)
- **gTTS** (>=2.5) for text-to-speech generation
- **aiosqlite** (>=0.19) for async SQLite database (per-guild config)
- **pytz** (>=2024.1) for timezone handling
- **python-dotenv** (>=1.0) for environment variable loading
- **FFmpeg** for audio playback (system dependency, included in Docker image)
- **Docker** + **Docker Compose** for containerized deployment
- **pytest** + **pytest-asyncio** for testing (dev only)

## Project Structure

```
horitas/
├── src/                    # Bot source code
│   ├── __init__.py
│   ├── main.py             # Entry point: load config → create bot → run
│   ├── bot.py              # Bot subclass (setup_hook, auto cog loading)
│   ├── config.py           # Dataclass config from env vars with validation
│   ├── database.py         # SQLite data layer (aiosqlite, auto-migrate)
│   ├── cogs/               # Discord.py cogs (modular features)
│   │   ├── __init__.py
│   │   ├── announcer.py    # Hourly task + announcement logic (multi-guild)
│   │   ├── commands.py     # Hybrid commands (slash + prefix)
│   │   └── health.py       # File-based healthcheck for Docker
│   ├── services/           # Business logic (no Discord imports)
│   │   ├── __init__.py
│   │   ├── audio.py        # Audio playback + random pool selection
│   │   ├── tts.py          # TTS generation (gTTS, async, with fallback)
│   │   ├── phrases.py      # Dynamic phrases: DB → JSON → hardcoded fallback
│   │   └── scheduler.py    # Precise next-hour delay calculation
│   └── utils/              # Shared utilities
│       ├── __init__.py
│       ├── logging.py      # Structured logging setup (no print!)
│       └── paths.py        # Absolute path resolution (no cwd dependency)
    ├── admin/                  # Optional Flask web admin panel
    │   ├── Dockerfile          # Separate container (python:3.12-slim)
    │   ├── app.py              # Flask app (routes + auth)
    │   ├── database.py         # Synchronous SQLite (stdlib, WAL mode)
    │   ├── requirements.txt    # Flask >=3.0
    │   ├── templates/          # Jinja2 templates (Bootstrap 5 dark)
    │   │   ├── base.html       # Layout with navbar
    │   │   ├── login.html      # Password auth
    │   │   ├── dashboard.html  # Bot status overview
    │   │   ├── phrases.html    # CRUD phrases per hour
    │   │   ├── audio.html      # Upload/delete audio files
    │   │   └── config.html     # Per-guild config
    │   └── static/             # CSS + JS
    │       ├── style.css
    │       └── app.js
    ├── audio/                  # Audio files (Docker volume, read-only)
    │   ├── intro/              # Pool: random intro sounds (e.g. bells.mp3)
    │   ├── outro/              # Pool: random outro sounds (e.g. final.mp3)
    │   └── phrases.json.example # Template for custom phrases (copy to phrases.json)
├── data/                   # Persistent data (Docker volume, gitignored)
│   └── config.db           # SQLite database (auto-created)
├── tests/                  # pytest test suite (mocks, no token needed)
│   ├── __init__.py
│   ├── conftest.py         # Shared fixtures and mocks
│   ├── test_config.py
│   ├── test_database.py
│   ├── test_audio_service.py
│   ├── test_tts_service.py
│   ├── test_phrases_service.py
│   ├── test_scheduler.py
│   ├── test_announcer.py
│   ├── test_logging.py
│   └── test_paths.py
    ├── CONTRIBUTING.md        # Contributor guide
├── .github/workflows/      # CI/CD pipelines
│   ├── test.yml            # Run tests on every PR
│   └── release.yml         # Build + push to ghcr.io on tag v*
├── Dockerfile              # Multi-stage build (python:3.12-slim + ffmpeg)
├── docker-compose.yml      # Bot-only deployment
├── docker-compose.admin.yml # Override: adds web admin service
├── Makefile                # Shortcuts: test, build, run, release
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Dev/test dependencies (includes prod)
├── pyproject.toml          # Project metadata + pytest config
├── .env.example            # Template for environment variables
├── .gitignore
├── .dockerignore
├── LICENSE                 # MIT
└── README.md               # User-facing docs + quick setup
```

## Key Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_TOKEN` | ✅ | — | Bot token from Discord Developer Portal |
| `BOT_PREFIX` | ❌ | `!` | Command prefix for text commands |
| `DEFAULT_TZ` | ❌ | `Europe/Madrid` | Default timezone for announcements |
| `LOG_LEVEL` | ❌ | `INFO` | Python logging level (DEBUG/INFO/WARNING/ERROR) |
| `AUDIO_DIR` | ❌ | `/app/audio` | Path to audio files directory |
| `DATA_DIR` | ❌ | `/app/data` | Path to persistent data directory |
| `ADMIN_PASSWORD` | ⚠️ | — | Password for admin panel (required if using admin) |
| `ADMIN_SECRET_KEY` | ❌ | auto | Flask session secret (auto-generated if not set) |

## Architecture Decisions

1. **Cogs pattern**: Each feature area is a discord.py Cog for modularity
2. **Services layer**: Business logic separated from Discord concerns — services do NOT import discord
3. **Audio pools**: Intro/outro sounds randomly selected from directories (supports `.mp3`, `.ogg`, `.wav`)
4. **Multi-guild**: Bot supports multiple servers with per-guild config stored in SQLite
5. **Timezone-aware**: All datetime operations use timezone-aware objects via `pytz`
6. **Graceful degradation**: gTTS failure → log warning, continue without TTS. Empty pool → warning, skip that step
7. **No print()**: All output uses Python `logging` module with structured format
8. **Phrase fallback**: DB → `phrases.json` → hardcoded default. Admin panel writes to DB, bot without admin reads from JSON
9. **Admin panel**: Separate Flask container shares DB/audio via Docker volumes. Auth via password env var
10. **Example files pattern**: `.env.example` and `phrases.json.example` are tracked; `.env` and `phrases.json` are gitignored
11. **Absolute paths**: `pathlib.Path` resolved from config — never rely on cwd

## Audio Sequence

```
intro (random from pool) → TTS (dynamic phrase with {hora}) → outro (random from pool)
```

Each step is independent — if one fails, the sequence continues with the remaining steps.

## Commands

| Command | Access | Description |
|---------|--------|-------------|
| `/forzar` | Owner only | Force immediate announcement in current guild |
| `/estado` | Everyone | Bot status (uptime, guilds, next announcement) |
| `/sync` | Owner only | Sync slash commands (manual, never auto) |
| `/config timezone <zone>` | Admin | Set server timezone (e.g. `Europe/Madrid`) |
| `/config canal <mode>` | Admin | Set announcement channel mode (`mas_usuarios` / `canal_fijo`) |

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS guild_config (
    guild_id INTEGER PRIMARY KEY,
    timezone TEXT DEFAULT 'Europe/Madrid',
    announce_mode TEXT DEFAULT 'mas_usuarios',
    channel_id INTEGER DEFAULT NULL,
    enabled INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS phrases (
    hour_key TEXT PRIMARY KEY,    -- "0"-"23" or "default"
    phrase TEXT NOT NULL           -- may contain {hora} placeholder
);
```

- Auto-created on first run via migrations in `database.py`
- Missing guild → defaults applied automatically
- Modes: `mas_usuarios` (most users), `canal_fijo` (fixed channel)
- Phrases table used by admin panel; empty table → falls back to `phrases.json`

## Testing

```bash
# Run tests (no Discord token needed — uses mocks)
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Via Makefile
make test
```

All tests use `unittest.mock.AsyncMock` — no real Discord connection required.

## Docker

```bash
# Bot only
docker compose up -d

# Bot + Admin panel (set ADMIN_PASSWORD in .env first)
docker compose -f docker-compose.yml -f docker-compose.admin.yml up -d

# Check health
docker inspect --format='{{.State.Health.Status}}' horitas-bot
```

Admin panel runs at `http://127.0.0.1:8080` (local only).

## Code Conventions

- **Language**: Code in English, user-facing strings (bot messages, phrases) in Spanish
- **Logging**: Always use `logging.getLogger(__name__)` — never `print()`
- **Async**: Use `asyncio.to_thread()` for blocking I/O (gTTS, file ops)
- **Type hints**: All function signatures should have type hints
- **Error handling**: Catch specific exceptions, log with `logger.exception()`, never crash silently
- **Naming**: snake_case for files/functions, PascalCase for classes, UPPER_CASE for constants

## Common Gotchas

- `end.mp3` from the original bot does NOT exist — the new version uses intro/outro pools instead
- Token must be regenerated from the Discord Developer Portal (old one was exposed in `.env`)
- `ffmpeg` is required at runtime — included in the Docker image, not in requirements.txt
- Audio pools can be empty without crashing (warning logged, step skipped)
- TTS files are temporary and cleaned up after playback via `finally` blocks
- `%-I` strftime format is Linux-only — use `%I` with `.lstrip('0')` for portability
- Slash commands are NOT auto-synced — use `/sync` manually after deployment
- SQLite DB lives in `data/` volume — survives container restarts
- `phrases.json` is gitignored — copy from `phrases.json.example` to customize
- Admin panel uses synchronous `sqlite3` (not `aiosqlite`) with WAL mode for safe concurrent access with the bot
- Admin `database.py` is a separate file from bot `database.py` — same schema, different async models
