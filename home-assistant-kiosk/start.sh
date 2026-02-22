#!/bin/bash

# Wait for display to be ready
while [ -z "$DISPLAY" ]; do
    sleep 1
    export DISPLAY=:0
done

# Wait for X server to be ready
while ! xset q &>/dev/null; do
    sleep 1
done

# Disable screen saver and power management
xset s off
xset -dpms
xset s noblank

# Hide cursor after 1 second of inactivity
unclutter -idle 1 &

# Wait a bit for the server to start (service should already be running)
sleep 10

# Start Chromium in kiosk mode
chromium-browser \
    --kiosk \
    --no-sandbox \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-translate \
    --disable-features=TranslateUI \
    --start-maximized \
    --disable-pinch \
    --force-device-scale-factor=0.5 \
    --overscroll-history-navigation=0 \
    --disable-background-timer-throttling \
    --disable-backgrounding-occluded-windows \
    --disable-renderer-backgrounding \
    --disable-features=TranslateUI \
    --disable-ipc-flooding-protection \
    --disable-background-mode \
    --disable-default-apps \
    --disable-extensions \
    --password-store=basic \
    --use-mock-keychain \
    --no-first-run \
    --fast \
    --fast-start \
    --disable-default-apps \
    http://192.168.68.108:8123/dashboard-tablet/wall-tablet-1