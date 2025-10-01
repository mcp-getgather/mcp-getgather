#!/bin/sh
set -e

export DISPLAY=:99
export NO_AT_BRIDGE=1
export SESSION_MANAGER=""
export DBUS_SESSION_BUS_ADDRESS=""
export USER=root

echo "Starting TigerVNC server on DISPLAY=$DISPLAY..."
Xvnc -alwaysshared ${DISPLAY} -geometry 1920x1080 -depth 24 -rfbport 5900 -SecurityTypes None &
sleep 2
echo "TigerVNC server running on DISPLAY=$DISPLAY"

echo "Starting DBus session"
eval $(dbus-launch --sh-syntax)
export SESSION_MANAGER=""

echo "Starting JWM (Joe's Window Manager)"
cp /app/.jwmrc $HOME
jwm >/dev/null 2>&1 &

# So that the desktop is not completely empty
xeyes &

# Start FastAPI server
/opt/venv/bin/python -m uvicorn getgather.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips="*"
