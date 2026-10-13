# HACS batch 3: user-selectable device-tracker client selection

Rubric: `../rubric.md`.
Paths below are relative to each integration's `custom_components/<domain>/` dir under
`<local clone of HACS integrations>/`. "FW" = only the generic legacy device_tracker
framework mechanisms apply (`track_new_devices` / `new_device_defaults` in the shared legacy
PLATFORM_SCHEMA, per-device `track:` in `known_devices.yaml`); bucket reflects the integration's
own settings (same convention as core_batch1/core_batch3/hacs_batch2).

## Assigned integrations

| Integration | Bucket | Mechanism / keys | UI type | Default / semantics |
|---|---|---|---|---|
| juacas/zte_tracker (zte_tracker) | B | `register_new_devices` in entry.options, toggled by a "Register New Devices" switch entity; `remove_tracked_entity` service (MAC) | Switch entity (not in the flow) + service with free-text MAC | Default True = every seen client; off = freeze set (only clients already in entity registry); deletion is manual via service |
| lrehmann/pihole_presence (pihole_presence) | B (weak) | `stale_device_days` (recency filter on Pi-hole network table) | int in config + options flow | Default 30; clients with no DNS query in N days skipped (DHCP-lease clients always included); otherwise all |
| marq24/ha-bosch-ebike-flow (bosch_ebike) | N/A | One GPS TrackerEntity for the bike | - | Own device only |
| mudape/iphonedetect (iphonedetect) | N/A-single-target | One config entry per iPhone (`name`, `ip_address`) | Text in config flow / reconfigure | Config entry IS the selection |
| nielstron/inteno_hass (inteno) | C | Options only `scan_interval`, `detection_time` | - | Every client gets a tracker; registry trackers restored |
| p0l0/hapetwalk (petwalk) | N/A | One ROUTER-source TrackerEntity per pet known to the PetWALK door | - | Pets, not network clients |
| pajew-ski/ha-speedport (speedport) | C | Options only `pause_time` | - | Tracker per device the router reports at setup |
| ruaan-deysel/ha-unifi-insights (unifi_insights) | B | `track_wifi_clients`, `track_wired_clients` (legacy `track_clients` migrated) | bool, options flow | Default False/False = no trackers; wired/wireless category only; trackers for deselected category removed on reload |
| sHedC/homeassistant-leakbot (leakbot) | N/A | ScannerEntity (source `"detector"`) per Leakbot device | - | Own devices only |
| schmidtfx/swisscom-internetbox-hass (swisscom_internetbox) | C | Options only `consider_home` | - | Every client with a MAC gets a tracker |
| shaiu/technicolor (technicolor) | C | Dead `CONFIG_SCHEMA` in device_tracker.py with `devices`/`exclude` lists, never read | - | Every router client gets a tracker |
| theoabw/ha-openwrt-presence (openwrt_presence) | B | `enable_new_trackers` | BooleanSelector, options flow | Default False -> new trackers created disabled (entity_registry_enabled_default); all clients still get entities |
| tomaae/homeassistant-mikrotik_router (mikrotik_router) | B | `track_network_hosts` (+ `track_network_hosts_timeout`) | bool, options flow | Default False = no host trackers; on = all hosts |
| travisghansen/hass-pfsense (pfsense) | **A** (allow-list) | `device_tracker_enabled` + `devices` | bool + `cv.multi_select` of ARP-table entries (labels "mac - host (ip)"), options flow | Default disabled; empty list = no trackers (per-ARP mode hard-coded off); deselected MACs' devices removed |
| usersaynoso/ha-cudy-router (cudy_router) | **A** (allow-list) | `tracked_device_macs` + `auto_add_device_trackers` (also `auto_add_connected_devices` / `device_list` shaping the picker) | SelectSelector(multiple, dropdown) of connected/known clients; BooleanSelector; options flow | Auto off by default = only picked clients tracked; auto on = all connected + picked; stale trackers cleaned up |
| vithurshanselvarajah/ha-glinet (glinet_router) | **A** (allow- or deny-list, unknown devices only) | `add_all_devices`, `unknown_devices_filter_mode` (blacklist/whitelist), `unknown_devices_filter_select`, `unknown_devices_filter_manual`; also `cleanup_devices` | bool; SelectSelector dropdown; SelectSelector(multiple) of discovered clients; multiline text of MACs; config + options flow | Default: only "known" clients (MAC already a device of another config entry) tracked; with `add_all_devices` unknown clients tracked minus blacklist / only whitelist; disallowed unknown entities removed |
| vmakeev/huawei_mesh_router (huawei_mesh_router) | B | `device_tracker` (platform on/off), `device_tracker_zones` | bool, options flow (features step) | Default False for new entries (True for migrated v1 entries); on = every connected client |

## Sanity sweep: router/network-client trackers not using "ScannerEntity"/"SourceType.ROUTER"

Swept every `custom_components/**/device_tracker*.py` lacking both strings, plus all
`get_scanner`/`setup_scanner`/`DeviceScanner` definitions and `see` service usage anywhere.
New network-client scanners (not in the excluded owner list):

| Integration | Bucket | Mechanism / keys | UI type | Default / semantics |
|---|---|---|---|---|
| PaulAnnekov/home-assistant-padavan-tracker (padavan_tracker) | B (+FW) | Legacy `get_scanner`; `rssi` minimum in PLATFORM_SCHEMA | YAML | Unset = all wireless clients; set = drop clients below RSSI |
| ayavilevich/homeassistant-dlink-presence (dlink_presence) | B (+FW) | Legacy `async_get_scanner`; `require_ip` | YAML bool | Default False = all clients; True = only clients with an IP |
| kevinhaendel/ha-ubee (ubee) | C (+FW) | Legacy `get_scanner`; only host/creds/model | YAML | All clients; only FW `track`/`track_new_devices` |
| luis-garza/movistar_rft8115vw (movistar_rft8115vw) | C (+FW) | Legacy `get_scanner`; only host/password | YAML | All clients; only FW mechanisms |

Hits that are not network-client scanners (N/A, listed for completeness): Danielhiversen/home_assistant_tractive (tractive_custom, GPS pets), WulfgarW/homeassistant-pycupra (pycupra, car GPS), gcobb321/icloud3 (icloud3, phone GPS), robinostlund/homeassistant-volkswagencarnet (volkswagencarnet, car GPS), tom-winkler/ha-webfleet-integration (webfleet, fleet GPS), bramkragten/mind (mind, car GPS), jesserockz/ha-leafspy (leafspy, car GPS), twrecked/hass-virtual (virtual, user-defined virtual trackers), andreadegiovine/homeassistant-stellantis-vehicles, gorfo66/flashbird-homeassistant, kayloehmann/ha-gardena-smart-system, moehrem/DiveraControl (vehicles/mowers/units via other modules), RogerSelwyn/mqtt_discoverystream_ha (re-publishes existing entities). Already-assigned: juacas/zte_tracker legacy module, shaiu/technicolor, juacas/honor_x3, Csontikka mikrotik_extended types file, tomaae mikrotik types file.

## Per-integration notes

### juacas/zte_tracker (zte_tracker) - B
- `const.py:18` `CONF_REGISTER_NEW_DEVICES = "register_new_devices"`; `coordinator.py:79` reads it from `entry.options` (default True).
- Not in config/options flow (`config_flow.py:82-98`, `:255-290` only host/creds/model/query/session/mesh flags). It is toggled by `switch.py:67-120` `ZteRegisterNewDevicesSwitch`, which persists the value into entry.options.
- `device_tracker.py:57,86-94`: when off, new MACs are skipped unless already in the entity registry; registry entries are always recreated (`:101-152`). So "off" freezes the current tracker set - a de facto allow-list only in combination with manual deletion.
- `services.yaml` `remove_tracked_entity` (free-text MAC) removes a tracker + orphaned device (`__init__.py:259-320`); `remove_unidentified_entities` too. No per-device selection setting.
- `legacy_device_tracker.py`: legacy `get_scanner` kept for back-compat; returns the shared scanner only; FW mechanisms only.

### lrehmann/pihole_presence (pihole_presence) - B (weak)
- `const.py:9,15` `stale_device_days` default 30; `config_flow.py:41-44` (same schema in config and options flow).
- `coordinator.py:465,500`: Pi-hole network-table entries whose last DNS query is older than the cutoff are skipped; DHCP-lease entries (`:468-480`) are always merged in. TrackerEntity with `SourceType.ROUTER` (`device_tracker.py:104-106`). No removal of trackers that go stale (known_macs only grows).

### marq24/ha-bosch-ebike-flow (bosch_ebike) - N/A
- `device_tracker.py:22-30` one tracker for the bike; `source_type` GPS (ROUTER commented out).

### mudape/iphonedetect (iphonedetect) - N/A-single-target
- `config_flow.py:38-44` `name` + `ip_address` (+ `subnet_check`); unique id per name; `device_tracker.py:30-42` one `BaseScannerEntity` (ROUTER) per entry.

### nielstron/inteno_hass (inteno) - C
- Options (`config_flow.py:135-149`): `scan_interval`, `detection_time` only. `device_tracker.py:59-70` adds a tracker for every `coordinator.api.devices` MAC; registry entries restored (`:36-45`).

### p0l0/hapetwalk (petwalk) - N/A
- `device_tracker.py:23-62` one tracker per pet (skips unknown/unnamed pets), source ROUTER but not network clients.

### pajew-ski/ha-speedport (speedport) - C
- Options: `pause_time` only (`config_flow.py:102-119`). `device_tracker.py:22-31` one tracker per `speedport.devices` at setup.

### ruaan-deysel/ha-unifi-insights (unifi_insights) - B
- `const.py:17-23` `track_clients` (deprecated), `track_wifi_clients`, `track_wired_clients`, all default False.
- `config_flow.py:603-642` options flow: two bools (plus `client_control`).
- `device_tracker.py:39-75` per-client filter by wired/wireless type (unknown type tracked if either on), only currently connected clients; `:94-115` removes registry trackers not in the wanted set; no trackers when both off. Options update reloads entry (`__init__.py:328,372-376`).

### sHedC/homeassistant-leakbot (leakbot) - N/A
- `device_tracker.py:15-50` ScannerEntity per Leakbot device, source `"detector"`, `is_connected` always True. Own devices.

### schmidtfx/swisscom-internetbox-hass (swisscom_internetbox) - C
- Options: `consider_home` only (`config_flow.py:60-75`). `device_tracker.py:23-41` tracker for every device with a MAC.

### shaiu/technicolor (technicolor) - C
- `device_tracker.py:27-40` defines `CONFIG_SCHEMA` with `devices` / `exclude` string lists, but it is in the platform module (never used as the integration schema) and the keys are never read; `__init__.py:14-35` imports YAML host/creds only (`yaml_options = {}`). `device_tracker.py:64-78` adds a tracker for every router device. Config flow (`config_flow.py:39-46`) host/user/password only.

### theoabw/ha-openwrt-presence (openwrt_presence) - B
- `config_flow.py:44` `CONF_ENABLE_NEW_TRACKERS = "enable_new_trackers"`; options flow `:262-283` BooleanSelector, default False.
- `device_tracker.py:129-131` `entity_registry_enabled_default` returns the option -> by default new trackers are created disabled (counts as "new devices disabled by default" B per rubric). All clients still get registry entries (`:17-38`).

### tomaae/homeassistant-mikrotik_router (mikrotik_router) - B
- `const.py:32-35` `track_network_hosts` (default False), `track_network_hosts_timeout` (180). Options flow `config_flow.py:209-211,245-247`; labels "Track network devices" in strings.json.
- `entity.py:82-87` `_skip_sensor` skips all `MikrotikHostDeviceTracker` when off; `device_tracker.py:185-196` is_connected False when off. `track_iface_clients` only adds MAC/IP attributes to interfaces (`coordinator.py:950-955`), not trackers. Entry reloads on options change (`__init__.py:41-51`); no explicit removal of existing host trackers when turned off.

### travisghansen/hass-pfsense (pfsense) - A (allow-list)
- `const.py:38-39` `device_tracker_enabled` (default False), `:47` `devices`.
- `config_flow.py:197-235` options init (enable + scan interval + consider_home), then `:237-281` `async_step_device_tracker`: `cv.multi_select` of live ARP-table entries (labels `mac - hostname (ip)`, previously selected kept at top).
- `device_tracker.py:85-101` only configured MACs get trackers (`device_per_arp_entry = False` hard-coded, so empty = none; comment "seems unlikely *all* devices are intended to be monitored"). `:119-131` devices for MACs removed from the list are deleted from the device registry; tracked list persisted as `tracked_macs` in entry.data.

### usersaynoso/ha-cudy-router (cudy_router) - A (allow-list)
- `const.py:33-36` `device_list`, `auto_add_connected_devices`, `auto_add_device_trackers`, `tracked_device_macs`. Initial entry sets `auto_add_device_trackers=False`, `tracked_device_macs=[]` (`config_flow.py:155-156`).
- Options: `config_flow.py:350-351` BooleanSelectors; `:454-517` `trackers` step SelectSelector(multiple, dropdown) of eligible clients (connected clients, or the manual `device_list` selection when auto-add of connected devices is off); step skipped when auto-add trackers is on.
- `device_tracking.py:249-268` `tracker_allowed_macs`: picked MACs, plus all connected when `auto_add_device_trackers`. `device_tracker.py:63-95` builds trackers only for allowed MACs and calls `async_cleanup_stale_tracker_entities` to remove deselected ones. Strings: "Select specific connected clients that should always keep a device_tracker entity".

### vithurshanselvarajah/ha-glinet (glinet_router) - A (allow- or deny-list, unknown devices only)
- Tracker code in `entities/device_tracker.py` (re-exported by `device_tracker.py`); creates trackers for `hub.tracked_devices`.
- `const.py:10-15` keys; `config_flow.py:189-236` (shared config/options schema): `add_all_devices` bool default False, `cleanup_devices` minutes, `unknown_devices_filter_mode` dropdown blacklist/whitelist, `unknown_devices_filter_select` SelectSelector(multiple) of discovered clients (only when discovered), `unknown_devices_filter_manual` multiline MACs.
- `hub.py:993-1000`: a client whose MAC is already a device of another config entry is "known" and always tracked (cannot be excluded); otherwise `hub.py:1828-1836` `_unknown_device_allowed`: requires `add_all_devices`, then whitelist = only listed, blacklist = all but listed. `hub.py:360-372` removes entities/devices of disallowed unknown clients; `:1016+` optional stale cleanup after N minutes disconnected.

### vmakeev/huawei_mesh_router (huawei_mesh_router) - B
- `const.py:20-21,36-37` `device_tracker`, `device_tracker_zones` (default False); options flow features step `config_flow.py:226-237`. `__init__.py:52-53` excludes the device_tracker platform when off; v1->v2 migration sets True (`:155-161`). `device_tracker.py:49-63` tracker per connected client when on. `device_tracker_zones` only changes state to router-specific zones.

### Sweep: PaulAnnekov/home-assistant-padavan-tracker (padavan_tracker) - B (+FW)
- `device_tracker.py:16-21` PLATFORM_SCHEMA `url`, `username`, `password`, optional `rssi` (-200..0); `:24-28` legacy `get_scanner`; `scan_devices` drops clients with RSSI below the threshold (`:123`). Signal-strength filter only.

### Sweep: ayavilevich/homeassistant-dlink-presence (dlink_presence) - B (+FW)
- `device_tracker.py:21-33` PLATFORM_SCHEMA adds `require_ip` (default False); `:41-45` `async_get_scanner`; `dlink_telnet.py:311` keeps only clients with an IP when set. No per-device choice.

### Sweep: kevinhaendel/ha-ubee (ubee) - C (+FW)
- `device_tracker.py:21-30` PLATFORM_SCHEMA host/creds/model; `:41-` `get_scanner`; `scan_devices` returns all. Only FW mechanisms.

### Sweep: luis-garza/movistar_rft8115vw (movistar_rft8115vw) - C (+FW)
- `device_tracker.py:20-21` PLATFORM_SCHEMA host/password; `:25` `get_scanner`; `scan_devices` returns all. Only FW mechanisms.
