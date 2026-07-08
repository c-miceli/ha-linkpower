from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, DEVICE_NAME

class LinkPowerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_bluetooth(self, discovery_info) -> FlowResult:
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        self.context["title_placeholders"] = {"name": discovery_info.name or DEVICE_NAME}
        return await self.async_step_user({CONF_ADDRESS: discovery_info.address, CONF_NAME: discovery_info.name or DEVICE_NAME})

    async def async_step_user(self, user_input=None) -> FlowResult:
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_ADDRESS])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input.get(CONF_NAME, DEVICE_NAME), data=user_input)

        devices = bluetooth.async_discovered_service_info(self.hass)
        choices = {
            d.address: f"{d.name or 'Unknown'} ({d.address})"
            for d in devices
            if (d.name or "") == DEVICE_NAME
        }
        schema = vol.Schema({
            vol.Required(CONF_ADDRESS): vol.In(choices or {"C8:17:F5:E0:C9:12": "Link-Power-1 (manual)"}),
            vol.Optional(CONF_NAME, default=DEVICE_NAME): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema)
