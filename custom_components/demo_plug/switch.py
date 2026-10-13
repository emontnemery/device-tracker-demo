"""Demo plug switch."""

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the plug switch."""
    async_add_entities([DemoPlug()])


class DemoPlug(SwitchEntity):
    """Plug relay."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_should_poll = False
    _attr_unique_id = "e8:68:e7:3a:1f:2c"
    _attr_is_on = True
    _attr_device_info = DeviceInfo(
        identifiers={("demo_plug", "e8:68:e7:3a:1f:2c")},
        connections={(CONNECTION_NETWORK_MAC, "e8:68:e7:3a:1f:2c")},
        manufacturer="Shelly",
        model="Plug S",
        name="Kitchen plug",
    )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on."""
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off."""
        self._attr_is_on = False
        self.async_write_ha_state()
