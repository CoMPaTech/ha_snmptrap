"""SNMP Trap Configuration flow."""

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from . import DOMAIN


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Minimal config flow for SNMP Trap Listener."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        await self.async_set_unique_id("snmptrap_singleton")
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title="SNMP Trap Listener",
            data={},  # nothing to store
        )

