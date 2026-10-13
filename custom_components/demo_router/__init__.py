"""Demo router illustrating scanner device tracker behavior.

configuration.yaml:
  demo_router:
    mode: today     # stock ScannerEntity: no device unless the MAC is known elsewhere
    mode: proposed  # scanner creates its own client device (unifi/netgear style)
"""

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType

from .clients import ACCESS_POINTS

DOMAIN = "demo_router"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Create one config entry per access point."""
    mode = config.get(DOMAIN, {}).get("mode", "today")
    for ap, ap_info in ACCESS_POINTS.items():
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data={"ap": ap, "title": ap_info["name"], "mode": mode},
            )
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up an access point."""
    ap_info = ACCESS_POINTS[entry.data["ap"]]
    dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.data["ap"])},
        connections={(dr.CONNECTION_NETWORK_MAC, ap_info["mac"])},
        manufacturer="Demo Networks",
        model=ap_info["model"],
        name=ap_info["name"],
        sw_version="7.62",
    )
    await hass.config_entries.async_forward_entry_setups(
        entry, [Platform.DEVICE_TRACKER]
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an access point."""
    return await hass.config_entries.async_unload_platforms(
        entry, [Platform.DEVICE_TRACKER]
    )
