# Galactic Unicorn Horn

Fetches calendar events and displays them on an LED matrix display ([Galactic Unicorn Leg](https://github.com/kotamorishi/galactic-unicorn-leg)) via Raspberry Pi.

## Tech Stack

- **Language:** Python 3
- **Libraries:** icalendar, requests, python-dotenv, Pillow, caldav
- **Target device:** Raspberry Pi (sends HTTP requests to Galactic Unicorn Leg)
- **Calendar integration:**
  - Google Calendar: iCal URL (secret address, no auth required)
  - Apple Calendar: CalDAV authentication (app-specific password, no public setting required)

## Project Structure

```
main.py            # Main loop (periodically fetch calendar → display on LED)
config.py          # Load settings from .env
renderer.py        # Text → bitmap conversion (Pillow, PixelMplus12)
icloud_calendar.py # Apple CalDAV auth for private calendar access
llm_helper.py      # LLMHAT/Ollama detection and natural language formatting
.env.example       # Environment variable template
requirements.txt   # Python package dependencies
fonts/             # Pixel fonts (not committed, see README.md)
tests/             # pytest tests
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with calendar credentials and device IP
python main.py
```

## Environment Variables

Managed via `.env` file (in `.gitignore`). See `.env.example` for reference.

## Galactic Unicorn Leg API

- `POST /api/bitmap` — Bitmap display (used by this project. mono format, base64 encoded, max width 5000px)
- `DELETE /api/bitmap` — Clear bitmap (return to text mode)
- `POST /api/message` — Text display (ASCII only. Japanese not supported)
- `GET /api/status` — Get device status
- `POST /api/schedules` — Set schedules
- Max connections: 1-2, keep requests under 1/sec

**Important:** Text API (`POST /api/message`) supports ASCII only. For Japanese, use bitmap API (`POST /api/bitmap`). This project always uses bitmap API since calendar events may contain Japanese.

## Testing

```bash
python3 -m pytest tests/ -v
```

## Development Guidelines

- All code, comments, commit messages, and documentation must be in English
- Keep secrets (iCal URLs, iCloud credentials) in `.env`, never hardcode
- Keep at least 1 second interval between LED device requests
- Commit and push frequently, even for small changes
- **README sync:** README.md (English) and README_jp.md (Japanese) must have the same content. When updating one, always update the other to match
