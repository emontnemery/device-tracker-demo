"""A Shelly-like plug whose device carries its WiFi MAC, so router trackers can find it."""

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Create the config entry."""
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            "demo_plug", context={"source": SOURCE_IMPORT}, data={}
        )
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the plug."""
    await hass.config_entries.async_forward_entry_setups(entry, [Platform.SWITCH])
    return True
