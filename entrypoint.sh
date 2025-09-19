#!/bin/sh
set -e

# Start Xvfb display server
export DISPLAY=:99
export XAUTHORITY=/tmp/xauth99
rm -f "$XAUTHORITY"; touch "$XAUTHORITY"
xauth -f "$XAUTHORITY" add :99 . "$(mcookie)"
echo "Starting Xvfb on DISPLAY=$DISPLAY..."
Xvfb :99 -screen 0 1920x1080x24 -nolisten tcp -auth "$XAUTHORITY" >/dev/null 2>&1 &
# Wait for Xvfb socket to appear
while [ ! -e /tmp/.X11-unix/X99 ]; do
  sleep 0.1
done
# wait until the server really answers (not just the socket exists)
for i in $(seq 1 100); do xdpyinfo >/dev/null 2>&1 && break; sleep 0.1; done
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

# start mcp inspector
if [ -z "$MCP_INSPECTOR_DISABLED" ] || [ ! "$MCP_INSPECTOR_DISABLED" = "true" ]; then
  if [ -z $MCP_PROXY_AUTH_TOKEN ]; then
    export MCP_PROXY_AUTH_TOKEN=getgather
  fi
  echo "Starting MCP inspector..."
  HOST=0.0.0.0 ALLOWED_ORIGINS=http://localhost:23456 \
    MCP_AUTO_OPEN_ENABLED=false MCP_PROXY_AUTH_TOKEN=$MCP_PROXY_AUTH_TOKEN \
    npx @modelcontextprotocol/inspector &
else
  echo "MCP inspector disabled"
fi

# Start FastAPI server
/opt/venv/bin/python -m uvicorn getgather.main:app --host 0.0.0.0 --port 23456 --proxy-headers --forwarded-allow-ips="*"
