# Device tracker client selection: core batch 3

Rubric: `../rubric.md`. Read-only; all paths are relative to `homeassistant/components/`.

**Legacy-framework caveat (applies to every legacy `get_scanner`/`setup_scanner` platform below):**
the shared legacy `device_tracker` YAML schema (`device_tracker/legacy.py:94-110`) provides
`track_new_devices` / `new_device_defaults: {track_new_devices: ...}` (default `True`,
`device_tracker/const.py:81-82`). In addition, `known_devices.yaml` has a per-device `track:` flag.
These are framework features, not integration settings. The table buckets each legacy
platform on its **own** settings: C means the integration adds nothing. When the framework is
counted, they become B through `track_new_devices: false`, or A as a YAML deny-list through
`track: false` in `known_devices.yaml`.

| Integration | Bucket | Kind | Selection keys (file:line) | UI / default / semantics | Removal |
|---|---|---|---|---|---|
| private_ble_device | N/A-single-target | config entry, `BaseScannerEntity` with BLUETOOTH_LE | `irk` (config_flow.py:18,73) | Each config entry is one IRK, and the entry itself is the selection. The flow creates one tracker per entry (device_tracker.py:24). | n/a |
| probe_plus | not a tracker platform | — | — | No `device_tracker.py`. Only sensors (BLE food probe). | — |
| quantum_gateway | C | legacy `get_scanner` | only host/ssl/password (device_tracker.py:21-27) | Tracks all clients. Only the framework filters apply. | framework |
| ruckus_unleashed | **A** | config entry, `ScannerEntity` | options `mac_filter` (`CONF_MAC_FILTER`, const.py:9); options flow config_flow.py:133-180; applied in device_tracker.py:29,50-51,77 | UI `cv.multi_select` of currently connected clients ("hostname (mac)"), with previously selected offline MACs kept as "Unknown (mac)". **Allow-list.** Default `[]`, and empty means track all. The restore of offline registry entities also honours the filter. | Yes. When the new filter is non-empty, the options flow removes registry entries whose unique_id is not in it (config_flow.py:143-153). `OptionsFlowWithReload` then reloads. |
| sky_hub | C | legacy `async_get_scanner` | `host` only (device_tracker.py:22-24) | All clients | framework |
| snmp | C | legacy `async_get_scanner` | `baseoid`, host, community, keys (device_tracker.py:45-53) | `baseoid` picks the SNMP MAC table to read, not individual clients. All MACs found are tracked (device_tracker.py:142). | framework |
| sofar | not a tracker platform | — | — | No `device_tracker.py` (inverter). | — |
| swisscom | C | config entry, `ScannerEntity` (YAML import removed; only raises a repair, device_tracker.py:27-50) | host/username/password only (config_flow.py:22-27). No options flow. | Every LAN device with a key gets a tracker (device_tracker.py:64-69, coordinator.py:61). | None |
| synology_srm | C | legacy `get_scanner` | connection keys only (device_tracker.py:33-42) | All clients | framework |
| thomson | C | legacy `get_scanner` | host/user/password (device_tracker.py:32-38) | All clients | framework |
| tomato | C | legacy `get_scanner` | host/port/ssl/verify_ssl/user/password/http_id (device_tracker.py:33-45) | All clients | framework |
| ubus | C | legacy `get_scanner` | host/user/password, `dhcp_software` (device_tracker.py:26-35) | `dhcp_software` only selects the name-resolution source, not which clients are tracked. | framework |
| unifi_direct | C | config entry, `ScannerEntity` (YAML imported, device_tracker.py:34-80) | host/username/password/port (config_flow.py:13-19). No options flow. | Every MAC returned by the AP gets a tracker (device_tracker.py:91-101). | None |
| upc_connect | C | legacy `async_get_scanner` | password/host (device_tracker.py:25-30) | All clients | framework |
| vodafone_station | C | config entry, `ScannerEntity` | Options flow has only `consider_home` (config_flow.py:212-230) | Every router device gets a tracker (device_tracker.py:56-63). `consider_home` is a presence timeout, not a filter. | Stale (vanished) devices are cleaned up automatically (coordinator.py:176-181, `cleanup_device_tracker`). This is not user selection. |
| wiim | not a tracker platform | — | — | No `device_tracker.py` (media_player only). | — |
| xiaomi | C | legacy `get_scanner` | host/username/password (device_tracker.py:22-28) | All clients | framework |
| xiaomi_miio | C | legacy `get_scanner` (Mi WiFi Repeater). YAML-only; the integration's config flow does not cover the tracker. | host/token (device_tracker.py:21-28) | All associated stations (device_tracker.py:76) | framework |
| zha | N/A | config entry, `ScannerEntity` | — | Tracks ZHA's own Zigbee devices (one "Device scanner" entity per device that supports it, device_tracker.py:44-55), not network clients. | — |

## Sanity sweep: other device_tracker platforms not in either list

I grepped for `ScannerEntity|SourceType.ROUTER|get_scanner|DeviceScanner|setup_scanner`. It found 4 extra integrations, none of which is a network-client scanner:

| Integration | Bucket | Notes |
|---|---|---|
| aprs | N/A (GPS/APRS) | Legacy `setup_scanner` with `see()`. Required `callsigns` list (device_tracker.py:44,56) is a per-callsign allow-list, but these are radio positions, not network clients. |
| demo | N/A | Demo legacy `setup_scanner` (device_tracker.py:12) |
| fleetgo | N/A (GPS vehicles) | Legacy `setup_scanner`. Optional `include` list of license plates (device_tracker.py:33-35,89), where empty means all. It is an allow-list, but of vehicles, not network clients. |
| google_maps | N/A (GPS) | Legacy `setup_scanner`, `SourceType.GPS` (device_tracker.py:145) |

Also noted (not caught by the grep): mqtt `device_tracker` lets the user set `source_type` (it can be `router`) per configured entity (mqtt/device_tracker.py:48-74). That makes it N/A-single-target. The remaining `device_tracker.py` platforms (autoskope, fressnapf_tracker, geofency, gpslogger, husqvarna_automower, icloud, ituran, locative, lojack, mobile_app, mysensors, nrgkick, paj_gps, renault, scorpiontrack, starline, starlink, subaru, template, tesla_fleet, teslemetry, tessie, tile, traccar, traccar_server, tractive, victron_gx, volvo) are GPS/`TrackerEntity` and out of scope.

## Summary
- **Bucket A:** ruckus_unleashed (`mac_filter` options multi-select allow-list of discovered clients; empty means all; deselected trackers are removed).
- **Bucket B:** none (when only integration-specific settings are counted). Every legacy platform gets B/A only through the framework's `track_new_devices` / `known_devices.yaml` `track:`.
- **Bucket C:** quantum_gateway, sky_hub, snmp, swisscom, synology_srm, thomson, tomato, ubus, unifi_direct, upc_connect, vodafone_station, xiaomi, xiaomi_miio
- **N/A:** private_ble_device (single-target), zha (own Zigbee devices)
- **Not a tracker platform:** probe_plus, sofar, wiim
