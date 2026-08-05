"""SNMP Trap Sensor."""

from homeassistant.helpers.entity import Entity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from . import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, add_entities):
    add_entities([LastTrapSensor(hass)], True)


class LastTrapSensor(Entity):
    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self._attr_name = "SNMP Last Trap"
        self._attr_unique_id = "snmptrap_last_trap"
        self._state = None
        self._attrs = {}

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attrs

    async def async_update(self):
        data = self.hass.data.get(DOMAIN, {}).get("last_trap")
        if not data:
            self._state = None
            self._attrs = {}
            return

        kv = data.get("kv", {})
        if kv:
            trap_oid = next(iter(kv))
            val = kv[trap_oid]
            if isinstance(val, list):
                self._state = val[0]
            else:
                self._state = val
        else:
            self._state = data.get("raw_string", "")

        self._attrs = data

