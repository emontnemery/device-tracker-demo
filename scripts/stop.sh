#!/usr/bin/env bash
# Stop everything started by start.sh.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
pkill -f "homeassistant -c $ROOT/instances/" || true
pkill -f "$ROOT/fake_unifi/fake_unifi.py" || true
