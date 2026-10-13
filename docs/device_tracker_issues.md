# Router device trackers: problem overview

Prep for the exploration meeting (Erik, Niels, possibly design). Based on our Discord discussion of
2026-10-05/06.

## Background

Router integrations (unifi, fritz, asuswrt, tplink_omada, ...) create a `device_tracker` entity
(`ScannerEntity`) for each MAC address seen on the network. Integrations with several access points
or several config entries create one entity per client per AP.

Popularity of the biggest ones (analytics.home-assistant.io, 2026-10-12, of ~699k installs):
fritz 48.7k, unifi 41.8k, nmap_tracker 8.4k, freebox 6.2k, asuswrt 5.2k, tplink_omada 3.4k,
devolo_home_network 3.4k, keenetic_ndms2 3.2k, mikrotik 3.1k, netgear 2.9k.

## How it works today

- `ScannerEntity.device_info` is `@final` and returns `None`, so a router tracker never describes a
  device (`device_tracker/entity.py:654`).
- The tracker is **disabled by default** unless some other integration already registered a device
  with the same MAC (`entity.py:660`).
- If the MAC is known, the tracker creates its own device with that MAC connection, named
  hostname or MAC (`entity.py:706`).
- Old intent: that device was shared with the other integration's device, so the tracker showed
  up on the phone's device and didn't clutter the UI.
- That never worked for phones. mobile_app has never registered a MAC on its device: it uses
  `identifiers` only, and no version in git history has `connections`. So a router tracker
  could never land on the mobile_app device, even with MAC privacy off. Sharing only ever
  happened with integrations that register MACs (Shelly, ESPHome, Sonos, ...). See the
  phone-matching gap below.
- Since devices are no longer shared between config entries, even that case now gets a separate
  device, shown under "Linked devices".
- A device created by the **same** integration also counts as "known". When such a device appears
  after the tracker, a listener enables the tracker (`entity.py:90`). Devices are created even for
  disabled entities.
- No core router integration adds its own disable-by-default logic. fing overrides the rule to
  always enable.
- As a result, the rule only hides clients for some integrations:
  - **netgear** creates per-client sensors (link rate, signal, SSID, ...) with `connections={MAC}`
    for every client (`netgear/sensor.py:37`).
  - **fritz** creates a parental-control switch for every client with an IP, if the box supports
    it (`fritz/switch.py:240`).
  - So in both, every client already gets a device and an enabled tracker today.
  - **unifi** only creates client devices for opted-in entities (block switches,
    bandwidth/uptime sensors), so its wireless trackers stay disabled. Instead it filters which
    trackers get created (`unifi/device_tracker.py:84`).
  - Integrations without per-client entities (tplink_omada, asuswrt, freebox, mikrotik, keenetic,
    devolo, ...) rely fully on the rule.

End result: a long list of device trackers named by hostname or raw MAC. For most integrations they
have no device, so there's no device-based naming and no device to disable or delete. Users who
enable them see the full mess. fritz and netgear users get every client enabled, each with its own
device.

## Agreed: let scanner trackers create devices

Drop the `device_info = None` suppression and let router integrations create a device per client.
Popular integrations already do this for clients through their other platforms:

- unifi: `connections={MAC}`, `manufacturer=client.oui`, `name=client.name or client.hostname`
  (`unifi/entity.py:90`).
- netgear: `connections={MAC}` plus `via_device_id` = the router (`netgear/entity.py:35`).
- fritz: `connections={MAC}` on the profile switches (`fritz/switch.py:512`).

The manufacturer from the MAC prefix (OUI) only works for devices that keep their real MAC (IoT
devices, TVs, printers, ...). Phones and tablets randomize by default (iOS 14+, Android 10+). A
randomized MAC is locally administered (second hex digit 2, 6, A or E) and has no registered
vendor, so those devices get no manufacturer. The demo reflects this: phones show `<unknown>`.

Per-AP duplicates stay: one device per client per AP or entry. We can't fix that, and it's
accepted.

### Catch: the default-disabled rule switches itself off

The rule (`entity.py:660`) treats `device_info is not None` as "enabled". Once trackers set
`device_info`, every tracker is created enabled. In the demo all 25 are enabled (see the
screenshots). For a home with 50–100 clients and a couple of APs, that means 100+ enabled trackers
and devices, with state writes and recorder history for each.

Making the rule independent of `device_info` doesn't really help. The platform creates the device
before it applies the disabled check (`entity_platform.py:1027` vs `:1076`). So we'd get a quiet
entity list but 100+ devices holding only a disabled tracker. Existing installs keep their disabled
trackers, but those would gain a device each.

Options:

1. **Device creation alone:** every client is enabled and has a device. Simple, but noisier than
   today for most integrations. It's what fritz and netgear users already get.
2. **Device creation plus "disabled unless MAC known":** a quiet entity list, but a cluttered device
   list. We'd have to decide whether disabled trackers get devices.
3. **Device creation plus client selection (below):** unselected clients get no entity and no
   device, like ruckus, omada_open_api and pfsense.

So the two changes aren't fully independent. Either ship device creation together with selection,
or decide that option 1 or 2 is acceptable for now. The per-entry "Enable newly added entities"
system option still creates devices, and few users find it.

## Needs design: let the user pick which clients to track

Most clients on a network are irrelevant for presence. The idea is a standard way for router
integrations to expose the network clients they see, and a UI where the user picks which ones
become device trackers.

- Many integrations already build their own version of this, especially in HACS. Core has no
  standard and we push back on integration-specific solutions. Core 3/42, HACS 14/38 offer
  per-client selection (see [filtering_overview.md](filtering_overview.md)).
- What a router can show for each client: user-assigned name (if the router has one), DHCP
  hostname, IP, MAC, vendor (from the MAC's OUI), connected/last seen, AP/SSID.
- Phones: private MAC per network, but stable per network by default, so a picked phone stays
  tracked. But a phone is the hardest client to recognize in the list:
  - No vendor, because the MAC is randomized (see above).
  - Usually no useful name. The client sends the name in its own DHCP request; the router only
    records it.
    - iOS sends a generic hostname when the private address is on
      ([Apple](https://support.apple.com/en-gb/HT211949)).
    - Android varies. Android 15 has a per-network "Send device name" setting, reportedly on by
      default ([GrapheneOS](https://discuss.grapheneos.org/d/16593-wlan-settings-send-device-name)).
      Older versions sent `android-<hex>`, and some manufacturers send the model name.
  - So a phone typically shows as a bare MAC, at best a model name. Only an alias the user typed
    into the router UI ("Erik's iPhone" in unifi) makes it recognizable. Some routers guess the
    device type from DHCP fingerprints or mDNS, but that's specific to each router and rarely
    exposed through its API.

What unifi's picker does today (real integration against a fake controller, screenshots
`unifi_*`):

- It's under Options → More options → "Create entities from network clients"
  (`client_source`). It's a dropdown of `name or hostname (MAC)`. Unnamed phones show up as
  `(ae:62:0b:d4:9f:3a)`, and offline clients are listed too.
- `client_source` applies to all platforms, not just trackers: each picked client also gets a
  "blocked" switch. That switch creates the client device, and the device enables the tracker.
  Picked clients end up enabled and on a device named after the UniFi alias.
- Default (track clients on, nothing picked): 15 client trackers, all disabled, no devices.
- With track clients off and three clients picked, the other 12 trackers stay in the registry as
  disabled. They were never loaded, so unifi's removal logic never runs for them.

Open questions:

1. Where does the UI live: each integration's options flow (like unifi `client_source` and
   ruckus `mac_filter`) or a shared core UI?
2. Minimum features: search, show online/offline, show vendor/hostname, give a client a name?
3. Default for newly seen clients: track nothing, track everything, or create disabled?
4. When a client is deselected, are its entity and device removed?
5. Validation: can the other integrations (fritz, asuswrt, omada, ...) supply enough info for a
   useful list? unifi clearly can.
6. Priority: it needs solving but ranks low. If it's small, we just do it. If not, it gets
   prioritized against other work. Bring in design (Marcin?) for the UI.

## Related gap: zone per router or AP

- Each tracker entity can be given a zone in its settings: "Associated zone", the entity-registry
  option `device_tracker.associated_zone` from #172157 (`device_tracker/entity.py:480`). See
  `../screenshots/zone_1_entity_settings.png`.
- A router or AP **device** has no such setting (`../screenshots/zone_3_router_device_settings.png`:
  only name, area, labels, enable). A user with an AP at a holiday home or office has to set the
  zone on every client tracker of that AP, one by one, including new ones.
- Core router integrations have no zone option of their own.
- Custom integrations that do it (survey in `zone_survey/report.md`):
  - **huawei_mesh_router** (and a fork): a "Zone" select entity per router/satellite. Clients
    inherit the zone of the router they're connected through. It overrides `state` and switches
    `source_type` to GPS.
  - **FaserF/ha-openwrt**: a zone per router for its MQTT presence mode, with handoff between
    APs.
  - **ha-mikrotik-extended**: one free-text zone per config entry.
  - **tomaae/mikrotik_router** had the same until v2.3. In September 2026 it migrated that
    setting into core's per-entity `associated_zone`.
  - **SSID-based trackers**: HA-WiFi-Sensor-Tracker maps SSID → zone, but writes core's private
    `_scanner_option_associated_zone`. ha-ssid-connection-tracker seeds the `associated_zone`
    entity option from an entry-level zone.
- With per-AP client devices (proposed above), a zone on the AP device that its client trackers
  inherit, unless overridden per entity, would be a natural fit. Open question: device-level
  zone, config-entry option, or leave it to integrations?

## Related gap: router trackers can't be matched to the phone

- MAC privacy is on by default on iOS and Android, so a phone joins each Wi-Fi network with a
  random per-network MAC. The router integration only ever sees that MAC, not the hardware MAC.
- mobile_app's device has no MAC at all: it registers `identifiers` only, never `connections`
  (`mobile_app/__init__.py:208`). As far as I know, the companion apps can't read the phone's own
  MAC either. The "Wi-Fi BSSID" sensor reports the AP's MAC, not the phone's.
- So HA can never link a router tracker to the mobile_app device of the same phone, even with
  privacy turned off. The router tracker ends up named by a random MAC (or no hostname), with no
  link to the phone's device or its person. The user has to recognize it and add it to the
  person by hand.
- Open question: is a manual link worth offering, e.g. "this client is that phone" in the client
  picker? Or could mobile_app report something the router can match, like IP or hostname, while
  on the home Wi-Fi?
- In the demo, each phone is registered through the real mobile_app API. Each person only has the
  mobile_app tracker; nothing links it to the router's view of the same phone. In the unifi
  instance, the phone and the picked UniFi client are both called "Erik's iPhone": two unrelated
  devices, and the router tracker becomes `device_tracker.erik_s_iphone_2`.

## Screenshots

From the demo instances in this repo (see the [README](../README.md)). The today and proposed
instances run the `demo_router` custom integration (`../custom_components/demo_router`), with a
"Main router" and an "Upstairs access point" entry, 20 clients, and a `demo_plug` Shelly-like
plug that registers its MAC. All three instances also have two mobile_app phones, Erik's iPhone
and Anna's Galaxy S24, on their own persons.

Today (stock `ScannerEntity`):

- `../screenshots/today_1_integration.png`: 25 entities, but only one client device (the plug's
  MAC).
- `../screenshots/today_2_entities_default.png`: out of the box only one tracker is visible; the
  other 24 are disabled.
- `../screenshots/today_3_entities_enabled.png`: after the user enables them: names like
  `5a:1c:93:7e:21:04`, no device, duplicates per AP.
- `../screenshots/today_4_device_kitchen_plug.png` and `today_4_device_shellyplug_s_3a1f2c.png`: the
  tracker for a known MAC gets its own device, linked to the plug instead of joining it.

Proposed (scanner creates a device, unifi/netgear style):

- `../screenshots/proposed_2_devices.png`: one device per client per AP, vendor filled in from OUI,
  every tracker enabled.
- `../screenshots/proposed_3_entities.png`: trackers grouped under devices; names come from the
  device.
- `../screenshots/proposed_4_device_5a1c937e2104.png`: a phone with a private MAC: device named by
  MAC, "Connected via Main router", linked to the same MAC's device on the upstairs AP.
- `../screenshots/proposed_1_integration.png`, `proposed_4_device_main_router.png`: integration and
  router pages.

UniFi (the real core integration against a fake controller with the same 20 clients, port 8126):

- `../screenshots/unifi_1_integration.png`, `unifi_2_entities_default.png`: after setup, only the
  two AP trackers are enabled; the 15 client trackers are disabled.
- `../screenshots/unifi_3_options.png`, `unifi_4_options_expanded.png`,
  `unifi_4b_options_expanded_scrolled.png`: the options flow.
- `../screenshots/unifi_5_client_picker.png`: the "Create entities from network clients" picker.
- `../screenshots/unifi_6_entities_after_pick.png`, `unifi_7_devices_after_pick.png`: after
  turning track clients off and picking 3 clients.

Zones: `../screenshots/zone_1_entity_settings.png` (per-entity option),
`zone_3_router_device_settings.png` (nothing on the router device).

mobile_app (proposed instance, except where noted):

- `../screenshots/mobile_1_app_device.png`: the phone's mobile_app device: no MAC, and the BSSID
  sensor shows the AP's MAC.
- `../screenshots/mobile_2_devices_both_views.png`: the mobile_app devices next to the router's
  devices for the same phones (`5a:1c:93:7e:21:04`, `Galaxy-S24`), with nothing linking them.
- `../screenshots/mobile_3_trackers_both_views.png`: the same, as tracker entities.
- `../screenshots/mobile_4_person.png`: the person only has the mobile_app tracker.
- `../screenshots/unifi_7_devices_after_pick.png` (unifi instance): two "Erik's iPhone" devices,
  one from Mobile App and one from UniFi Network.

To reproduce: see the [README](../README.md).
