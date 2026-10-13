"""Scanner device trackers for the demo router."""

from homeassistant.components.device_tracker import ScannerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .clients import CLIENTS

DOMAIN = "demo_router"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add one tracker per client seen by this access point."""
    ap = entry.data["ap"]
    ap_device_id = dr.async_get_device_id_by_identifier(
        hass, (DOMAIN, ap), config_entry_id=entry.entry_id
    )
    cls = ProposedScanner if entry.data["mode"] == "proposed" else TodayScanner
    async_add_entities(
        cls(ap, ap_device_id, mac, hostname, vendor, connected, idx)
        for idx, (mac, hostname, vendor, connected, aps) in enumerate(CLIENTS)
        if ap in aps
    )


class TodayScanner(ScannerEntity):
    """Stock ScannerEntity, named like fritz/asuswrt do (hostname, else MAC)."""

    _attr_should_poll = False

    def __init__(
        self,
        ap: str,
        ap_device_id: str,
        mac: str,
        hostname: str | None,
        vendor: str | None,
        connected: bool,
        idx: int,
    ) -> None:
        """Initialize."""
        self._ap_device_id = ap_device_id
        self._vendor = vendor
        self._connected = connected
        self._attr_mac_address = mac
        self._attr_hostname = hostname
        self._attr_ip_address = f"192.168.1.{100 + idx}"
        self._attr_unique_id = f"{ap}_{mac}"
        self._attr_name = hostname or mac

    @property
    def unique_id(self) -> str:
        """Per access point, like integrations with several entries do."""
        return self._attr_unique_id

    @property
    def is_connected(self) -> bool:
        """Return if connected."""
        return self._connected


class ProposedScanner(TodayScanner):
    """Scanner which creates its own client device, like unifi/netgear clients."""

    _attr_has_entity_name = True

    def __init__(self, *args) -> None:
        """Initialize."""
        super().__init__(*args)
        self._attr_name = None

    @property
    def device_info(self) -> DeviceInfo:  # overrides ScannerEntity's @final None
        """Client device, attached to the access point."""
        return DeviceInfo(
            connections={(CONNECTION_NETWORK_MAC, self._attr_mac_address)},
            manufacturer=self._vendor,
            name=self._attr_hostname or self._attr_mac_address,
            via_device_id=self._ap_device_id,
        )
