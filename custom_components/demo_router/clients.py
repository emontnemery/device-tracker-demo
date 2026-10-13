"""Fake network clients.

Phones use per-network randomized ("private") MACs and typically report no hostname.
"""

ACCESS_POINTS = {
    "main": {"name": "Main router", "model": "DR-6000", "mac": "02:00:00:aa:00:01"},
    "upstairs": {
        "name": "Upstairs access point",
        "model": "DR-AP2",
        "mac": "02:00:00:aa:00:02",
    },
}

# mac, hostname, vendor (from OUI, None for randomized MACs), connected, access points
CLIENTS: list[tuple[str, str | None, str | None, bool, tuple[str, ...]]] = [
    ("5a:1c:93:7e:21:04", None, None, True, ("main", "upstairs")),
    ("ae:62:0b:d4:9f:3a", None, None, True, ("main", "upstairs")),
    ("e6:3b:51:88:0c:7d", None, None, False, ("main",)),
    ("36:d0:7a:12:6e:b9", "Galaxy-S24", None, True, ("main", "upstairs")),
    ("fa:9e:44:c1:3d:20", "android-5c7e1a9f3b2d", None, False, ("main",)),
    ("3c:22:fb:4a:9e:11", "MacBook-Pro", "Apple, Inc.", True, ("main", "upstairs")),
    ("9c:b6:d0:7f:31:c2", "LAPTOP-7F3K2Q1", "Intel Corporate", True, ("upstairs",)),
    ("e8:68:e7:3a:1f:2c", "shellyplug-s-3A1F2C", "Espressif Inc.", True, ("main",)),
    ("24:6f:28:9b:4d:17", "ESP_9B4D17", "Espressif Inc.", True, ("main",)),
    ("f0:27:2d:4b:2c:1f", "amazon-4b2c1f8a9", "Amazon Technologies Inc.", True, ("main",)),
    ("8c:79:f5:61:0a:e3", "Living-Room-TV", "Samsung Electronics Co.,Ltd", True, ("main",)),
    ("54:60:09:c3:77:58", "Chromecast", "Google, Inc.", True, ("main",)),
    ("a0:d3:c1:4a:2b:1c", "HP4A2B1C", "Hewlett Packard", False, ("upstairs",)),
    ("b8:27:eb:0e:55:9a", "raspberrypi", "Raspberry Pi Foundation", True, ("main",)),
    ("d8:1f:12:3e:a7:60", None, "Tuya Smart Inc.", True, ("main",)),
    ("98:b6:e9:5d:02:4f", "NINTENDO-SWITCH", "Nintendo Co.,Ltd", False, ("upstairs",)),
    ("50:ec:50:a1:b2:c3", "roborock-vacuum-s7_miapB2C3", "Beijing Roborock Technology Co., Ltd.", True, ("main",)),
    ("00:17:88:6d:4e:19", "Philips-hue", "Signify Netherlands B.V.", True, ("main",)),
    ("00:24:e4:72:8a:05", "WBS-05", "Withings", True, ("upstairs",)),
    ("6e:85:2f:b0:4c:93", None, None, False, ("main", "upstairs")),
]
