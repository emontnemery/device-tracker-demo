# Device tracker client selection — core batch 1

Paths relative to `homeassistant/components/`.

## Framework notes (apply to many rows)

- **Legacy `DeviceScanner` / `see()` platforms (YAML `device_tracker:` platform)** inherit the
  framework `PLATFORM_SCHEMA` (`device_tracker/legacy.py:100-111`): `track_new_devices`
  (`CONF_TRACK_NEW`, legacy.py:103) and `new_device_defaults: {track_new_devices}` (legacy.py:94-99,
  107-109) — a coarse "track newly discovered devices" switch (default True). Plus per-device
  `track: true/false` in `known_devices.yaml` (schema legacy.py:1045, default False for hand-written
  entries; auto-added entries get `track_new`). That is per-device allow/deny via YAML, but it is
  **framework-level, not integration-provided**. Rows below bucket by the integration's *own*
  settings and flag `FW` where the legacy framework mechanism applies.
- **Config-entry `ScannerEntity`**: `entity_registry_enabled_default` (`device_tracker/entity.py:646-656`)
  creates trackers *disabled* unless the MAC is already known to the device registry. Not a user
  setting (doesn't count), but it is a built-in filter of sorts.

## Table

| Integration | Bucket | Keys / location | UI type | Default | Semantics | Removal |
|---|---|---|---|---|---|---|
| acaia | N/A (not a tracker platform) | — | — | — | Coffee scale; no device_tracker platform | — |
| actiontec | C (+FW) | YAML: host/username/password only (`actiontec/device_tracker.py:24-30`) | YAML | all scanned MACs reported | Legacy scanner; no own filter | FW (known_devices.yaml) |
| arris_tg2492lg | C (+FW) | YAML: password, host (`arris_tg2492lg/device_tracker.py:22-27`) | YAML | all | Legacy; no own filter | FW |
| aruba | C (+FW) | YAML: host/username/password (`aruba/device_tracker.py:28-34`) | YAML | all | Legacy; no own filter | FW |
| asuswrt | B | Options flow: `track_unknown` (`asuswrt/const.py:10`, `config_flow.py:80`, used `router.py:313,320`); `require_ip` (AP mode only, `config_flow.py:100`, `bridge.py:230`) | bool checkboxes | `track_unknown=False`; `require_ip=True` | `track_unknown=False` skips new clients with no name; `require_ip` drops clients without an IP in AP mode. `interface`/`dnsmasq` are stats/lease-file paths, not filters | No removal: already-tracked MACs (incl. restored from registry, `router.py:250-270`) stay even if option later turned off |
| bbox | C (+FW) | YAML: host (`bbox/device_tracker.py:28-30`) | YAML | all | Legacy; no own filter (`filter_named` at :66 is just a name lookup) | FW |
| bluetooth | N/A (not a tracker platform) | — | — | — | BLE stack; no device_tracker platform | — |
| bluetooth_le_tracker | A (YAML, via known_devices.yaml) + B | `known_devices.yaml` `track:` read explicitly (`bluetooth_le_tracker/device_tracker.py:114-127`) → `devs_to_track` / `devs_no_track`; `track_new_devices` (`:76`, `:195-200`); `track_battery`/`track_battery_interval` (`:43-50`, battery only) | YAML | FW `track_new_devices` default True; new devices need `MIN_SEEN_NEW=5` sightings (`:41,91`) | Both allow- (`track: true`) and deny-list (`track: false`) of specific BLE MACs; `track_new_devices: false` + no tracked devices → platform refuses setup (`:129-131`). Open BLE discovery (not single fixed beacon) so counted as scanner | FW; deny-listed devices never re-seen |
| bt_home_hub_5 | C (+FW) | YAML: host (`bt_home_hub_5/device_tracker.py:23-25`) | YAML | all | Legacy; no own filter | FW |
| bt_smarthub | C (+FW) | YAML: host, smarthub_model (`bt_smarthub/device_tracker.py:25-30`) | YAML | all | Legacy; no own filter | FW |
| cisco_ios | C (+FW) | YAML: host/username/password/port (`cisco_ios/device_tracker.py:21-30`) | YAML | all | Legacy; no own filter | FW |
| cisco_mobility_express | C (+FW) | YAML: host/username/password/ssl/verify_ssl (`cisco_mobility_express/device_tracker.py:30-38`) | YAML | all | Legacy; no own filter (SSID only exposed as extra attr) | FW |
| cppm_tracker | C (+FW) | YAML: host/client_id/api_key (`cppm_tracker/device_tracker.py:24-31`) | YAML | all online endpoints (`:76-81`, first 100) | Legacy; online-status check is inherent, not a user filter | FW |
| ddwrt | B (+FW) | YAML: `wireless_only` (`ddwrt/device_tracker.py:34-35,44-46`, used `:69,122,130`) | YAML bool | `True` | True = only wireless clients (Wireless endpoint); False = all LAN (DHCP/ARP) clients | FW |
| devolo_home_network | C | Config flow: ip_address/password only (`devolo_home_network/config_flow.py:25-30`); no options flow | — | every connected Wi-Fi station on the devolo AP (`device_tracker.py:36-45`) | Wi-Fi-only scope is inherent (`CONNECTED_WIFI_CLIENTS`), not selectable. Framework disabled-by-default unless MAC known applies | Never removed: trackers restored from registry on every setup (`device_tracker.py:47-58`) |
| dhcp | N/A (not a tracker platform) | — | — | — | Only *watches* existing ROUTER-source device_tracker states for discovery (`dhcp/__init__.py:129-131,374`); creates none | — |
| dlna_dmr | N/A (not a tracker platform) | — | — | — | Media player; grep hit was `seek` | — |
| fing | C | Config flow: ip_address/port/api_key (`fing/config_flow.py:38-44,93-95`); no options flow | — | every device the Fing agent knows (active or not) | Overrides `entity_registry_enabled_default=True` (`fing/device_tracker.py:93-96`) so even the framework disabled-default filter is bypassed | Yes: entities removed from registry when the device disappears from the agent's list (`device_tracker.py:30-46`) |
| fortios | C (+FW) | YAML: host/token/verify_ssl (`fortios/device_tracker.py:27-33`) | YAML | all online (API filter `format=...` at :84 is a field selector) | Legacy; no own filter | FW |

## Bucket summary

- **A**: bluetooth_le_tracker (YAML known_devices.yaml `track:` allow/deny, explicitly consumed by the integration; also coarse `track_new_devices`).
  - Note: every legacy `C (+FW)` row also technically supports per-device `track:` in known_devices.yaml via the framework; reclassify those as A if framework-level YAML counts.
- **B**: asuswrt (`track_unknown`, `require_ip` options), ddwrt (`wireless_only` YAML).
- **C**: actiontec, arris_tg2492lg, aruba, bbox, bt_home_hub_5, bt_smarthub, cisco_ios, cisco_mobility_express, cppm_tracker, fortios (all legacy, FW only); devolo_home_network, fing (config entry, no options).
- **N/A (not a tracker platform)**: acaia, bluetooth, dhcp, dlna_dmr.
