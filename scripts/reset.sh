#!/usr/bin/env bash
# Delete all state of the demo instances (run stop.sh first). start.sh sets them up again.
# Keeps only configuration.yaml and the custom_components symlink in each instance.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
for name in today proposed unifi; do
  find "$ROOT/instances/$name" -mindepth 1 -maxdepth 1 \
    ! -name configuration.yaml ! -name custom_components -exec rm -rf {} +
done
