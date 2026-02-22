# home-assistant-kiosk

Turns a Raspberry Pi into a dedicated Home Assistant dashboard kiosk using Chromium in kiosk mode.

## How it works

`start.sh` waits for the X display server, disables screen blanking/power management, hides the cursor, then launches Chromium in fullscreen kiosk mode pointed at a Home Assistant dashboard.

## Key details

- Target URL: `http://192.168.68.108:8123/dashboard-tablet/wall-tablet-1`
- Uses `--force-device-scale-factor=0.5` to fit more content on screen.
- `unclutter` is used to auto-hide the mouse cursor.
- Script expects to run in an X11 session (DISPLAY=:0).

## Dependencies (on the Pi)

- `chromium-browser`
- `unclutter`
- `xset` (part of x11-xserver-utils)

## Setup

The script is intended to be started on boot, typically via a systemd service or autostart entry in the desktop environment.
