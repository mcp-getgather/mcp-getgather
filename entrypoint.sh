#!/bin/sh
set -e

# Start Xvfb display server
Xvfb :99 -screen 0 1920x1080x24 >/dev/null 2>&1 &
export DISPLAY=:99

# Start Xfce desktop and VNC server
startxfce4 >/dev/null 2>&1 &

# Start VNC server only if VNC_PASSWORD is set
if [ -n "$VNC_PASSWORD" ]; then
    # Create VNC password file
    mkdir -p /root/.vnc
    x11vnc -storepasswd "$VNC_PASSWORD" /root/.vncpass

    # Start x11vnc
    x11vnc \
        -forever \
        -usepw \
        -rfbport 5900 \
        -display :99 \
        -rfbauth /root/.vncpass \
        -listen 0.0.0.0 \
        -quiet \
        -no6 >/dev/null 2>&1 &
    echo "VNC server started on port 5900"
else
    echo "VNC_PASSWORD not set, VNC server not started"
fi

# Run D-BUS daemon
echo "Starting D-BUS daemon..."
rm -rf /run/dbus
mkdir -p /run/dbus
dbus-daemon --system --fork
echo "D-BUS daemon started with pid: $(cat /run/dbus/pid)"

# Start FastAPI server
/opt/venv/bin/python -m uvicorn getgather.api.main:app --host 0.0.0.0 --port 8000 --log-level debug