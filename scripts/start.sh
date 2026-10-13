#!/usr/bin/env bash
# Start the fake UniFi controller and the three demo instances; set up fresh ones.
# HASS_PYTHON must point at a Python that has Home Assistant installed, e.g. the
# .venv/bin/python of a core dev checkout.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${HASS_PYTHON:?set HASS_PYTHON to the Python of a Home Assistant core checkout}"

nohup "$PY" -I "$ROOT/fake_unifi/fake_unifi.py" > "$ROOT/fake_unifi/run.log" 2>&1 &
declare -A PORTS=([today]=8124 [proposed]=8125 [unifi]=8126)
fresh=()
for name in today proposed unifi; do
  dir="$ROOT/instances/$name"
  [ -e "$dir/.storage/onboarding" ] || fresh+=("$name")
  if [ ! -e "$dir/.storage/http" ]; then
    # Confirmed ("stable") HTTP config, so there's no port-change trial to confirm
    mkdir -p "$dir/.storage"
    cat > "$dir/.storage/http" <<JSON
{
  "version": 3,
  "minor_version": 1,
  "key": "http",
  "data": {
    "stable": {
      "server_port": ${PORTS[$name]},
      "cors_allowed_origins": ["https://cast.home-assistant.io"],
      "login_attempts_threshold": -1,
      "ip_ban_enabled": true,
      "ssl_profile": "modern_v6",
      "use_x_frame_options": true,
      "created_at": "2026-10-13T00:00:00+00:00",
      "error": null,
      "error_message": null
    },
    "pending": null,
    "yaml_migration_done": true
  }
}
JSON
  fi
  nohup "$PY" -m homeassistant -c "$dir" > "$dir/run.log" 2>&1 &
done
for name in "${fresh[@]}"; do
  "$PY" -I "$ROOT/scripts/setup_demo.py" "$name"
done
echo "today: http://localhost:8124  proposed: http://localhost:8125  unifi: http://localhost:8126"
echo "login: demo / demodemo (Erik) or anna / annaanna (Anna)"
