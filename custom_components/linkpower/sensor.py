from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import PERCENTAGE, CONF_ADDRESS, CONF_NAME
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

    coordinator = DataUpdateCoordinator(hass, None, name=f"{name} coordinator", update_method=update)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([
        LinkPowerSensor(coordinator, entry, name, "battery", "Battery", PERCENTAGE, SensorDeviceClass.BATTERY),
        LinkPowerSensor(coordinator, entry, name, "status", "Status"),
        LinkPowerSensor(coordinator, entry, name, "raw_4303", "Raw 4303"),
        LinkPowerSensor(coordinator, entry, name, "raw_4304", "Raw DC Port"),
        LinkPowerSensor(coordinator, entry, name, "raw_4305", "Raw Type-C Port"),
    ])

class LinkPowerSensor(SensorEntity):
    def __init__(self, coordinator, entry, devname, key, label, unit=None, device_class=None):
        self.coordinator = coordinator
        self._key = key
        self._attr_name = f"{devname} {label}"
        self._attr_unique_id = f"{entry.unique_id}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.unique_id)},
            "name": devname,
            "manufacturer": "PeakDo / LinkPower",
        }

    @property
    def native_value(self):
        return getattr(self.coordinator.data, self._key, None)

    async def async_update(self):
        await self.coordinator.async_request_refresh()
