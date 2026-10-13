"""Set up a freshly started demo instance through Home Assistant's public APIs.

Usage (with Home Assistant's Python, it needs aiohttp):
  python scripts/setup_demo.py today|proposed|unifi
  python scripts/setup_demo.py pick-unifi   # unifi options: track only 3 picked clients

Does, in order:
- onboarding: owner "Erik", login demo / demodemo; country set to avoid a repair issue
- a second user "Anna" (anna / annaanna) with a person
- one mobile_app registration per person, through the same registration and webhook
  API the companion apps use: battery, Wi-Fi SSID and BSSID sensors, location = home
- unifi instance only: the real unifi config flow against fake_unifi on localhost:8443
"""

import asyncio
import sys
from typing import Any

import aiohttp

PORTS = {"today": 8124, "proposed": 8125, "unifi": 8126}
# BSSID the phones report: the MAC of the AP they're connected to
AP_MACS = {
    "today": "02:00:00:aa:00:01",
    "proposed": "02:00:00:aa:00:01",
    "unifi": "78:45:58:aa:00:01",
}
OWNER = {"name": "Erik", "username": "demo", "password": "demodemo"}
ANNA = {"name": "Anna", "username": "anna", "password": "annaanna"}
PHONES = {
    "demo": {
        "device_id": "demo-erik-iphone",
        "app_id": "io.robbie.HomeAssistant",
        "app_name": "Home Assistant",
        "app_version": "2026.9.1",
        "device_name": "Erik's iPhone",
        "manufacturer": "Apple",
        "model": "iPhone16,1",
        "os_name": "iOS",
        "os_version": "26.0",
        "supports_encryption": False,
        "app_data": {},
        "sensors": ("connectivity_ssid", "connectivity_bssid"),
        "battery": 64,
    },
    "anna": {
        "device_id": "demo-anna-galaxy",
        "app_id": "io.homeassistant.companion.android",
        "app_name": "Home Assistant",
        "app_version": "2026.9.2-full",
        "device_name": "Anna's Galaxy S24",
        "manufacturer": "samsung",
        "model": "SM-S921B",
        "os_name": "Android",
        "os_version": "16",
        "supports_encryption": False,
        "app_data": {},
        "sensors": ("wifi_connection", "wifi_bssid"),
        "battery": 81,
    },
}
UNIFI_PICK = {
    "track_clients": False,
    "track_devices": True,
    "block_client": [],
    "more_options": {
        "client_source": ["5a:1c:93:7e:21:04", "36:d0:7a:12:6e:b9", "3c:22:fb:4a:9e:11"]
    },
}


class Instance:
    """One demo Home Assistant instance."""

    def __init__(self, session: aiohttp.ClientSession, port: int) -> None:
        """Initialize."""
        self.session = session
        self.base = f"http://localhost:{port}"
        self.client_id = self.base + "/"

    async def request(
        self, method: str, path: str, token: str | None = None, **kwargs: Any
    ) -> Any:
        """Do a request and return the JSON body."""
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        async with self.session.request(
            method, self.base + path, headers=headers, **kwargs
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def wait_ready(self) -> None:
        """Wait until the HTTP server answers."""
        for _ in range(120):
            try:
                await self.request("GET", "/api/onboarding")
            except aiohttp.ClientError:
                await asyncio.sleep(1)
            else:
                return
        raise SystemExit(f"{self.base} did not come up")

    async def wait_running(self, token: str) -> None:
        """Wait until all integrations are set up; onboarding is served earlier."""
        for _ in range(180):
            if (await self.request("GET", "/api/config", token))["state"] == "RUNNING":
                return
            await asyncio.sleep(1)
        raise SystemExit(f"{self.base} did not finish starting")

    async def token(self, username: str, password: str) -> str:
        """Log in through the login flow."""
        flow = await self.request(
            "POST",
            "/auth/login_flow",
            json={
                "client_id": self.client_id,
                "handler": ["homeassistant", None],
                "redirect_uri": self.client_id,
            },
        )
        result = await self.request(
            "POST",
            f"/auth/login_flow/{flow['flow_id']}",
            json={"client_id": self.client_id, "username": username, "password": password},
        )
        return await self._exchange(result["result"])

    async def _exchange(self, code: str) -> str:
        data = {"grant_type": "authorization_code", "code": code, "client_id": self.client_id}
        return (await self.request("POST", "/auth/token", data=data))["access_token"]

    async def onboard(self) -> str:
        """Run onboarding and return the owner's token."""
        steps = await self.request("GET", "/api/onboarding")
        if any(step["done"] for step in steps):
            raise SystemExit(f"{self.base} is already set up; run scripts/reset.sh first")
        result = await self.request(
            "POST",
            "/api/onboarding/users",
            json={"client_id": self.client_id, "language": "en", **OWNER},
        )
        token = await self._exchange(result["auth_code"])
        await self.request("POST", "/api/onboarding/core_config", token, json={})
        await self.request("POST", "/api/onboarding/analytics", token, json={})
        await self.request(
            "POST",
            "/api/onboarding/integration",
            token,
            json={"client_id": self.client_id, "redirect_uri": self.client_id + "?auth_callback=1"},
        )
        return token

    async def ws(self, token: str, messages: list[dict[str, Any]]) -> list[Any]:
        """Send websocket commands in order, return their results."""
        results = []
        async with self.session.ws_connect(self.base + "/api/websocket") as ws:
            await ws.receive_json()
            await ws.send_json({"type": "auth", "access_token": token})
            assert (await ws.receive_json())["type"] == "auth_ok"
            for msg_id, msg in enumerate(messages, start=1):
                # Later messages may reference earlier results
                msg = {k: v(results) if callable(v) else v for k, v in msg.items()}
                await ws.send_json({"id": msg_id, **msg})
                reply = await ws.receive_json()
                if not reply.get("success"):
                    raise SystemExit(f"{msg['type']} failed: {reply}")
                results.append(reply["result"])
        return results

    async def add_user(self, token: str, user: dict[str, str]) -> None:
        """Create a user with a login and a person."""
        await self.ws(
            token,
            [
                {"type": "config/auth/create", "name": user["name"], "group_ids": ["system-users"]},
                {
                    "type": "config/auth_provider/homeassistant/create",
                    "user_id": lambda r: r[0]["user"]["id"],
                    "username": user["username"],
                    "password": user["password"],
                },
                {"type": "person/create", "name": user["name"], "user_id": lambda r: r[0]["user"]["id"]},
            ],
        )

    async def add_phone(self, token: str, phone: dict[str, Any], bssid: str) -> None:
        """Register a phone like the companion app does."""
        registration = {k: v for k, v in phone.items() if k not in ("sensors", "battery")}
        reg = await self.request("POST", "/api/mobile_app/registrations", token, json=registration)
        hook = f"/api/webhook/{reg['webhook_id']}"
        ssid_id, bssid_id = phone["sensors"]
        sensors = [
            {
                "unique_id": "battery_level",
                "name": "Battery level",
                "state": phone["battery"],
                "type": "sensor",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
                "entity_category": "diagnostic",
            },
            {
                "unique_id": ssid_id,
                "name": "SSID" if phone["os_name"] == "iOS" else "Wi-Fi connection",
                "state": "Home WiFi",
                "type": "sensor",
                "icon": "mdi:wifi",
            },
            {
                "unique_id": bssid_id,
                "name": "BSSID" if phone["os_name"] == "iOS" else "Wi-Fi BSSID",
                "state": bssid,
                "type": "sensor",
                "icon": "mdi:wifi-star",
            },
        ]
        for sensor in sensors:
            await self.request("POST", hook, json={"type": "register_sensor", "data": sensor})
        config = await self.request("GET", "/api/config", token)
        await self.request(
            "POST",
            hook,
            json={
                "type": "update_location",
                "data": {
                    "gps": [config["latitude"], config["longitude"]],
                    "gps_accuracy": 12,
                    "battery": phone["battery"],
                },
            },
        )

    async def add_unifi(self, token: str) -> None:
        """Run the real unifi config flow against the fake controller."""
        flow = await self.request("POST", "/api/config/config_entries/flow", token, json={"handler": "unifi"})
        result = await self.request(
            "POST",
            f"/api/config/config_entries/flow/{flow['flow_id']}",
            token,
            json={
                "host": "localhost",
                "username": "admin",
                "password": "admin",
                "port": 8443,
                "verify_ssl": False,
            },
        )
        if result["type"] != "create_entry":
            raise SystemExit(f"unifi config flow failed: {result}")

    async def unifi_options(self, token: str, options: dict[str, Any]) -> None:
        """Run the real unifi options flow."""
        entries = await self.request("GET", "/api/config/config_entries/entry", token)
        entry = next(e for e in entries if e["domain"] == "unifi")
        flow = await self.request(
            "POST", "/api/config/config_entries/options/flow", token, json={"handler": entry["entry_id"]}
        )
        await self.request("POST", f"/api/config/config_entries/options/flow/{flow['flow_id']}", token, json=options)


async def main(name: str) -> None:
    """Set up one instance."""
    async with aiohttp.ClientSession() as session:
        if name == "pick-unifi":
            inst = Instance(session, PORTS["unifi"])
            await inst.unifi_options(await inst.token(OWNER["username"], OWNER["password"]), UNIFI_PICK)
            print("unifi: picked 3 clients, track clients off")
            return
        inst = Instance(session, PORTS[name])
        await inst.wait_ready()
        owner_token = await inst.onboard()
        await inst.wait_running(owner_token)
        await inst.ws(owner_token, [{"type": "config/core/update", "country": "SE"}])
        await inst.add_user(owner_token, ANNA)
        anna_token = await inst.token(ANNA["username"], ANNA["password"])
        await inst.add_phone(owner_token, PHONES["demo"], AP_MACS[name])
        await inst.add_phone(anna_token, PHONES["anna"], AP_MACS[name])
        if name == "unifi":
            await inst.add_unifi(owner_token)
        print(f"{name}: set up on {inst.base}")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in (*PORTS, "pick-unifi"):
        raise SystemExit(__doc__)
    asyncio.run(main(sys.argv[1]))
