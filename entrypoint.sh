#!/bin/sh
set -e

# Start Xvfb display server
export DISPLAY=:99
echo "Starting Xvfb on DISPLAY=$DISPLAY..."
Xvfb :99 -screen 0 1920x1080x24 >/dev/null 2>&1 &

# Wait for Xvfb to start
while [ ! -e /tmp/.X11-unix/X99 ]; do
  sleep 0.1
done
echo "Xvfb running on DISPLAY=$DISPLAY"

echo "Starting JWM (Joe's Window Manager)"
jwm >/dev/null 2>&1 &

echo "Starting x11vnc server..."
x11vnc \
    -forever \
    -nopw \
    -rfbport 5900 \
    -display :99 \
    -listen 0.0.0.0 \
    -quiet \
    -no6 >/dev/null 2>&1 &
echo "VNC server started on port 5900"

# So that the desktop is not completely empty
xeyes &
xclock &

# Run D-BUS daemon
echo "Starting D-BUS daemon..."
rm -rf /run/dbus
mkdir -p /run/dbus
dbus-daemon --system --fork
echo "D-BUS daemon started with pid: $(cat /run/dbus/pid)"

# Start FastAPI server
/opt/venv/bin/python -m uvicorn getgather.api.main:app --host 0.0.0.0 --port 8000