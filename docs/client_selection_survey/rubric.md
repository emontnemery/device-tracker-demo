# Rubric: user-selectable device tracker (scanner) client selection

Question per integration: does it offer USER-FACING settings (options flow, config flow,
subentries, or YAML config) that let the user choose WHICH network clients/devices get a
scanner device tracker (ScannerEntity / SourceType.ROUTER/legacy see()) created?

Reference POSITIVE: core `unifi` options flow -> `CONF_CLIENT_SOURCE` ("client_source":
multi-select of known clients; if non-empty, ONLY those clients get trackers), plus coarser
filters: `track_clients` on/off, `track_wired_clients`, `ssid_filter`.
Reference NEGATIVE: core `tplink_omada` — creates trackers with no user selection setting.

Classify each integration into exactly one bucket:
- A  PER-DEVICE SELECTION: user picks specific clients (multi-select of discovered clients,
     list of MACs/hostnames/IPs, include/allow-list or exclude/deny-list of specific devices).
     Note whether it is an allow-list, deny-list, or both, and whether it is a UI selector of
     discovered clients vs free-text MAC/IP entry vs YAML.
- B  COARSE FILTER ONLY: no per-device choice, but category filters (track on/off globally,
     wired/wireless, SSID/interface/network/VLAN filter, "only new devices", "track new
     devices default disabled", etc.).
- C  NONE: trackers created for every client with no selection setting (entity-registry
     enable/disable doesn't count; `new devices enabled by default = False` style
     options/pref_disable_new_entities count as B and should be noted).
- N/A  Not a network-client scanner (e.g. tracks the integration's own device(s) only,
     BLE beacon of a fixed configured device, or scanner of a single configured target like
     ping host) — say why briefly. If a single-target integration where the config entry
     IS the selection (e.g. one entry per tracked host), put it in N/A-single-target.

For each integration record: name, bucket, the exact option keys / config keys and where they
live (file:line), UI selector type, default behaviour, and one sentence on semantics
(e.g. "empty = track all"). Also note removal behaviour if obvious (are trackers for
deselected clients removed?). Keep each entry concise.

Read code, don't guess. Check config_flow.py, const.py, device_tracker.py, __init__.py,
strings.json/translations, and legacy PLATFORM_SCHEMA.
