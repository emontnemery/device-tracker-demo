# Router device tracker demo

Demo Home Assistant instances and background research for the discussion about router
(scanner) device trackers: missing devices, client selection, zones per router, and matching
router trackers to phones.

- Problem overview: [docs/device_tracker_issues.md](docs/device_tracker_issues.md)
- What integrations already do for client filtering:
  [docs/filtering_overview.md](docs/filtering_overview.md), with the full per-integration survey
  in [docs/client_selection_survey/](docs/client_selection_survey/)
- Zone settings per router in core and custom integrations:
  [docs/zone_survey/report.md](docs/zone_survey/report.md)
- Screenshots: [screenshots/](screenshots/), listed at the end of the problem overview

## The instances

| Instance | URL | What it shows |
|---|---|---|
| today | http://localhost:8124 | `demo_router` with stock `ScannerEntity`: no client devices, most trackers disabled |
| proposed | http://localhost:8125 | `demo_router` where each scanner tracker creates its own client device (unifi/netgear style) |
| unifi | http://localhost:8126 | The real core unifi integration against a fake UniFi controller, to try its client picker |

Logins: `demo` / `demodemo` (owner, person "Erik") and `anna` / `annaanna` (person "Anna").

All three instances also have two phones set up through the real mobile_app integration:
"Erik's iPhone" and "Anna's Galaxy S24". Each is on its own person, at home, with battery,
SSID and BSSID sensors. They aren't linked to the router's trackers for the same phones; that
missing link is one of the gaps.

No core integration is modified:

- `custom_components/demo_router`: a made-up router with a "Main router" and an "Upstairs
  access point" entry and 20 clients (`clients.py`). Phones and tablets have randomized MACs,
  and most have no hostname. `mode: today` is the stock `ScannerEntity`. `mode: proposed`
  overrides its `@final` `device_info` to simulate the proposed change: a device with
  `connections={MAC}`, the vendor from the MAC prefix as manufacturer, and the AP as parent
  device.
- `custom_components/demo_plug`: a Shelly-like plug whose device has its Wi-Fi MAC, so the today
  instance shows what happens when another integration knows a client's MAC.
- unifi: the unmodified core integration, pointed at `fake_unifi/fake_unifi.py`. That's a classic
  (non UniFi OS) controller on `https://localhost:8443` that accepts any login. It serves the same
  20 clients, two U6 APs and one WLAN. Two clients have UniFi aliases. The self-signed cert is
  created on first start in `fake_unifi/.cert/`.
- mobile_app: the unmodified core integration. `scripts/setup_demo.py` registers the phones
  through the same registration and webhook API the companion apps use.

## Requirements

- A Home Assistant core **dev** checkout with its virtualenv set up (`script/setup`). Tested on
  dev @ `aafdfa9d12c` (2026.11.0.dev0, 2026-10-12). The demo relies on recent dev features, like
  the per-entity tracker zone option and `via_device_id`, so older versions won't work.
- For screenshots only: Playwright, in any Python:
  `pip install playwright && playwright install chromium`.

## Running

```bash
export HASS_PYTHON=/path/to/core/.venv/bin/python
scripts/start.sh    # starts the fake controller and the 3 instances; sets up fresh ones
scripts/stop.sh
scripts/reset.sh    # deletes all instance state (run stop.sh first); start.sh sets it up again
```

The first start takes a minute or two. Logs are in `instances/<name>/run.log` and
`fake_unifi/run.log`. Each instance keeps its state under `instances/<name>/`, which git ignores.

Things to try:

- **today**: Settings → Entities, search `device_tracker`. Only one of the 25 router trackers is
  visible, next to the two phones; the other 24 are disabled. Enable a few and see that they have
  no device.
- **proposed**: Settings → Devices. There's one device per client per AP, and phones have no
  manufacturer. Compare "Erik's iPhone" (Mobile App) with `5a:1c:93:7e:21:04` (Demo router):
  that's the same phone.
- **unifi**: Settings → Devices & services → UniFi Network → Configure → More options →
  "Create entities from network clients". Turn off "Track network clients", pick a few clients,
  then wait about 30 seconds: the registry reloads the entry to enable the picked trackers.
  `"$HASS_PYTHON" scripts/setup_demo.py pick-unifi` does the same pick through the API.
- **Zones**: open any router tracker → Settings for its "Associated zone". The router device's
  settings have no zone.

Each instance always shows one repair issue, `deprecated_method`, because Home Assistant runs
from a virtualenv. The logs also show errors for Bluetooth, libpcap and libturbojpeg, which come
from the environment and can be ignored.

The ports are written to `.storage/http` before the first start, not set with `http:` in YAML.
YAML port settings are deprecated and would show a "Confirm new HTTP server configuration"
dialog on every fresh start.

## Screenshots

```bash
python scripts/screenshots.py            # all stages: today proposed zone mobile unifi
python scripts/screenshots.py mobile     # or just some
```

The stages change the instances on purpose: today enables every router tracker, and unifi picks
three clients. Run `scripts/stop.sh && scripts/reset.sh && scripts/start.sh` afterwards to get
the fresh state back.
