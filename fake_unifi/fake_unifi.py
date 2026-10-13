"""Minimal fake UniFi Network controller (classic, non UniFi OS) for screenshots.

Serves the demo_router client list so the real unifi integration can be set up:
  python fake_unifi.py   # https://localhost:8443, any username/password

Run it with Home Assistant's Python; it needs aiohttp and cryptography.
"""

import importlib.util
import pathlib
import ssl
import time

from aiohttp import WSMsgType, web

HERE = pathlib.Path(__file__).parent
spec = importlib.util.spec_from_file_location(
    "clients", HERE.parent / "custom_components/demo_router/clients.py"
)
clients_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clients_mod)

SITE = "default"
AP_MACS = {"main": "78:45:58:aa:00:01", "upstairs": "78:45:58:aa:00:02"}
# Names the user gave clients in the UniFi UI
ALIASES = {"5a:1c:93:7e:21:04": "Erik's iPhone", "36:d0:7a:12:6e:b9": "Anna's phone"}

NOW = int(time.time())


def _clients(online_only: bool) -> list[dict]:
    result = []
    for idx, (mac, hostname, vendor, connected, aps) in enumerate(clients_mod.CLIENTS):
        if online_only and not connected:
            continue
        client = {
            "_id": f"client{idx}",
            "mac": mac,
            "ip": f"192.168.1.{100 + idx}",
            "is_wired": False,
            "essid": "Home WiFi",
            "ap_mac": AP_MACS[aps[0]],
            "first_seen": NOW - 86400 * 30,
            "last_seen": NOW if connected else NOW - 7200,
            "uptime": 3600,
            "site_id": "1",
        }
        if hostname:
            client["hostname"] = hostname
        if vendor:
            client["oui"] = vendor.split(",")[0].split(" ")[0]
        if mac in ALIASES:
            client["name"] = ALIASES[mac]
        result.append(client)
    return result


DEVICES = [
    {
        "_id": f"dev_{key}",
        "board_rev": 21,
        "device_id": f"dev_{key}",
        "ip": f"192.168.1.{2 + i}",
        "last_seen": NOW,
        "mac": mac,
        "model": "U6LR",
        "name": name,
        "state": 1,
        "type": "uap",
        "version": "6.6.77",
        "adopted": True,
        "uptime": 864000,
        "wlan_overrides": [],
    }
    for i, (key, mac, name) in enumerate(
        (("main", AP_MACS["main"], "U6 Living room"), ("upstairs", AP_MACS["upstairs"], "U6 Upstairs"))
    )
]

PAYLOADS = {
    "/api/self/sites": [{"desc": "Home", "name": SITE, "role": "admin", "_id": "1"}],
    f"/api/s/{SITE}/stat/sta": lambda: _clients(True),
    f"/api/s/{SITE}/rest/user": lambda: _clients(False),
    f"/api/s/{SITE}/stat/device": DEVICES,
    f"/api/s/{SITE}/rest/wlanconf": [{"_id": "1", "name": "Home WiFi", "enabled": True}],
    f"/api/s/{SITE}/stat/sysinfo": [
        {
            "anonymous_controller_id": "24f81231-a456-4c32-abcd-f5612345385f",
            "build": "atag_8.4.62",
            "hostname": "unifi",
            "name": "UniFi Network",
            "timezone": "Europe/Stockholm",
            "update_available": False,
            "update_downloaded": False,
            "uptime": 1196290,
            "version": "8.4.62",
        }
    ],
}


async def root(request: web.Request) -> web.Response:
    """Not UniFi OS."""
    raise web.HTTPFound("/manage")


async def login(request: web.Request) -> web.Response:
    """Accept any credentials."""
    resp = web.json_response({"data": [], "meta": {"rc": "ok"}})
    resp.set_cookie("unifises", "fake")
    return resp


async def api(request: web.Request) -> web.Response:
    """Serve known payloads, empty lists for everything else."""
    payload = PAYLOADS.get(request.path, [])
    if callable(payload):
        payload = payload()
    if request.path.startswith("/v2/"):
        return web.json_response(payload)
    return web.json_response({"meta": {"rc": "ok"}, "data": payload})


async def websocket(request: web.Request) -> web.WebSocketResponse:
    """Keep the event websocket open, never send events."""
    ws = web.WebSocketResponse(heartbeat=30)
    await ws.prepare(request)
    async for msg in ws:
        if msg.type == WSMsgType.ERROR:
            break
    return ws


def _ensure_cert() -> tuple[pathlib.Path, pathlib.Path]:
    """Create a self-signed localhost cert on first run."""
    cert_dir = HERE / ".cert"
    cert, key = cert_dir / "cert.pem", cert_dir / "key.pem"
    if cert.exists() and key.exists():
        return cert, key
    import datetime  # noqa: PLC0415

    from cryptography import x509  # noqa: PLC0415
    from cryptography.hazmat.primitives import hashes, serialization  # noqa: PLC0415
    from cryptography.hazmat.primitives.asymmetric import rsa  # noqa: PLC0415
    from cryptography.x509.oid import NameOID  # noqa: PLC0415

    cert_dir.mkdir(exist_ok=True)
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    now = datetime.datetime.now(datetime.UTC)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=3650))
        .sign(private_key, hashes.SHA256())
    )
    key.write_bytes(
        private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    cert.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    return cert, key


def main() -> None:
    """Run the server."""
    app = web.Application()
    app.router.add_get("/", root)
    app.router.add_post("/api/login", login)
    app.router.add_get(f"/wss/s/{SITE}/events", websocket)
    app.router.add_route("*", "/api/{tail:.*}", api)
    app.router.add_route("*", "/v2/{tail:.*}", api)
    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ctx.load_cert_chain(*_ensure_cert())
    web.run_app(app, host="127.0.0.1", port=8443, ssl_context=ctx)


if __name__ == "__main__":
    main()
