"""Sensor platform for LinkPower Battery."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEVICE_NAME, DOMAIN, MANUFACTURER
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
            LinkPowerValueSensor(coordinator, entry, "charge_state", "Charge State"),
            LinkPowerValueSensor(coordinator, entry, "raw_ext_info", "Ext Info Raw"),
            LinkPowerValueSensor(coordinator, entry, "raw_dc_port", "DC Port Raw"),
            LinkPowerValueSensor(coordinator, entry, "raw_typec_port", "Type-C Port Raw"),
            LinkPowerValueSensor(coordinator, entry, "ext_info_diff", "Ext Info Diff"),
            LinkPowerValueSensor(coordinator, entry, "dc_port_diff", "DC Port Diff"),
            LinkPowerValueSensor(coordinator, entry, "typec_port_diff", "Type-C Port Diff"),
            LinkPowerValueSensor(coordinator, entry, "ext_status_byte", "Ext Status Byte"),
            LinkPowerValueSensor(coordinator, entry, "dc_status_byte", "DC Status Byte"),
            LinkPowerValueSensor(coordinator, entry, "typec_status_byte", "Type-C Status Byte"),
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
    """Battery percentage."""

    _attr_name = "LinkPower Battery"
    _attr_unique_id = "linkpower_battery"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.BATTERY

    @property
    def native_value(self):
        """Return battery percentage."""
        return (self.coordinator.data or {}).get("battery")


class LinkPowerValueSensor(LinkPowerBaseSensor):
    """Generic LinkPower value sensor."""

    def __init__(
        self,
        coordinator: LinkPowerCoordinator,
        entry: ConfigEntry,
        key: str,
        name: str,
    ) -> None:
        """Initialize value sensor."""
        super().__init__(coordinator, entry)
        self._key = key
        self._attr_name = f"LinkPower {name}"
        self._attr_unique_id = f"linkpower_{key}"

        if key.startswith("raw_") or key.endswith("_byte") or key.endswith("_diff"):
            self._attr_entity_registry_enabled_default = False

    @property
    def native_value(self):
        """Return sensor value."""
        return (self.coordinator.data or {}).get(self._key)

    @property
    def extra_state_attributes(self):
        """Return byte attributes for raw packet sensors."""
        value = (self.coordinator.data or {}).get(self._key)

        if not isinstance(value, str) or "-" not in value:
            return None

        parts = value.split("-")
        return {f"byte_{index}": byte for index, byte in enumerate(parts)}
