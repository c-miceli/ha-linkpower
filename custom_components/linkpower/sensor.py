"""Sensor platform for LinkPower Battery."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, DEVICE_NAME, MANUFACTURER
from .coordinator import LinkPowerCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LinkPower sensors."""
    coordinator: LinkPowerCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            LinkPowerBatterySensor(coordinator, entry),
            LinkPowerRawSensor(coordinator, entry, "raw_ext_info", "Ext Info Raw"),
            LinkPowerRawSensor(coordinator, entry, "raw_dc_port", "DC Port Raw"),
            LinkPowerRawSensor(coordinator, entry, "raw_typec_port", "Type-C Port Raw"),
        ]
    )


class LinkPowerBaseSensor(CoordinatorEntity, SensorEntity):
    """Base LinkPower sensor."""

    def __init__(self, coordinator: LinkPowerCoordinator, entry: ConfigEntry) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._entry.unique_id or self._entry.entry_id)},
            "name": DEVICE_NAME,
            "manufacturer": MANUFACTURER,
            "model": "LinkPower 1",
        }


class LinkPowerBatterySensor(LinkPowerBaseSensor):
    """Battery percentage sensor."""

    _attr_name = "LinkPower Battery"
    _attr_unique_id = "linkpower_battery"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.BATTERY

    @property
    def native_value(self):
        """Return battery percentage."""
        return self.coordinator.data.get("battery")


class LinkPowerRawSensor(LinkPowerBaseSensor):
    """Raw telemetry sensor."""

    def __init__(
        self,
        coordinator: LinkPowerCoordinator,
        entry: ConfigEntry,
        key: str,
        name: str,
    ) -> None:
        """Initialize raw sensor."""
        super().__init__(coordinator, entry)
        self._key = key
        self._attr_name = f"LinkPower {name}"
        self._attr_unique_id = f"linkpower_{key}"

    @property
    def native_value(self):
        """Return raw telemetry."""
        return self.coordinator.data.get(self._key)
