from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .ble_client import LinkPowerClient
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    address = entry.data[CONF_ADDRESS]
    name = entry.data.get(CONF_NAME, "LinkPower Battery")
    client = LinkPowerClient(address)

    async def update():
        return await client.read_once()

    coordinator = DataUpdateCoordinator(hass, None, name=f"{name} binary coordinator", update_method=update)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([
        LinkPowerBinarySensor(coordinator, entry, name, "dc_output", "DC Output"),
        LinkPowerBinarySensor(coordinator, entry, name, "typec_active", "Type-C Active"),
    ])

class LinkPowerBinarySensor(BinarySensorEntity):
    def __init__(self, coordinator, entry, devname, key, label):
        self.coordinator = coordinator
        self._key = key
        self._attr_name = f"{devname} {label}"
        self._attr_unique_id = f"{entry.unique_id}_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.unique_id)},
            "name": devname,
            "manufacturer": "PeakDo / LinkPower",
        }

    @property
    def is_on(self):
        return getattr(self.coordinator.data, self._key, None)

    async def async_update(self):
        await self.coordinator.async_request_refresh()
