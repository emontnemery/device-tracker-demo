"""Config flow for the demo plug."""

from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult


class DemoPlugConfigFlow(ConfigFlow, domain="demo_plug"):
    """Demo plug config flow, entries are only created from YAML."""

    VERSION = 1

    async def async_step_import(self, import_data: dict[str, Any]) -> ConfigFlowResult:
        """Create the entry."""
        await self.async_set_unique_id("e8:68:e7:3a:1f:2c")
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title="Kitchen plug", data={})
