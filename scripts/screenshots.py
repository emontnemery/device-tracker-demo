"""Take the screenshots in screenshots/ from the running demo instances.

Needs Playwright (any Python):
  pip install playwright && playwright install chromium
  python scripts/screenshots.py [stage ...]

Stages: today, proposed, zone, mobile, unifi. Default: all. The stages change the
instances on purpose (today enables every router tracker, unifi picks 3 clients), so
run scripts/reset.sh afterwards to get the fresh state back.
"""

import pathlib
import re
import sys

from playwright.sync_api import Page, sync_playwright

OUT = pathlib.Path(__file__).resolve().parent.parent / "screenshots"
TODAY, PROPOSED, UNIFI = 8124, 8125, 8126
UNIFI_PICK = {
    "track_clients": False,
    "track_devices": True,
    "block_client": [],
    "more_options": {
        "client_source": ["5a:1c:93:7e:21:04", "36:d0:7a:12:6e:b9", "3c:22:fb:4a:9e:11"]
    },
}


def login(page: Page, port: int) -> None:
    """Log in as the owner and dismiss the HTTP config confirmation."""
    page.goto(f"http://localhost:{port}/")
    page.wait_for_selector("input[name=username]", timeout=30000)
    page.fill("input[name=username]", "demo")
    page.fill("input[name=password]", "demodemo")
    page.keyboard.press("Enter")
    page.wait_for_selector("home-assistant", timeout=30000)
    page.wait_for_timeout(4000)
    confirm = page.get_by_role("button", name="Confirm")
    if confirm.count():
        confirm.first.click()
        page.wait_for_timeout(1000)


def shot(page: Page, name: str) -> None:
    """Save a screenshot."""
    page.screenshot(path=OUT / f"{name}.png")
    print("saved", name)


def nav(page: Page, port: int, path: str, name: str, search: str | None = None) -> None:
    """Open a page, optionally type into its search box, and screenshot it."""
    page.goto(f"http://localhost:{port}{path}")
    page.wait_for_timeout(3500)
    if search:
        page.get_by_placeholder(re.compile(r"^Search \d+")).locator("visible=true").first.fill(search)
        page.wait_for_timeout(1500)
    shot(page, name)


def ws(page: Page, msg: dict) -> object:
    """Send a websocket command through the frontend's connection."""
    return page.evaluate("m => document.querySelector('home-assistant').hass.callWS(m)", msg)


def api(page: Page, path: str, data: dict) -> object:
    """POST to the REST API through the frontend's connection."""
    return page.evaluate(
        "([p, d]) => document.querySelector('home-assistant').hass.callApi('POST', p, d)",
        [path, data],
    )


def device_ids(page: Page, name: str) -> list[str]:
    """Return the ids of all devices with this name."""
    return [d["id"] for d in ws(page, {"type": "config/device_registry/list"}) if d["name"] == name]


def slug(name: str) -> str:
    """Make a file-name friendly version of a device name."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def today(page: Page) -> None:
    """Stock ScannerEntity."""
    login(page, TODAY)
    nav(page, TODAY, "/config/integrations/integration/demo_router", "today_1_integration")
    nav(page, TODAY, "/config/entities", "today_2_entities_default", search="device_tracker")
    # Simulate the user enabling every router tracker
    for entry in ws(page, {"type": "config/entity_registry/list"}):
        if entry["platform"] == "demo_router" and entry["disabled_by"]:
            ws(page, {"type": "config/entity_registry/update", "entity_id": entry["entity_id"], "disabled_by": None})
    for entry in ws(page, {"type": "config_entries/get", "domain": "demo_router"}):
        api(page, f"config/config_entries/entry/{entry['entry_id']}/reload", {})
    page.wait_for_timeout(4000)
    nav(page, TODAY, "/config/entities", "today_3_entities_enabled", search="device_tracker")
    for name in ("Kitchen plug", "shellyplug-s-3A1F2C"):
        nav(page, TODAY, f"/config/devices/device/{device_ids(page, name)[0]}", f"today_4_device_{slug(name)}")


def proposed(page: Page) -> None:
    """Scanner creates its own client device."""
    login(page, PROPOSED)
    nav(page, PROPOSED, "/config/integrations/integration/demo_router", "proposed_1_integration")
    nav(page, PROPOSED, "/config/devices/dashboard?domain=demo_router", "proposed_2_devices")
    nav(page, PROPOSED, "/config/entities", "proposed_3_entities", search="device_tracker")
    nav(page, PROPOSED, f"/config/devices/device/{device_ids(page, 'Main router')[0]}", "proposed_4_device_main_router")
    phone = device_ids(page, "5a:1c:93:7e:21:04")
    nav(page, PROPOSED, f"/config/devices/device/{phone[0]}", "proposed_4_device_5a1c937e2104")


def zone(page: Page) -> None:
    """Per-entity zone option vs. nothing on the router device."""
    login(page, PROPOSED)
    page.goto(f"http://localhost:{PROPOSED}/config/entities")
    page.wait_for_timeout(3000)
    page.get_by_placeholder(re.compile(r"^Search \d+")).locator("visible=true").first.fill("galaxy-s24")
    page.wait_for_timeout(1500)
    page.get_by_text("Galaxy-S24").nth(1).click()
    page.wait_for_timeout(2500)
    page.get_by_role("button", name=re.compile("Settings", re.I)).first.click()
    page.wait_for_timeout(2500)
    shot(page, "zone_1_entity_settings")
    page.goto(f"http://localhost:{PROPOSED}/config/devices/device/{device_ids(page, 'Upstairs access point')[0]}")
    page.wait_for_timeout(3000)
    page.get_by_role("button", name=re.compile("Edit", re.I)).first.click()
    page.wait_for_timeout(2000)
    shot(page, "zone_3_router_device_settings")


def mobile(page: Page) -> None:
    """mobile_app phones next to the router's view of the same phones."""
    login(page, PROPOSED)
    nav(page, PROPOSED, f"/config/devices/device/{device_ids(page, "Erik's iPhone")[0]}", "mobile_1_app_device")
    nav(page, PROPOSED, "/config/devices/dashboard", "mobile_2_devices_both_views")
    nav(page, PROPOSED, "/config/entities", "mobile_3_trackers_both_views", search="device_tracker")
    page.goto(f"http://localhost:{PROPOSED}/config/person")
    page.wait_for_timeout(3000)
    page.get_by_text("Erik", exact=True).last.click()
    page.wait_for_timeout(2000)
    shot(page, "mobile_4_person")


def unifi(page: Page) -> None:
    """The real unifi options flow, before and after picking clients."""
    login(page, UNIFI)
    nav(page, UNIFI, "/config/integrations/integration/unifi", "unifi_1_integration")
    nav(page, UNIFI, "/config/entities", "unifi_2_entities_default", search="device_tracker")
    page.goto(f"http://localhost:{UNIFI}/config/integrations/integration/unifi")
    page.wait_for_timeout(3000)
    page.get_by_role("button", name=re.compile("Configure|Options", re.I)).first.click()
    page.wait_for_timeout(2500)
    shot(page, "unifi_3_options")
    page.get_by_text("More options").first.click()
    page.wait_for_timeout(1500)
    shot(page, "unifi_4_options_expanded")
    picker = page.get_by_text("Create entities from network clients").first
    picker.scroll_into_view_if_needed()
    page.wait_for_timeout(500)
    shot(page, "unifi_4b_options_expanded_scrolled")
    picker.click()
    page.wait_for_timeout(1500)
    shot(page, "unifi_5_client_picker")
    page.keyboard.press("Escape")
    entry = ws(page, {"type": "config_entries/get", "domain": "unifi"})[0]
    flow = api(page, "config/config_entries/options/flow", {"handler": entry["entry_id"]})
    api(page, f"config/config_entries/options/flow/{flow['flow_id']}", UNIFI_PICK)
    # Picked clients' trackers are enabled by the registry, which reloads the entry after 30 s
    page.wait_for_timeout(45000)
    nav(page, UNIFI, "/config/entities", "unifi_6_entities_after_pick", search="device_tracker")
    nav(page, UNIFI, "/config/devices/dashboard", "unifi_7_devices_after_pick")


STAGES = {"today": today, "proposed": proposed, "zone": zone, "mobile": mobile, "unifi": unifi}

if __name__ == "__main__":
    selected = sys.argv[1:] or list(STAGES)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for stage in selected:
            STAGES[stage](browser.new_page(viewport={"width": 1440, "height": 1000}))
        browser.close()
