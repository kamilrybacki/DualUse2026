#!/usr/bin/env bash
# Start the headless fldigi test rig: PulseAudio null sink "cable" + fldigi under Xvfb with
# XML-RPC on 7362. Proven in a bare Ubuntu 24.04 container (no sound hardware) on 2026-09-07.
#
#   sudo apt install fldigi pulseaudio pulseaudio-utils xvfb
#   tools/fldigi/rig_up.sh              # start (idempotent)
#   tools/fldigi/rig_up.sh stop
#   make decode FILE=x.wav              # uses --player "paplay --device=cable" via env below
#
# Then: uv run python tools/fldigi/decode_test.py file.wav --player "paplay --device=cable"
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CFG="${FLDIGI_CONFIG_DIR:-$HERE/config}"
PORT="${FLDIGI_XMLRPC_PORT:-7362}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp/xdg-$(id -u)}"
mkdir -p "$XDG_RUNTIME_DIR" "$CFG"

if [[ "${1:-}" == "stop" ]]; then
  pkill -f "fldigi --config-dir $CFG" || true
  pactl unload-module module-null-sink 2>/dev/null || true
  echo "rig stopped"
  exit 0
fi

# 1. PulseAudio with a virtual cable (no hardware needed)
if ! pactl info >/dev/null 2>&1; then
  pulseaudio -D --exit-idle-time=-1 --disallow-exit >/dev/null 2>&1 || true
  sleep 1
fi
if ! pactl list short sinks | grep -q '^[0-9]*\s*cable\s'; then
  pactl load-module module-null-sink sink_name=cable sink_properties=device.description=cable >/dev/null
fi
pactl set-default-sink cable
pactl set-default-source cable.monitor

# 2. Minimal fldigi config: PulseAudio backend, XML-RPC on, RSID off, no first-run wizard.
#    Only written if absent so GUI-made changes survive.
if [[ ! -f "$CFG/fldigi_def.xml" ]]; then
  cp "$HERE/fldigi_def.minimal.xml" "$CFG/fldigi_def.xml"
fi

# 3. fldigi headless
if ! pgrep -f "fldigi --config-dir $CFG" >/dev/null; then
  setsid nohup xvfb-run -a fldigi --config-dir "$CFG" --xmlrpc-server-port "$PORT" -i \
    >"$CFG/fldigi.log" 2>&1 </dev/null &
  for _ in $(seq 1 30); do
    sleep 1
    if curl -s -o /dev/null "http://127.0.0.1:$PORT/RPC2"; then break; fi
  done
fi

python3 - "$PORT" <<'EOF'
import sys, xmlrpc.client
rpc = xmlrpc.client.ServerProxy(f"http://127.0.0.1:{sys.argv[1]}")
print("fldigi", rpc.fldigi.version(), "| modems:", [m for m in rpc.modem.get_names() if m in ("NAVTEX", "SITORB")])
EOF
echo "rig up: play with  paplay --device=cable <wav>  | decode_test.py --player \"paplay --device=cable\""
