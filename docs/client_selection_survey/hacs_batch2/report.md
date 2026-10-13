# HACS batch 2: user-selectable device-tracker client selection

Rubric: `../rubric.md`.
Paths below are relative to each integration's `custom_components/<domain>/` dir under
`<local clone of HACS integrations>/`.

| Integration | Bucket | Mechanism / keys | UI type | Default / semantics |
|---|---|---|---|---|
| al-one/hass-xiaomi-miot (xiaomi_miot) | N/A | `scanner_properties` device customization exposes a device's own property (e.g. `online_status`) as a ROUTER ScannerEntity; other trackers are GPS (watches) | - | Tracks the integration's own Xiaomi devices only |
| amosyuen/ha-tplink-deco (tplink_deco) | C | Only `client_prefix`/`client_postfix` (naming) | - | Every client in coordinator data gets a tracker |
| benleb/sureha (sureha) | N/A | Pet trackers (source `flap`) | - | One tracker per pet, not network clients |
| brewmarsh/meraki-homeassistant (meraki_ha) | B | `enable_device_tracker` (bool), `enabled_networks` (network multi-select), `ignored_networks`; hard-coded skip of randomized MACs | BooleanSelector + SelectSelector(multiple) | Default on, all networks; filter is per network, not per client |
| bullitt186/ha-omada-open-api (omada_open_api) | **A** (allow-list) | `selected_clients` option (+ `ssid_filter` pre-filter of the picker) | SelectSelector(multiple) of discovered clients, config + options flow | Empty = no client trackers (opt-in); deselected client devices removed |
| cataseven/Keenetic-Router-Pro (keenetic_router_pro) | **A** (allow-list) | `tracked_clients` in entry.data | `cv.multi_select` of discovered clients, config + options flow | Empty = no trackers; no explicit cleanup of deselected found |
| corgan2222/ha-better-presence2 (better_presence) | N/A | Per-person aggregate TrackerEntity built from existing HA trackers | - | Not a network scanner |
| custom-components/ble_monitor (ble_monitor) | N/A (BLE; effectively per-device allow-list) | per-device `track_device` in `devices` list | YAML + options flow (free-text MAC/UUID + bool) | Default False; only listed+flagged BLE MACs/UUIDs tracked |
| cyberjunky/home-assistant-arpscan_tracker (arpscan_tracker) | **A** (allow + deny) | `include`, `exclude` (IPs), `hosts` (probe-only IPs); also `track_new_devices`, `devices_enabled` | Free-text comma-separated IPs, config + options flow | Empty = all; include wins over exclude; existing registry trackers still restored |
| djchen/ha-unifi-presence (unifi_presence) | **A** (allow-list) | `tracked_devices` option | SelectSelector(multiple, custom_value=False) of discovered clients, config + options flow | Must be non-empty; only selected tracked; deselected entities removed |
| dmamontov/hass-miwifi (miwifi) | B | `is_track_devices` (bool) | cv.boolean, config + options flow | Default True = all clients |
| dscao/ikuai (ikuai) | **A** (allow-list, picked via include- or exclude-mode) | `tracker_config` (entry.data), `source_mode` (UI vs const.py) | `cv.multi_select` of online IPs/MACs with include/exclude mode, plus free-text custom add; delete step | Only configured targets tracked; nothing tracked by default |
| elad-bar/ha-edgeos (edgeos) | **A** (allow-list, via entity) | Per-device "Monitored" CONFIG switch (`EntityKeys.DEVICE_MONITORED`), stored in `monitored-devices` storage | Switch entity per DHCP device (no flow) | Default not monitored = no tracker; toggle removes/re-creates entities |
| hiall-fyi/tado_ce (tado_ce) | N/A | Tado mobile devices with `geoTrackingEnabled` (ROUTER source TrackerEntity) | - | Cloud phone presence; selection is in Tado app |
| johnnyh1975/ha_roomba_plus (roomba_plus) | N/A | Robot's own current-room TrackerEntity | - | Own device only |
| juacas/honor_x3 (honor_x3) | C | Legacy `DeviceScanner`; no integration-specific schema | - | Reports all active DHCP clients; only generic legacy known_devices.yaml `track`/`track_new_devices` apply |

## Per-integration notes

### al-one/hass-xiaomi-miot (xiaomi_miot) - N/A
- `device_tracker.py:65-89` defines a ROUTER `ScannerEntity` used only via `XEntity.CLS['scanner']`; `core/device.py:452-470` maps a device's `scanner_properties` customization to `device_tracker` (e.g. `core/device_customizes.py:161` `ainice.sensor_occupy.bt` -> `online_status`). Other trackers (`MiotTrackerEntity`, `XiaoxunWatchTrackerEntity`) are GPS. Tracks the integration's own devices, not network clients.

### amosyuen/ha-tplink-deco (tplink_deco) - C
- `device_tracker.py:117-175` `_async_setup_clients` adds a `TplinkDecoClientDeviceTracker` for every MAC in client coordinator data. Config keys (`config_flow.py:85-130`, `const.py:40-43`) are only host/creds/intervals and name prefix/postfix. No removal of departed clients.

### benleb/sureha (sureha) - N/A
- `device_tracker.py:21-33`: one `SureDeviceTracker` per pet (`EntityType.PET`), source type `flap`. Not a network scanner.

### brewmarsh/meraki-homeassistant (meraki_ha) - B
- `const/config.py:19,22,31`: `ignored_networks`, `enabled_networks`, `enable_device_tracker` (default True, `:34`).
- `schemas.py:87-97` setup-flow `enabled_networks` SelectSelector(multiple) of org networks; `schemas.py:118-134` options: `enabled_networks` (multi, custom_value) and `enable_device_tracker` BooleanSelector.
- `discovery/handlers/network.py:227-243`: tracker creation gated on `enable_device_tracker`; per-network client iteration; locally-administered (randomized) MACs skipped unconditionally. Networks filtered at `discovery/coordinator.py:47-52`; `ignored_networks` filtered in `core/coordinator_helpers/update_processor.py:169-173`.
- Semantics: empty enabled_networks = all networks. No per-client choice.

### bullitt186/ha-omada-open-api (omada_open_api) - A (allow-list, UI picker of discovered clients)
- `const.py:17` `selected_clients`, `:19` `ssid_filter`.
- Config flow: `config_flow.py:684` `ssid_filter` step (SelectSelector of SSIDs that only pre-filters the client list; wired always shown), `:763-769` `selected_clients` SelectSelector(multiple, dropdown) labelled with online state/name/IP/MAC. Options flow: `:1971-1980` same pair.
- `__init__.py:571-597`: client coordinators created only for `selected_client_macs`; empty = no client trackers (opt-in). Infrastructure device trackers (APs/switches/gateways, `device_tracker.py:49-64`) are always created.
- Removal: `__init__.py:896-920` removes device-registry devices of deselected clients on options update.

### cataseven/Keenetic-Router-Pro (keenetic_router_pro) - A (allow-list, UI picker)
- `const.py:63` `tracked_clients`, stored in `entry.data` as list of `{mac, ip, name}`.
- Config flow `async_step_select_clients` `config_flow.py:266-322` (`cv.multi_select` of discovered clients); options `async_step_init` `:570-716` rewrites `entry.data[tracked_clients]` (`:612`), default = current MACs.
- `device_tracker.py:37-40`: no trackers if list empty; one `KeeneticClientTracker` per entry. No explicit entity/device cleanup for deselected clients found (entry reloads; stale registry entries likely linger).

### corgan2222/ha-better-presence2 (better_presence) - N/A
- `device_tracker.py:18-61`: one `BetterPresenceEntity` per configured person (`const.py:9-14` `persons`/`devices` are existing HA entities); source mirrors the underlying tracker. Aggregator, not a network scanner.

### custom-components/ble_monitor (ble_monitor) - N/A (BLE, but per-device allow-list)
- `const.py:45` `track_device`, default False (`const.py:76`). Per-device in the `devices` list: YAML (`__init__.py:73`) and options-flow device step (`config_flow.py:66,219,307`; free-text MAC/UUID + boolean).
- `__init__.py:571-576` builds `tracker_whitelist` only from devices with `track_device: true`; `device_tracker.py:92-96` restores those. Source type BLUETOOTH_LE. If BLE scanners were in scope this would be A (allow-list, free-text).

### cyberjunky/home-assistant-arpscan_tracker (arpscan_tracker) - A (allow + deny, free-text IPs)
- `const.py:13-17`: `include`, `exclude`, `hosts`, `devices_enabled`, `track_new_devices` (both default True, `:25-26`).
- Config flow `config_flow.py:190-194`, options `:347-367`: booleans + plain `str` fields parsed as comma-separated IP lists.
- Applied in coordinator processing `__init__.py:129-137`: if `include` non-empty only those IPs; else `exclude` drops listed IPs. `hosts` (`__init__.py:91,108`) makes the scanner probe only those IPs (VPN use case). Empty = all.
- B-style extras: `track_new_devices` False stops creating new entities (`device_tracker.py:131-133`); `devices_enabled` False creates them disabled.
- Removal: `device_tracker.py:81-125` restores every registry entry for the entry regardless of filters, so trackers for newly excluded IPs persist (just no updates).

### djchen/ha-unifi-presence (unifi_presence) - A (allow-list, UI picker)
- `const.py:13` `tracked_devices` (stored in options).
- Selector `config_flow.py:101-110`: SelectSelector(multiple, custom_value=False) of discovered UniFi clients. Setup step `:608-642` (error `no_devices` if empty), options `:681-712` (error `no_tracked_devices` if empty).
- `device_tracker.py:28`: one tracker per tracked MAC.
- Removal: `config_flow.py:145-160,692-693` removes entity-registry entries for deselected MACs.

### dmamontov/hass-miwifi (miwifi) - B
- `const.py:44` `is_track_devices`; `config_flow.py:142,230` (config), `:346-349` (options), cv.boolean default True.
- `device_tracker.py:101-105`: new devices skipped if disabled. Also `activity_days` (`config_flow.py:364`) governs purge of inactive devices, not selection. No per-client choice.

### dscao/ikuai (ikuai) - A (allow-list; picked via include or exclude mode)
- `const.py:15-18` `tracker_config`, `source_mode` (`mode_ui` / `mode_const`).
- `config_flow.py:221-225` `scan_add`: `ip_filter_mode`/`mac_filter_mode` (include|exclude SelectSelector) + `cv.multi_select` of currently online IPs/MACs; exclude-mode adds all other online hosts. `async_step_custom_add` (`:266-378`) accepts free-text IPs/IP ranges/MACs; `manage_devices` sets names/buffers; options flow (`:480+`) offers scan_add/custom_add/delete_devices.
- `mode_const` reads a hand-edited `DEVICE_TRACKERS` dict in `const.py` (`device_tracker.py:21-36`).
- `device_tracker.py:38-43`: trackers only for configured targets; nothing by default. Deleting a target in options removes it from config; entity cleanup not verified.

### elad-bar/ha-edgeos (edgeos) - A (allow-list via per-device CONFIG switch, not a flow)
- `common/entity_descriptions.py:282-290`: device tracker has `EntityValidation.MONITORED`; a `DEVICE_MONITORED` switch (EntityCategory.CONFIG) exists per device.
- `managers/config_manager.py:237-240`: `monitored-devices` storage, default False -> no tracker until the user turns the switch on.
- `managers/coordinator.py:822-835`: toggling sets the flag and removes/re-creates the device's entities. Devices come from DHCP static mappings + leases (`data_processors/device_processor.py:109-164`).

### hiall-fyi/tado_ce (tado_ce) - N/A
- `device_tracker.py:36-65`: trackers for Tado mobile devices with `geoTrackingEnabled` (selection lives in the Tado app); ROUTER source type only because it's a binary atHome flag. Option `mobile_devices_enabled` (`config_flow_options.py:220`) controls polling. Not network clients.

### johnnyh1975/ha_roomba_plus (roomba_plus) - N/A
- `device_tracker.py:64-76`: one current-room TrackerEntity for the robot itself, always created.

### juacas/honor_x3 (honor_x3) - C
- `device_tracker.py:19-24` legacy `get_scanner`; `scan_devices` returns MACs of all active DHCP clients. No PLATFORM_SCHEMA; `__init__.py:12-18` CONFIG_SCHEMA only username/password. Only the generic legacy `known_devices.yaml` `track:` flag and `new_device_defaults.track_new_devices` apply (core, not integration-specific).

## Buckets
- **A**: omada_open_api, keenetic_router_pro, arpscan_tracker, unifi_presence, ikuai, edgeos
- **B**: meraki_ha, miwifi
- **C**: tplink_deco, honor_x3
- **N/A**: xiaomi_miot, sureha, better_presence, ble_monitor (BLE; would be A), tado_ce, roomba_plus
