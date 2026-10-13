
Two judgement calls you may want to change: wifi_sensor_tracker and bermuda are in A because they let the user pick specific devices, but neither tracks router clients (one uses HA Wi-Fi sensors, the other BLE). If only router clients count, move both to N/A.

**Bucket A (pick specific clients):**
- **asusrouter:** pick from a list of discovered clients, as either an include list or an exclude list.
- **ha_keenetic:** pick from a list of discovered clients, plus an "all clients" switch. Nothing is tracked by default.
- **FaserF openwrt:** pick from a list of discovered clients, plus a free-text MAC list. Empty means track all.
- **openwrt_ubus:** free-text list of MAC/IP prefixes, separately for wireless and wired. Empty means track all.
- **technitiumdns:** free-text list of IPs, subnets or ranges, as an include list or an exclude list. Matches by IP, not MAC.
- **wifi_sensor_tracker (caveat):** the user picks which Wi-Fi SSID sensors become trackers.
- **bermuda (caveat):** the user picks which discovered Bluetooth devices get trackers. Nothing is tracked by default.

**Bucket B (on/off or category filters only):**
- **mikrotik_extended:** one switch to track all network hosts, off by default.
- **livebox:** separate wireless and wired switches, plus "All" vs "Active only".

---

# HACS batch 1: user-selectable device tracker client selection

Rubric: `../rubric.md`. Paths relative to `<local clone of HACS integrations>/<owner>/<repo>/custom_components/<domain>/`.

| Integration | Bucket | Keys (location) | Selector / kind | Default / semantics |
|---|---|---|---|---|
| 5a2v0/HA-WiFi-Sensor-Tracker (wifi_sensor_tracker) | A (caveat: the source is HA Wi-Fi SSID sensor entities, not router clients) | `sensors` (config_flow.py:87-98 user, :254-265 options) | Entity selector, `multiple`, limited to discovered `*_wifi_connection`/`*_ssid` sensors; allow-list | Required and non-empty. Only the selected sensors get a ScannerEntity (ROUTER). |
| AldenDana/ha-zte-fibra (zte_fibra_tracker) | C | options only `scan_interval` (config_flow.py:73-87) | none | Every MAC from the router gets a tracker (device_tracker.py:27-38). |
| AlexandrErohin/home-assistant-tplink-router (tplink_router) | C | config/options: host/user/pass/scan_interval/verify_ssl only (config_flow.py:26-31, 110-116) | none | Every client gets a tracker; registry entries are restored (device_tracker.py:36-52). |
| Amateur-God/home-assistant-technitiumdns (technitiumdns) | A (allow- or deny-list) | `enable_dhcp_tracking`, `dhcp_ip_filter_mode` {disabled, include, exclude}, `dhcp_ip_ranges` (const.py:27-38; config_flow.py:141-161; utils.py:130-160; device_tracker.py:213) | Free text: IPs, CIDRs, `a-b` ranges (comma/semicolon/newline), plus a mode dropdown | Tracking is off by default. With the filter mode `disabled` or empty ranges, every DHCP lease is tracked. |
| Csontikka/ha-mikrotik-extended (mikrotik_extended) | B | `track_network_hosts` (const.py:44-45; config_flow.py:463 setup `sensor_select`, :723 options), `track_network_hosts_timeout` | Boolean | Default False. When True, every ARP/DHCP/wireless host is tracked (entity.py:107-117). |
| Cyr-ius/hass-livebox-component (livebox) | B | `wifi_tracking` (default True), `lan_tracking` (default False), `device_tracker_mode` "All"/"Active only" (const.py:25-34; config_flow.py:196-209; coordinator.py:150-213) | Booleans plus a dropdown | These are wired/wireless category and active-only filters. There is no per-device choice. |
| DECTYR/ha-integration (dectyr_rx5) | N/A | none | none | GPS TrackerEntity for drone-detector scanners, drones and operators. Not network clients. |
| DSorlov/http_agent (http_agent) | N/A-single-target | per-sensor `tracker_latitude`/`tracker_longitude`/... (config_flow.py:239-265) | Templates the user defines | A generic HTTP scraper. Each tracker is defined by hand, so there is no client discovery. |
| FUjr/homeassistant-openwrt-ubus (openwrt_ubus) | A (allow-list) | `enable_wireless_trackers`, `wireless_tracker_whitelist`, `enable_wired_tracker`, `wired_tracker_whitelist`, `wired_tracker_interfaces` (const.py:36-42, 80-85; config_flow.py:446-458, 490-497, 710-736; device_tracker.py:216-277; shared_data_manager.py:669-674) | Free text, comma-separated IP/MAC prefixes (prefix match) and interface names | Both enables default False. An empty whitelist tracks all clients. |
| FaserF/ha-openwrt (openwrt) | A (allow-list) | `tracked_devices`, `manual_tracked_devices`, plus `track_devices`, `track_wired`, `skip_random_mac` (const.py:24-29, 71-75; config_flow.py:1920-1985 setup `selective_tracking`, 2345-2430 options `options_select_devices`; coordinator.py:1250-1348, 1547-1564) | UI multi-select of discovered clients (SelectSelector) plus a multiline free-text MAC list | The two lists are merged. An empty merged list means no whitelist, so all clients are tracked. `track_devices` and `track_wired` default True. |
| FehTeh/ha-custom-component-growappy (growappy) | N/A | username/password only | none | One cloud-API "student presence" tracker per student on the account. Not network clients. |
| HarvsG/ha-glinet4-integration (glinet) | C | username/host/password/`consider_home` (config_flow.py:49-64; options reuse the same schema) | none | Every client gets a tracker (device_tracker.py:46-60). |
| Kajkac/ZTE-MC-Home-assistant-repo (zte_router) | C | No tracker options (config_flow.py:106-118, 168-182) | none | Every WiFi or wired MAC gets a tracker (device_tracker.py:20-49). |
| Vaskivskyi/ha-asusrouter (asusrouter) | A (both: include or exclude) | `track_devices`, `client_filter` {no_filter, include, exclude}, `client_filter_list` (const.py:469-471, 506, 513-514, 537, 543-547; config_flow.py:456-487, 1050-1073; router.py:332-337, 434-449, 605-617; device_tracker.py:36-45) | `cv.multi_select` of discovered clients (MAC to name) plus a mode dropdown | Defaults are `no_filter` (all clients) and `track_devices` True. |
| agittins/bermuda (bermuda) | A (caveat: BLE, not IP clients) | `configured_devices` (const.py:158; config_flow.py:~240-322 `selectdevices`; coordinator.py:698, 1072) | SelectSelector, multiple, of discovered BLE devices, iBeacons and random MACs; allow-list | Opt-in: empty means no trackers, except Private BLE / IRK devices, which are added automatically. BLUETOOTH_LE BaseScannerEntity. |
| akinin/ha_keenetic (ha_keenetic) | A (allow-list) | `create_device_tracker` (all clients), `create_select_device_tracker` (const.py:24-25; config_flow.py:376-388 options `configure_clients`; device_tracker.py:38) | `cv.multi_select` of discovered hotspot clients plus an "all" boolean | Both default off, so no trackers. Trackers are created if the MAC is selected or "all" is on. |

## Per-integration notes

### 5a2v0/HA-WiFi-Sensor-Tracker (wifi_sensor_tracker) — A (caveat)
- Trackers are derived from companion-app SSID sensors that already exist in HA. The user picks which of these sensor entities become `ScannerEntity` (SourceType.ROUTER) trackers. The selection lives in config-entry data and can be edited in the options flow.
- An empty selection is rejected (`no_sensors`), so this is strictly an allow-list.
- Removal: deselecting a sensor removes its `device_tracker` from the entity registry (config_flow.py:325-331), followed by a soft reload.
- It is not a router or network-client scanner. It is bucketed A because it is a per-device allow-list; re-bucket it as N/A if only router clients count.

### AldenDana/ha-zte-fibra (zte_fibra_tracker) — C
- The options flow only has `scan_interval`. Every MAC the router reports gets a tracker. There is no removal.

### AlexandrErohin/home-assistant-tplink-router (tplink_router) — C
- There are no tracking options. Trackers are added for every client and restored from the registry after a restart. There is no removal.

### Amateur-God/home-assistant-technitiumdns (technitiumdns) — A (allow-list or deny-list, free-text IP)
- `enable_dhcp_tracking` (default False) is the global switch.
- `dhcp_ip_filter_mode` (`disabled` by default) together with `dhcp_ip_ranges` (free text: single IPs, CIDRs, `a-b` ranges) acts as an IP allow-list (include) or deny-list (exclude). The filter applies to DHCP leases in the coordinator via `should_track_ip`.
- Matching is by IP, not MAC. The UI is a plain text box, not a selector of discovered clients.
- Removal: `async_cleanup_orphaned_entities` (__init__.py:460+) only logs orphans. Entities of filtered-out clients become unavailable and stay in the registry. Trackers are created only once at platform setup from the first refresh.

### Csontikka/ha-mikrotik-extended (mikrotik_extended) — B
- `track_network_hosts` (default False) is shown during setup and in the options flow. When True, every host gets a tracker. Container endpoints are skipped by code; there is no user setting for that.
- `track_iface_clients` exists in const but is effectively hard-coded to True.
- Removal: on setup, enabled `device_tracker` registry entries that are no longer provided are removed (device_tracker.py:106-115).

### Cyr-ius/hass-livebox-component (livebox) — B
- `wifi_tracking` (default True) and `lan_tracking` (default False) are wired/wireless category filters. Ethernet repeaters are still kept for topology.
- `device_tracker_mode` "All" vs "Active only" (const default "Active", which is not one of the `vol.In` values; any non-"All" value means active-only).
- There is no per-device choice and no removal of trackers.

### DECTYR/ha-integration (dectyr_rx5) — N/A
- `TrackerEntity` with GPS positions for RX5 scanners, detected drones and their operators. Not network clients.

### DSorlov/http_agent (http_agent) — N/A-single-target
- The user defines each "device_tracker" sensor by hand: lat/lon/location templates and a source type. The configuration itself is the selection.

### FUjr/homeassistant-openwrt-ubus (openwrt_ubus) — A (allow-list, free text)
- Wireless: `enable_wireless_trackers` (default False) plus `wireless_tracker_whitelist`. The whitelist is comma-separated free text, matched as a case-insensitive MAC prefix or an IP prefix, so it can name exact MACs or whole subnets.
- Wired: `enable_wired_tracker` (default False), `wired_tracker_whitelist` (same format) and `wired_tracker_interfaces` (interface filter, a coarse control). The integration logs a warning if wired tracking is on with no filters.
- An empty whitelist tracks all clients.
- `selected_sta` / `select_all_sta` select STA *sensors*, not trackers.
- Removal: none seen. Registry entries are kept and restored.

### FaserF/ha-openwrt (openwrt) — A (allow-list, UI selector plus free-text MAC)
- `tracked_devices`: SelectSelector multi-select of discovered clients, with labels from DHCP leases, history and a shared hostname registry. It is offered at setup (`selective_tracking`) and in options (`options_select_devices`).
- `manual_tracked_devices`: multiline text with one MAC per line.
- The two lists are merged into a whitelist (coordinator.py:1547-1564). If the merged list is empty there is no whitelist and all clients are tracked.
- Coarse controls: `track_devices` (default True), `track_wired` (default True) and `skip_random_mac` (default True).
- Removal: `_async_cleanup_entities` (device_tracker.py:62-108) removes trackers when `track_devices` is off, MQTT presence is on, wired tracking is turned off for wired MACs, or the MAC is the router's own or an interface name. It does NOT remove trackers for clients dropped from the whitelist.

### FehTeh/ha-custom-component-growappy (growappy) — N/A
- A cloud school app. There is one `TrackerEntity` per student on the account (ROUTER source type, but not network clients) and no selection.

### HarvsG/ha-glinet4-integration (glinet) — C
- Config and options cover only credentials, host and `consider_home`. Every client gets a tracker.

### Kajkac/ZTE-MC-Home-assistant-repo (zte_router) — C
- There are no tracker-related options. Every MAC seen gets a tracker. There is no removal.

### Vaskivskyi/ha-asusrouter (asusrouter) — A (both include and exclude, UI multi-select)
- `client_filter` (`no_filter` default, `include`, `exclude`) together with `client_filter_list` (`cv.multi_select` of discovered clients; saved MACs that are not currently present stay listed). It is in the options step `connected_devices`.
- `track_devices` (default True) is the global switch. If False, the platform sets up nothing.
- The filter is applied to `_clients` at setup, including clients restored from the registry, and on every update. Connect/disconnect events are filtered the same way.
- Removal: excluded clients get no entity object. Their registry entries are not auto-removed; a `remove_trackers` service (router.py:818-824, 982+) lets the user drop them manually.

### agittins/bermuda (bermuda) — A (caveat: BLE)
- `configured_devices` is a SelectSelector multi-select of discovered BLE devices, iBeacon meta-devices and recent random MACs. It is an opt-in allow-list, so empty means no trackers.
- Private BLE Device (IRK) devices are tracked automatically.
- The trackers are BLUETOOTH_LE BaseScannerEntity (area/distance based), not IP network clients. Re-bucket as N/A if only router clients count.

### akinin/ha_keenetic (ha_keenetic) — A (allow-list, UI multi-select)
- `create_device_tracker` (bool, "all clients", default False) and `create_select_device_tracker` (`cv.multi_select` of discovered hotspot clients, default []). Both are in the options step `configure_clients`. A tracker is created when the MAC is selected or "all" is on, so the default is no trackers.
- Removal: `remove_entities_or_devices` (__init__.py:148-186) removes trackers whose MAC is no longer selected while "all" is off. It also removes devices left with no entities.

## Summary
- **A**: technitiumdns (free-text IP include/exclude), openwrt_ubus (free-text MAC/IP prefix allow-list), FaserF openwrt (UI multi-select plus free-text MAC allow-list), asusrouter (UI multi-select include/exclude), ha_keenetic (UI multi-select allow-list plus "all"). With caveats (not router clients): wifi_sensor_tracker (entity selector of SSID sensors), bermuda (BLE multi-select).
- **B**: mikrotik_extended (track_network_hosts on/off), livebox (wifi/lan toggles plus active-only).
- **C**: zte_fibra_tracker, tplink_router, glinet, zte_router.
- **N/A**: dectyr_rx5, growappy, http_agent (single-target).
