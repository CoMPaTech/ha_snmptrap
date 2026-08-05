"""SNMP Trap Configuration flow."""

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from . import DOMAIN


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Minimal config flow for SNMP Trap Listener."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        return self.async_create_entry(
            title="SNMP Trap Listener",
            data={},  # nothing to store
        )

