# Survey: per-router / per-AP / per-client zone settings in router device trackers

Date: 2026-10-13. Read-only survey. Sources were fetched from each repo's default branch (or latest release where noted) via `gh api` / raw.githubusercontent and grepped for `zone`, `location_name`, `CONF_ZONE`, `associated_zone`, `def state`, `in_zones`. Paced GitHub code searches were also run (queries listed in section 5).

## 1. Core findings (sanity check)

- I grepped `config_flow.py` and `const.py` of every core integration whose `device_tracker.py` uses `ScannerEntity` or `SourceType.ROUTER` for `zone|location`, ignoring timezone hits. The only hits were `ssdp_location` in huawei_lte, keenetic_ndms2, netgear and fritz. None of them is a zone option.
- I grepped those core `device_tracker.py` files for `location_name|zone|def state`. There were no hits, so no core scanner overrides state or location.
- Conclusion: in core the only zone mechanism is the per-entity `device_tracker.associated_zone` entity-registry option. There is no per-router or per-device setting. This confirms the caller's finding.

## 2. HACS/custom integrations that DO offer a zone/location setting

| Repo | Setting key | Where | Granularity | Semantics |
|---|---|---|---|---|
| **vmakeev/huawei_mesh_router** (79 stars, pushed 2026-02) | option `device_tracker_zones` (bool, default False) + a per-router **"Zone" select entity** (`Select.ROUTER_ZONE`), one for the primary router and one for each satellite router. Values are kept in Store `huawei_mesh_{entry_id}_router_zones` | `const.py:21,37`; `__init__.py:84-92`; `select.py:239-265`; `update_coordinator.py:1074-1093, 1288-1292`; `device_tracker.py:91-108`; docs `docs/device-tracking.md#router-specific-zones`, `docs/controls.md#router-specific-zone` | **Per router/AP in a mesh** (the case the caller asked about) | Every client gets the zone of the router it is connected through (`connected_via`). Router devices get their own zone. An empty selection falls back to Home. `state` returns the **zone friendly name**, and `source_type` is switched to **GPS** whenever zones are on |
| **C3H3-AI/ha-huawei-router** (7 stars; also c3h3-ci/ha-huawei-router) | `device_tracker_zones`, same code | `custom_components/huawei_router/{const,select,update_coordinator,device_tracker}.py` | Per router | Rebranded derivative of vmakeev's code. `device_tracker.py:96-103` is identical |
| **FaserF/ha-openwrt** | `mqtt_zone` (`CONF_MQTT_ZONE`), a zone EntitySelector in the config flow step `mqtt_zone` and options step `options_mqtt_zone` | `const.py:34`; `config_flow.py:197, 2119-2137, 2804-2822`; `helpers/mqtt_presence.py:89-110`; `helpers/presence_templates/scripts/presence_event.sh:78-84`; strings title "MQTT Presence Location Zone" | **Per router (config entry)**, MQTT presence path only | The integration deploys shell scripts (based on f45tb00t/OpenWRT_HA_Presence) onto each OpenWrt AP. These publish the MQTT tracker state `ZONE_NAME` and attributes `{"in_zones":["<zone entity>"],"connected_ap":"<router id>"}`. Scripts also check whether another AP owns the MAC, so roaming between APs is handled. Its native polling `device_tracker.py` has no zone option. Upstream f45tb00t/OpenWRT_HA_Presence has no zone setting; FaserF added it |
| **Csontikka/ha-mikrotik-extended** (36 stars, pushed 2026-10-04) | option `zone` (`CONF_ZONE`), free-text `str`, default `home` | `config_flow.py:453, 666-667`; `coordinator.py:318-320`; `device_tracker.py:232-234`; README:569 | **Per router (config entry, integration-wide)** | `state` returns `option_zone if is_connected else not_home`. The string is used literally and is not checked against zones |
| **tomaae/homeassistant-mikrotik_router** (471 stars), **historical** | `zone` (`CONF_ZONE`), same as above, before v2.3 | pre-v2.3 (`e56e24c8`): `device_tracker.py:218`, `config_flow.py:363-364`, `coordinator.py:143-145`. v2.3 (2026-09-11, commit `bd093d00` "Migrate device trackers to the 2026.8 zone model"): `__init__.py:203-241, 297-300` | Was per router; now per entity | v2.3 **removed** the integration-wide zone option. A migration converts the legacy zone (name or entity_id) to a `zone.*` entity_id and writes it into each tracker's `device_tracker.associated_zone` entity option |
| **5a2v0/HA-WiFi-Sensor-Tracker** (19 stars). Not a router; the source is a phone's SSID sensor | `extra_zones` list of `{ssid, zone}` plus `home_wifi_ssid` | `config_flow.py:15, 29-53, 139+`; `device_tracker.py:19-25, 128-167` | **Per SSID**: one mapping applies to all trackers in the entry | Being on SSID X puts the device in the mapped zone. State is the zone's friendly name, and lat/lon are copied from the zone. It **writes the private core attribute `self._scanner_option_associated_zone`** (`device_tracker.py:134,144,157`), so it depends on core internals |
| **tenfire/ha-ssid-connection-tracker** (0 stars). Not a router; one entry per SSID sensor | `zone` (`CONF_ZONE`), zone EntitySelector | `config_flow.py:32-46, 93`; `device_tracker.py:34, 59-65`; `__init__.py:16-20` | Per config entry (one connection) | Uses the official API: on add it seeds the core `device_tracker.associated_zone` entity option (`CONF_ASSOCIATED_ZONE`) from the configured zone. This is a clean example of "integration-level default → core per-entity option" |

### Consumer-side (not a tracker producer, but maps router trackers to zones)

| Repo | Setting | Where | Semantics |
|---|---|---|---|
| **KruseLuds/halp** (13 stars), "Home Assistant Location & Presence analyzer" | `router_zones` (`CONF_ROUTER_ZONES`, dict of router-tracker entity_id → zone, or `__none_mobile__`), plus `ble_zones` | `const.py:19-24`; `config_flow.py:204-242` (one zone dropdown per selected router entity, default `zone.home`) | A per-person aggregator. The user gives each router tracker entity a fixed zone ("fixed-location mappings"). This works like core `associated_zone` but sits in the consumer instead of the tracker |

## 3. Notable near-misses

- **theoabw/ha-openwrt-presence**: `const.py:14,19` defines `CONF_ZONE="zone"` / `DEFAULT_ZONE="zone.home"`, but nothing uses them (dead constants). The README (lines 149-150) points users to core's per-entity associated zone. Note for the meeting: it creates **separate tracker entities per observer (router) for the same MAC** ("Two observers reporting the same MAC address therefore retain separate source tracker entities"). With core's per-entity option, that already gives (router, client) zone granularity.
- **djchen/ha-unifi-presence**: `device_tracker.py:42` says it relies on core ScannerEntity "including associated-zone handling". No own setting.
- **Hard-coded `home` state or location_name.** These override core and would **ignore** `associated_zone`:
  - lrehmann/pihole_presence: `device_tracker.py:79-81` `state` → `STATE_HOME if is_connected else STATE_NOT_HOME`.
  - custom-components/ble_monitor: `device_tracker.py:226-228`, same pattern.
  - Found by code search outside the batch list:
    - ansgarlichter/ha_vodafone_router: TrackerEntity with SourceType.ROUTER; `location_name` → `STATE_HOME if ... else None`.
    - MrPlanetRider/VOO-HACS: `location_name` → home/not_home.
    - lexbrugman/ha-unifi-aggregate-presence: one aggregate "anyone" TrackerEntity whose `location_name` is home/not_home.
- **TrackerEntity reporting location_name for non-network "places".** None of these is a zone-for-router setting:
  - benleb/sureha: pet location from the flap.
  - p0l0/hapetwalk: pet in/out.
  - FehTeh/growappy: student presence.
  - corgan2222/ha-better-presence2: per-person aggregate that passes the zone name through.
  - pnbruckner/ha-composite-tracker: falls back to `location_name = <state>` of a non-GPS input. It has no zone config of its own (no zone hits in `config_flow.py` or `const.py`).
  - johnnyh1975/roomba_plus: current room as `state`.
- **agittins/bermuda** (BLE): device `zone` is only `home`/`not_home` (`bermuda_device.py:119,698-700`). It has no zone option; areas are used instead.
- **hiall-fyi/tado_ce**: `_attr_in_zones = ["zone.home"]` for Tado geofencing presence. It is cloud data with no setting.
- **custom-components/places**: a reverse-geocode sensor that reads tracker zones (`home_zone` config). It is not a tracker setting.
- **"zone" hits that are unrelated**: firewall zones (vithurshanselvarajah/ha-glinet, ruaan-deysel/unifi-insights, Kajkac/ZTE), thermal zones (FUjr/openwrt-ubus), DNS zones (technitiumdns), camera analytics zones (meraki_ha), Aura light zones (asusrouter), IPv6 zone ids (Keenetic-Router-Pro), timezone (cudy).

## 4. Repos checked with "no" (no zone or location setting for routers or clients)

I inspected all of these (source downloaded and grepped):

- AldenDana/ha-zte-fibra
- AlexandrErohin/home-assistant-tplink-router
- Amateur-God/home-assistant-technitiumdns
- Cyr-ius/hass-livebox-component
- DECTYR/ha-integration
- DSorlov/http_agent (per-sensor lat/lon templates, not zone)
- FUjr/homeassistant-openwrt-ubus
- FehTeh/ha-custom-component-growappy
- HarvsG/ha-glinet4-integration
- Kajkac/ZTE-MC-Home-assistant-repo
- PaulAnnekov/home-assistant-padavan-tracker
- Vaskivskyi/ha-asusrouter (the `dev` branch is mid-refactor and has no platform files, so I checked release 0.40.1)
- agittins/bermuda
- akinin/ha_keenetic
- al-one/hass-xiaomi-miot
- amosyuen/ha-tplink-deco
- ayavilevich/homeassistant-dlink-presence
- benleb/sureha
- brewmarsh/meraki-homeassistant
- bullitt186/ha-omada-open-api
- cataseven/Keenetic-Router-Pro
- corgan2222/ha-better-presence2
- custom-components/ble_monitor
- cyberjunky/home-assistant-arpscan_tracker
- djchen/ha-unifi-presence
- dmamontov/hass-miwifi
- dscao/ikuai
- elad-bar/ha-edgeos
- hiall-fyi/tado_ce
- johnnyh1975/ha_roomba_plus
- juacas/honor_x3
- juacas/zte_tracker
- kevinhaendel/ha-ubee
- lrehmann/pihole_presence
- luis-garza/movistar_rft8115vw
- marq24/ha-bosch-ebike-flow
- mudape/iphonedetect
- nielstron/inteno_hass
- p0l0/hapetwalk
- pajew-ski/ha-speedport
- ruaan-deysel/ha-unifi-insights
- sHedC/homeassistant-leakbot
- schmidtfx/swisscom-internetbox-hass
- shaiu/technicolor
- theoabw/ha-openwrt-presence (dead constant only)
- travisghansen/hass-pfsense
- usersaynoso/ha-cudy-router
- vithurshanselvarajah/ha-glinet
- pnbruckner/ha-composite-tracker
- custom-components/places
- zachcheatham/ha-omada
- kvj/hass_openwrt

FaserF/ha-openwrt has nothing in its **native** tracker; the positive is MQTT-only, see section 2. tomaae/homeassistant-mikrotik_router has **no current** option; the positive is historical, see section 2.

Limits: the survey covers only Python/JSON/YAML/MD files under `custom_components/` and top-level docs. Other files (tests, `docs/`) were not grepped, except for docs fetched separately for the Huawei and FaserF positives. GitHub code search was rate-limited (10/min, paced) and only covers indexed default branches. The multi-site searches (`ap_zone`, `zone_per_ap`/`ap_zones`, `ScannerEntity "zone" "access_point"`, `"SourceType.GPS" "ap_mac" location_name`, `ScannerEntity "zone" "site"`) found **no** UniFi, Omada or other per-AP or per-site zone integrations.

## 5. GitHub code searches run (positives in bold)

- `ScannerEntity CONF_ZONE`: **tenfire/ha-ssid-connection-tracker**
- `ScannerEntity option_zone`: **Csontikka/ha-mikrotik-extended**, plus many personal config repos vendoring old tomaae mikrotik_router
- `"device_tracker_zones"`: **vmakeev/huawei_mesh_router**, **C3H3-AI / c3h3-ci ha-huawei-router**, tomaae (migration)
- `ScannerEntity "zone.name"`: the Huawei repos only
- `ScannerEntity location_name path:custom_components`: sureha, xiaomi_miot, oukene entity_copy / entity_collector (copies)
- `ScannerEntity "STATE_HOME" "zone" path:custom_components`: wifi_sensor_tracker, bermuda
- `"_scanner_option_associated_zone"`: **5a2v0/HA-WiFi-Sensor-Tracker** (private-attribute use)
- `"CONF_ASSOCIATED_ZONE"`: tomaae (migration), tenfire (seeding)
- `TrackerEntity "SourceType.ROUTER" location_name`: vodafone_router, VOO-HACS, unifi-aggregate-presence (all hard-coded home), composite, petwalk, xiaomi_miot, others not router-related
- `"router_zones"`: Huawei repos, **KruseLuds/halp** (consumer-side)
- `ScannerEntity "def state" "zone"`: mikrotik (tomaae-legacy copies, Csontikka), Huawei, wifi_sensor_tracker

## Bottom line

- **Per-router / per-AP zone** exists in two places:
  - **vmakeev/huawei_mesh_router** and its derivative: a mesh-aware select entity per router, and clients inherit the zone of the router they connect through.
  - **FaserF/ha-openwrt**: an MQTT presence zone per router, with handoff between APs.
- **Integration-wide zone per config entry** exists in **Csontikka/ha-mikrotik-extended**, and existed in **tomaae/mikrotik_router** until v2.3. In September 2026 tomaae migrated it *into* core's per-entity `associated_zone`.
- **Per-SSID zone** exists in **5a2v0/HA-WiFi-Sensor-Tracker** (which pokes the private `_scanner_option_associated_zone`) and **tenfire/ha-ssid-connection-tracker** (which seeds the `associated_zone` entity option).
- **None of the ~50 batch-list repos except those above** has a zone or location setting.
