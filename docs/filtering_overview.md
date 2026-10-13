# Device tracker client filtering: what integrations already do

Question: can the user choose **which** network clients get a device tracker? Survey of 2026-10-06
(core dev @ 18a591e4eb0). It's condensed here. The full per-integration reports with file:line
references are in [`client_selection_survey/`](client_selection_survey/) (`summary.md`, `*/report.md`).
Install counts come from analytics.home-assistant.io (2026-10-12).

| | Pick specific clients | Coarse filters only | Some filtering in total | No selection |
|---|---|---|---|---|
| Core | 3 | 7 | 10 of 42 | 32 |
| HACS | 14 | 12 | 26 of 38 | 12 |

Many more HACS integrations than core ones have this. Core has no standard way to do it, and we
push back on integration-specific solutions.

## Core: user picks specific clients

| Integration | Installs | Setting | How the user picks |
|---|---|---|---|
| unifi | 41.8k | options `client_source` (+ `track_clients`, `track_wired_clients`, `ssid_filter`) | multi-select of discovered clients; always-include, OR'ed with the coarse filters |
| nmap_tracker | 8.4k | `hosts_list`, `hosts_exclude`, `mac_exclude` | types IPs to scan, and IPs/MACs to exclude |
| ruckus_unleashed | 250 | options `mac_filter` | multi-select of discovered clients; only those are tracked (empty = all); deselected trackers removed |
| bluetooth_le_tracker | – | per-device `track:` in known_devices.yaml | YAML; Bluetooth, not network clients |

## Core: coarse filters only

fritz (48.7k, tracking on/off), asuswrt (5.2k, `track_unknown`, `require_ip`), mikrotik (3.1k,
Wi-Fi vs. all DHCP clients), keenetic_ndms2 (3.2k, `interfaces`), huawei_lte (850,
`track_wired_clients`), opnsense (594, `tracker_interfaces`, setup only), ddwrt (67, YAML
`wireless_only`).

## Core: no selection

freebox (6.2k), tplink_omada (3.4k), devolo_home_network (3.4k), netgear (2.9k), luci (859),
fing (281), unifi_direct (238), vodafone_station (184), swisscom (19), plus ~23 legacy YAML
scanners.

Framework-wide: legacy YAML scanners all get `track_new_devices` and a per-device `track:`. A
config-entry tracker for a MAC no other integration knows is created disabled
(`device_tracker/entity.py:660`). For tplink_omada users, that rule is the only control they have.

## HACS: user picks specific clients (14)

- Pick from a list of discovered clients: asusrouter (include or exclude), omada_open_api
  (nothing tracked until picked), unifi_presence (at least one must be picked),
  keenetic_router_pro, ha_keenetic, openwrt by FaserF (also typed MACs), pfsense, cudy_router,
  glinet_router (whitelist/blacklist, only for clients HA doesn't already know), ikuai.
- Typed lists: openwrt_ubus (MAC/IP prefixes), technitiumdns (IPs/subnets/ranges, include or
  exclude), arpscan_tracker (IP include/exclude).
- A "Monitored" switch entity per device instead of a settings form: edgeos.

HACS coarse filters only: meraki_ha, miwifi, mikrotik_extended, mikrotik_router, livebox,
unifi_insights, huawei_mesh_router, openwrt_presence, zte_tracker, pihole_presence,
padavan_tracker, dlink_presence.

HACS no selection: tplink_deco, tplink_router, glinet (HarvsG), zte_router, zte_fibra_tracker,
inteno, speedport, swisscom_internetbox, technicolor, honor_x3, ubee, movistar_rft8115vw.

Patterns worth copying: discovered-clients multi-select (unifi, ruckus, asusrouter, omada_open_api);
include/exclude mode (asusrouter, technitiumdns); removing trackers on deselect (ruckus,
omada_open_api, pfsense); applying only to clients HA doesn't already know (glinet_router).
