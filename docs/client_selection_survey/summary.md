# Device tracker client selection — summary (2026-10-06, core dev @ 18a591e4eb0)

Question: which integrations let the user choose WHICH network clients get a scanner
device tracker (like unifi), vs. creating trackers for every client (like tplink_omada)?
Full per-batch reports (file:line refs) in the sibling `*/report.md` files; rubric in `rubric.md`.

Scope: 57 core + 49 HACS candidates (grep for ScannerEntity / SourceType.ROUTER / legacy
scanner APIs), plus sweeps for misses (4 extra HACS legacy scanners found).

Framework notes (apply everywhere, not counted per integration):
- Config-entry ScannerEntity with a MAC is created disabled unless the MAC already has a
  device in the device registry (`device_tracker/entity.py:~647`). fing overrides it (always enabled).
- Legacy YAML scanners all get `track_new_devices` + per-device `track:` in known_devices.yaml.
- unifi `client_source` is an always-include override, OR'ed with the coarse filters; it is
  NOT "only these". For exclusive selection the user also sets `track_clients=False`.

## Core — per-device selection (A)
| Integration | Setting | UI | Semantics | Deselect removes? |
|---|---|---|---|---|
| unifi | options `client_source` (+ `track_clients`, `track_wired_clients`, `ssid_filter`, `ignore_local_mac`) | multi_select of discovered clients | force-include; combine with track_clients=False for exclusive | yes |
| ruckus_unleashed | options `mac_filter` | multi_select of discovered clients | allow-list; empty = all | yes (registry + reload) |
| nmap_tracker | `hosts_list`, `hosts_exclude`, `mac_exclude` (config+options) | free-text multi | IP scope + IP/MAC deny-lists | no |
| bluetooth_le_tracker (BLE, legacy) | reads known_devices.yaml `track:` itself | YAML | allow/deny of BLE MACs | — |

## Core — coarse filters only (B)
asuswrt (`track_unknown`, `require_ip`), ddwrt (YAML `wireless_only`), fritz
(`feature_device_tracking` on/off), huawei_lte (`track_wired_clients`), keenetic_ndms2
(`interfaces` multi-select), opnsense (`tracker_interfaces`, config-flow only),
mikrotik (`force_dhcp`, weak).

## Core — none (C)
Config entry: tplink_omada, devolo_home_network, fing, freebox, luci, netgear, swisscom,
unifi_direct, vodafone_station.
Legacy YAML (framework controls only): actiontec, arris_tg2492lg, aruba, bbox, bt_home_hub_5,
bt_smarthub, cisco_ios, cisco_mobility_express, cppm_tracker, fortios, hitron_coda,
linksys_smart, meraki, quantum_gateway, sky_hub, snmp, synology_srm, thomson, tomato, ubus,
upc_connect, xiaomi, xiaomi_miio.

N/A: ping, private_ble_device (single-target); ibeacon (BLE, `allow_nameless_uuids`); zha,
kitchen_sink, mqtt_json, owntracks, aprs, fleetgo, google_maps, demo; not tracker platforms:
acaia, bluetooth, dhcp, dlna_dmr, imap, motionblinds_ble, probe_plus, sofar, wiim.

## HACS — per-device selection (A)
| Integration | Setting | UI | Semantics |
|---|---|---|---|
| Vaskivskyi/ha-asusrouter (asusrouter) | `client_filter` {no_filter,include,exclude} + `client_filter_list` | multi_select of discovered clients | include OR exclude; default all; `remove_trackers` service |
| bullitt186/ha-omada-open-api (omada_open_api) | `selected_clients` (+ `ssid_filter` narrows picker) | SelectSelector multiple, config+options | opt-in allow-list; deselected removed |
| djchen/ha-unifi-presence (unifi_presence) | `tracked_devices` | SelectSelector multiple | allow-list, must be non-empty; deselected removed |
| cataseven/Keenetic-Router-Pro (keenetic_router_pro) | `tracked_clients` (entry.data) | multi_select | opt-in allow-list; no cleanup |
| akinin/ha_keenetic (ha_keenetic) | `create_select_device_tracker` + `create_device_tracker` (all) | multi_select + bool | opt-in; deselected removed |
| FaserF/ha-openwrt (openwrt) | `tracked_devices` + `manual_tracked_devices` (+ track_devices/track_wired/skip_random_mac) | SelectSelector + free-text MACs | allow-list; empty = all; deselected NOT removed |
| travisghansen/hass-pfsense (pfsense) | `devices` + `device_tracker_enabled` | multi_select of ARP entries | opt-in allow-list; deselected removed |
| usersaynoso/ha-cudy-router (cudy_router) | `tracked_device_macs` + `auto_add_device_trackers` | SelectSelector multiple | picked only, or auto-all + picked; stale cleaned |
| vithurshanselvarajah/ha-glinet (glinet_router) | `add_all_devices`, `unknown_devices_filter_mode` (black/whitelist), `_select`, `_manual` | multi_select + free-text MACs | applies only to clients unknown to HA; HA-known always tracked |
| dscao/ikuai (ikuai) | `tracker_config` + include/exclude mode | multi_select of online IPs/MACs + free text | only configured targets; none by default |
| FUjr/homeassistant-openwrt-ubus (openwrt_ubus) | `wireless_tracker_whitelist`, `wired_tracker_whitelist` (+ interfaces) | free-text MAC/IP prefixes | allow-list; empty = all |
| Amateur-God/home-assistant-technitiumdns (technitiumdns) | `dhcp_ip_filter_mode` + `dhcp_ip_ranges` | free-text IP/CIDR/range | include OR exclude, by IP |
| cyberjunky/home-assistant-arpscan_tracker (arpscan_tracker) | `include`/`exclude`/`hosts` | free-text IPs | allow + deny; empty = all |
| elad-bar/ha-edgeos (edgeos) | per-device "Monitored" config switch entity | switch entity, not a flow | opt-in per device |
Caveat A (not router clients): agittins/bermuda (BLE `configured_devices` picker),
5a2v0/HA-WiFi-Sensor-Tracker (entity picker of SSID sensors), custom-components/ble_monitor
(per-device `track_device`).

## HACS — coarse filters only (B)
meraki_ha (`enable_device_tracker`, `enabled_networks`/`ignored_networks`), miwifi
(`is_track_devices`), mikrotik_extended & mikrotik_router (`track_network_hosts`), livebox
(wifi/lan toggles, active-only), unifi_insights (wifi/wired toggles), huawei_mesh_router
(`device_tracker` on/off), openwrt_presence (`enable_new_trackers`), zte_tracker
("register new devices" switch entity), pihole_presence (`stale_device_days`, weak),
padavan_tracker (YAML `rssi`), dlink_presence (YAML `require_ip`).

## HACS — none (C)
tplink_deco, honor_x3 (legacy), zte_fibra_tracker, tplink_router, glinet (HarvsG), zte_router,
inteno, speedport, swisscom_internetbox, technicolor (has an unused `devices`/`exclude`
schema), ubee (legacy), movistar_rft8115vw (legacy).

N/A: xiaomi_miot, sureha, better_presence, tado_ce, roomba_plus, dectyr_rx5, growappy,
http_agent, bosch_ebike, iphonedetect (single-target), petwalk, leakbot.
