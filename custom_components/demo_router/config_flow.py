"""Config flow for the demo router."""

from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

DOMAIN = "demo_router"


class DemoRouterConfigFlow(ConfigFlow, domain=DOMAIN):
    """Demo router config flow, entries are only created from YAML."""

    VERSION = 1

    async def async_step_import(self, import_data: dict[str, Any]) -> ConfigFlowResult:
        """Create an entry per access point."""
        await self.async_set_unique_id(import_data["ap"])
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=import_data["title"], data=import_data)
