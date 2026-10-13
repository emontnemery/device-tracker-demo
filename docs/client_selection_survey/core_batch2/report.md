Paths are relative to `homeassistant/components/` in the core repo, on dev @ 18a591e4eb0.


**The rubric's description of unifi `client_source` is wrong.** A non-empty `client_source` does not mean "only those clients get trackers". It is an always-include list that is OR'ed with the coarse filters (`unifi/device_tracker.py:86`). To track only those clients, the user must also set `track_clients=False`.

# Device tracker client selection — core batch 2

## Framework baseline (applies to every config-entry `ScannerEntity` below)
`device_tracker/entity.py:647` (`ScannerEntity.entity_registry_enabled_default`): a tracker that has a MAC is created **disabled by default**, unless a device-registry device with that MAC already exists. This is not a user setting, so it does not count for the rubric. In practice, though, every config-entry integration in bucket C creates disabled entities for unknown clients.

Legacy scanners (`async_setup_scanner` / `see()`) all inherit two framework YAML settings:
- `track_new_devices` / `new_device_defaults.track_new_devices` (`device_tracker/legacy.py:97-109`, default True).
- The per-device `track:` flag in `known_devices.yaml` (`legacy.py:1045`).

That gives every legacy scanner a YAML-only, framework-level per-device choice. I classed those integrations by their own settings (C) and marked them "legacy-fw".

## Table

| Integration | Bucket | Keys / location | UI / selector | Default | Semantics |
|---|---|---|---|---|---|
| **unifi** (ref +) | **A** (allow-list, force-include) + B filters | options `client_source` (`config_flow.py:365`), `track_clients` (:351), `track_devices` (:355), `track_wired_clients` (:376), `ssid_filter` (:380), `ignore_local_mac` (:394); evaluated in `device_tracker.py:84-113` | options flow; `cv.multi_select` of discovered clients (client_source, ssid_filter), bools | track_clients/devices/wired = True; client_source/ssid_filter empty; ignore_local_mac False | `client_source` is an **OR override**: listed MACs are always tracked, NOT "only these"; exclusive selection needs `track_clients=False` as well |
| **tplink_omada** (ref −) | C | none (`device_tracker.py:31-39`) | — | all *known wireless* clients at setup | wireless-only is hard-coded; no option |
| freebox | C | none (`device_tracker.py:36-51`; config flow host/port only) | — | every LAN host | — |
| fritz | B | `feature_device_tracking` (`const.py:48`; config flow `config_flow.py:239/259`; options :443); `old_discovery` (:439) | bool | True | global on/off for client trackers |
| hitron_coda | C (legacy-fw) | YAML host/username/password/type (`device_tracker.py:25-31`) | YAML | all | — |
| huawei_lte | B | options `track_wired_clients` (`const.py:11`, `config_flow.py:405-410`; used `device_tracker.py:65-80,133-145`) | bool | True | False = wireless clients only |
| ibeacon | N/A (BLE beacons, not network clients) | options `allow_nameless_uuids` (`config_flow.py:57-90`, `const.py:51`); `ignore_uuids`/`ignore_addresses` in entry.data are auto-managed, not user-facing | free-text UUID + multi_select | empty | allow-list that opts in beacons with no name, by UUID; named beacons are always tracked |
| imap | not a tracker platform | — | — | — | no device_tracker.py |
| keenetic_ndms2 | B | options `interfaces` (`const.py:14`, `config_flow.py:216-225`; used `router.py:53,189`); `try_hotspot`/`include_arp`/`include_associated` (:226-239) | `cv.multi_select` of router bridge interfaces; bools | `["Home"]`; the three source bools True | only clients on the selected interfaces get trackers |
| kitchen_sink | N/A (demo) | — | — | — | one fixed DemoScanner + DemoTracker (`device_tracker.py:21-36`) |
| linksys_smart | C (legacy-fw) | YAML `host` (`device_tracker.py:24-26`) | YAML | all | — |
| luci | C | none (`device_tracker.py:99-118`; YAML PLATFORM_SCHEMA :35-43 is import-only) | — | all reachable | — |
| meraki | C (legacy-fw) | YAML `validator`/`secret` (`device_tracker.py:28-33`) | YAML | every observation is `see()`d (:130) | — |
| mikrotik | B (weak) | options `force_dhcp` (`const.py:19`, `config_flow.py:167`; `coordinator.py:259`); `arp_ping`, `detection_time` | bool | False | default: only wireless-registration clients (on wireless-capable hubs); True = all DHCP-lease clients |
| motionblinds_ble | not a tracker platform | — | — | — | no device_tracker.py |
| mqtt_json | N/A (GPS tracker) | YAML `devices: {dev_id: topic}` (`device_tracker.py:37-39`) | YAML | — | explicit list of GPS devices; not a network scanner |
| netgear | C | options `consider_home` only (`config_flow.py:84-88`) | — | all attached devices | router/AP mode decides automatically whether tracking runs (`router.py:114`); not user-settable |
| nmap_tracker | **A** (IP scan scope + IP and MAC deny-lists) | `hosts_list` (`const.py:22`), `hosts_exclude` (:23), `mac_exclude` (:24); schema `config_flow.py:149-160` (config + options); applied `__init__.py:198-200,271-272,418` | `TextSelector(multiple=True)` free text | hosts = local network; exclude = HA's own IP; mac_exclude empty | only hosts in hosts_list are scanned (can be single IPs); hosts_exclude and mac_exclude are deny-lists |
| opnsense | B | config-entry **data** `tracker_interfaces` (`const.py:8`, `config_flow.py:48-62`; filter `coordinator.py:55`; YAML import `__init__.py:35`) | `SelectSelector` multi-dropdown of firewall interfaces | `[]` | empty = all interfaces; otherwise only clients on the selected interfaces; no options flow |
| owntracks | N/A (phone GPS/BLE reporting) | YAML `waypoint_whitelist`, `events_only`, etc. (`__init__.py:34-63`) | YAML | — | not a network-client scanner |
| ping | N/A-single-target | config flow `host` (`config_flow.py:50`) | text | — | one config entry = one tracked host |

## Per-integration notes

**unifi (reference positive; confirmed, with the correction above).**
- **Where the options live.** Options flow is `config_flow.py:290-420`. Top level: `track_clients`, `track_devices`, `block_client`. A collapsed `more_options` section holds `client_source`, `track_wired_clients`, `ssid_filter`, `detection_time`, `ignore_wired_bug`, `ignore_local_mac`, `dpi_restrictions` and the bandwidth/uptime sensor toggles. Defaults are in `const.py:47-55`; parsing is in `hub/config.py:103-119`.
- **How a client is allowed.** `async_client_allowed_fn` (`device_tracker.py:84-113`) checks in this order:
  1. MAC in `client_source` → allowed, skipping every other check.
  2. `track_clients` is False → not allowed.
  3. `ignore_local_mac` is on and the client is wireless with a locally-administered MAC → not allowed.
  4. Client is not known as wireless and `track_wired_clients` is False → not allowed.
  5. Client is wireless, has an SSID, `ssid_filter` is non-empty and the SSID is not in it → not allowed.
  6. Otherwise allowed.
- **Other uses of `client_source`.** UI label "Create entities from network clients" (`strings.json:225`). It also gates sensors and switches the same way (`sensor.py:77,92`; `switch.py:85`).
- **`ssid_filter` also affects connection state.** A wireless client on an unselected SSID reports as not connected (`device_tracker.py:124-130`).
- **`track_devices`** controls Ubiquiti infrastructure trackers through a separate allowed check (`:183`).
- **Restore and pruning.** MACs in `client_source` or `block_client` are always restored, even when inactive or stale. Other inactive trackers are pruned after the retention window (`hub/entity_loader.py:133-170`).
- **Removal.** On any options update, each entity re-runs its allowed check and removes itself, including its entity-registry entry, if no longer allowed (`entity.py:277-290`). Newly allowed clients are added on the same signal (`hub/entity_loader.py:255-260`).

**tplink_omada (reference negative; confirmed).**
- Creates trackers for all *known wireless* clients once, at setup (`device_tracker.py:31-39`).
- No options flow; the config flow asks only for host, SSL, credentials and site.
- A code comment says users are expected to enable the entities they want, which depends on the framework's disabled-by-default behaviour.

**freebox — C.** Every MAC in `router.devices` gets a tracker on each new-device signal. Config flow is host/port only.

**fritz — B.**
- `feature_device_tracking` is asked in the user and SSDP config steps and in the options flow (which reloads the entry).
- When it is False, the coordinator skips the device scan (`coordinator.py:320`), so no client trackers are created.
- The only per-device filtering is internal (`helpers.py:14-30`: skip clients with no IP or already tracked).
- The "cleanup" button (`button.py:59`, `coordinator.py:717`) removes trackers for hosts the box no longer knows. With tracking disabled, it removes all client trackers.

**hitron_coda, linksys_smart, meraki — C (legacy-fw).** Their YAML holds only connection or auth keys. Meraki (a webhook receiver) calls `see()` for every observed `clientMac` with `SourceType.ROUTER`.

**huawei_lte — B.**
- `track_wired_clients` filters new entities as "wired allowed, or the client is wireless" (`device_tracker.py:144`).
- At setup, already-registered wired trackers are skipped when the option is off (`:65-80`). They are not removed from the registry, so they are left orphaned.
- The options flow is a plain `OptionsFlow` with no update listener. A change applies to new clients immediately, and to existing trackers only after a reload or restart.

**ibeacon — N/A (BLE).**
- Auto-discovers all iBeacons as Bluetooth LE scanner entities.
- `allow_nameless_uuids` is a UUID allow-list for beacons whose device has no name; those are ignored by default (`coordinator.py:152-155,476-495`).
- `ignore_uuids` / `ignore_addresses` are filled automatically for beacons that break the spec.
- If BLE trackers were in scope, this would be bucket A, limited to nameless beacons.

**keenetic_ndms2 — B.**
- Options flow reloads the entry. `interfaces` is a required multi-select of the router's bridge interfaces, default `["Home"]`.
- `try_hotspot`, `include_arp` and `include_associated` choose the data source.
- `router.py:186-190` keeps only devices on the selected interfaces.
- Trackers already in the registry are always re-created at setup (`device_tracker.py:40-60`). Deselecting an interface does not remove them; they just stop updating.

**kitchen_sink — N/A (demo).** Two hard-coded entities.

**luci — C.** Adds every MAC returned by `get_all_connected_devices(only_reachable=True)`. No options flow. The YAML `PLATFORM_SCHEMA` only imports host and credentials into a config entry.

**mikrotik — B (weak).**
- `force_dhcp` defaults to False. On a wireless-capable hub, only wireless/CAPsMAN registration-table clients are tracked. Setting it True, or having no wireless data, tracks all DHCP-lease clients (`coordinator.py:256-261`).
- Trackers already in the registry are restored (`device_tracker.py:34-43`) and never removed.

**mqtt_json — N/A (GPS).** The YAML `devices` map lists the tracked GPS devices explicitly; it is not a network scanner.

**netgear — C.** The only option is `consider_home`. Every device in `router.devices` gets a tracker. Router/AP mode decides automatically whether tracking runs at all (`router.py:114`).

**nmap_tracker — A.**
- The config flow and options flow (which reloads the entry) share one schema (`config_flow.py:138-185`).
- `hosts_list` (required free-text multi): IPs, CIDRs or ranges. It is the nmap target set, so single IPs make it an IP allow-list.
- `hosts_exclude`: IP deny-list, passed to nmap as `--exclude`.
- `mac_exclude`: MAC deny-list, applied after the scan (`__init__.py:418-420`).
- The lists are typed in by hand, not picked from discovered clients. Nothing is removed: excluded MACs stop updating and their registry entries stay.
- Possible UI problem (not checked in the UI): the labels in `strings.json` use keys `hosts`/`exclude`, but the schema keys are `hosts_list`/`hosts_exclude`. Those two fields may show without translated labels.

**opnsense — B.**
- `tracker_interfaces` is stored in config-entry data. It is set in a config-flow step or by YAML import.
- Empty means all interfaces; otherwise only ARP entries on the listed interfaces are kept (`coordinator.py:55`). Interfaces are checked against the firewall at setup (`__init__.py:135-150`).
- There is no options flow or reconfigure step, so it can't be changed after setup.

**owntracks — N/A.** Mobile-app GPS/BLE reporter. Its YAML settings don't select network clients.

**ping — N/A-single-target.** One config entry = one host = one tracker.

**imap, motionblinds_ble — not a tracker platform.** Neither has a `device_tracker.py`; they were broad grep hits.

## Summary
- **Bucket A:**
  - **unifi** (reference): `client_source` is an always-include multi-select of discovered clients, not exclusive.
  - **nmap_tracker**: typed-in IP/CIDR scan scope, plus IP and MAC deny-lists.
- **Bucket B:**
  - **fritz**: global on/off.
  - **huawei_lte**: wired on/off.
  - **keenetic_ndms2**: interface multi-select.
  - **opnsense**: interface multi-select, set only during config flow or YAML import.
  - **mikrotik** (weak): `force_dhcp` switches between wireless-only and all DHCP clients.
- **Bucket C:** tplink_omada (reference), freebox, luci, netgear. Legacy scanners hitron_coda, linksys_smart and meraki only have the framework `known_devices.yaml` `track:` / `track_new_devices` settings.
- **N/A:** ibeacon (BLE; has the nameless-UUID allow-list), kitchen_sink (demo), mqtt_json (GPS), owntracks (GPS), ping (single target).
- **Not a tracker platform:** imap, motionblinds_ble.
