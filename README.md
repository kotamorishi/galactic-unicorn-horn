# Galactic Unicorn Horn

Fetches calendar events from Apple Calendar and Google Calendar, then displays them on an LED matrix display ([Galactic Unicorn Leg](https://github.com/kotamorishi/galactic-unicorn-leg)) via Raspberry Pi.

## Supported Calendars

- **Apple Calendar (iCloud)** — CalDAV authentication. No need to make your calendar public
- **Google Calendar** — iCal URL. Uses the secret address

Both can be used simultaneously.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Fonts

Download [PixelMplus12](https://github.com/itouhiro/PixelMplus) and place it in the `fonts/` directory.

```
fonts/
  PixelMplus12-Regular.ttf
  PixelMplus12-Bold.ttf   (optional)
```

> PixelMplus12 is a free font. It is not included in this repository due to licensing.

### 3. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` to set the device IP and calendar credentials.

### 4. Run

```bash
python main.py
```

## Calendar Configuration

### Apple Calendar (iCloud)

Apple Calendar connects via CalDAV authentication. You do **not** need to make your calendar public.

#### Steps

1. Sign in to [appleid.apple.com](https://appleid.apple.com/)
2. Go to **Sign-In and Security** → **App-Specific Passwords**
3. Click **"+"** to generate a password (name it anything, e.g. "LED Display")
4. Copy the generated password in `xxxx-xxxx-xxxx-xxxx` format
5. Set the following in `.env`:

```
ICLOUD_USERNAME=your@icloud.com
ICLOUD_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

This will fetch events from all your iCloud calendars.

> You do not need to set `ICAL_URLS` for Apple Calendar.

### Google Calendar

Google Calendar connects via iCal URL.

#### Steps

1. Open [Google Calendar](https://calendar.google.com/)
2. Click **"⋮"** next to the target calendar → **"Settings and sharing"**
3. Copy the URL under **"Secret address in iCal format"**
4. Set the following in `.env`:

```
ICAL_URLS=https://calendar.google.com/calendar/ical/xxxxxxxx/basic.ics
```

For multiple calendars, separate URLs with commas:

```
ICAL_URLS=https://calendar.google.com/.../1.ics,https://calendar.google.com/.../2.ics
```

> This URL contains a random string that is impossible to guess. Only those who know the URL can access it. You do not need to make the calendar public.

### Using Both Apple + Google

Set both and all events will be merged and displayed in chronological order.

```
ICLOUD_USERNAME=your@icloud.com
ICLOUD_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
ICAL_URLS=https://calendar.google.com/calendar/ical/xxxxxxxx/basic.ics
```

## How Display Timing Works

Events are displayed based on their start time. For example, a `09:00-10:00 ABC` event:

| Time | Action | Color |
|------|--------|-------|
| 08:49 | Display off | — |
| 08:50 | Notification sound plays, shows `09:00-10:00 ABC` | Green |
| 09:00 | Color changes to red (event started) | Red |
| 09:05 | Display cleared | — |

- **10 min before start**: Display turns on (green) + notification sound
- **At start time**: Color changes to red
- **5 min after start**: Display is cleared
- Active events (red) take priority over upcoming events (green) if overlapping
- Sound plays only once per event

## Configuration Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `DEVICE_IP` | IP address of Galactic Unicorn Leg | `192.168.1.100` |
| `ICLOUD_USERNAME` | Apple ID (email address) | — |
| `ICLOUD_APP_PASSWORD` | iCloud app-specific password | — |
| `ICAL_URLS` | iCal URLs (comma-separated for multiple) | — |
| `FETCH_INTERVAL` | Calendar fetch interval in seconds | `300` |
| `SCROLL_SPEED` | Scroll speed (`slow` / `medium` / `fast`) | `medium` |
| `FONT_PATH` | Path to font file | `fonts/PixelMplus12-Regular.ttf` |
| `FONT_SIZE` | Font size in pixels | `12` |

## Running as a Service (Raspberry Pi)

To run as a background service that starts automatically on boot:

```bash
# Copy the service file
sudo cp galactic-unicorn-horn.service /etc/systemd/system/

# Edit the service file if your install path or user differs from /home/pi/
sudo nano /etc/systemd/system/galactic-unicorn-horn.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable galactic-unicorn-horn
sudo systemctl start galactic-unicorn-horn
```

Useful commands:

```bash
# Check status
sudo systemctl status galactic-unicorn-horn

# View logs
journalctl -u galactic-unicorn-horn -f

# Restart after config changes
sudo systemctl restart galactic-unicorn-horn

# Stop
sudo systemctl stop galactic-unicorn-horn
```

Key features:
- **Auto-start** on boot (`enable`)
- **Auto-restart** on crash (restarts after 10 seconds)
- **Logs** managed by journald (no log files to rotate)
- **Waits for network** before starting

## Security

- `.env` is included in `.gitignore` and will not be committed to Git
- If your iCloud app-specific password is compromised, revoke it at [appleid.apple.com](https://appleid.apple.com/)
- If your Google Calendar secret address is compromised, reset it from Google Calendar settings

## Testing

```bash
python3 -m pytest tests/ -v
```
