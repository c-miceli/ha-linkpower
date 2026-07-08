"""Binary sensor platform for LinkPower Battery."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
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
    """Set up LinkPower binary sensors."""
    coordinator: LinkPowerCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            LinkPowerDcOutputSensor(coordinator, entry),
            LinkPowerTypeCActiveSensor(coordinator, entry),
        ]
    )


class LinkPowerBaseBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Base LinkPower binary sensor."""

    def __init__(self, coordinator: LinkPowerCoordinator, entry: ConfigEntry) -> None:
        """Initialize binary sensor."""
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


class LinkPowerDcOutputSensor(LinkPowerBaseBinarySensor):
    """DC output status."""

    _attr_name = "LinkPower DC Output"
    _attr_unique_id = "linkpower_dc_output"

    @property
    def is_on(self) -> bool | None:
        """Return true if DC output appears active."""
        raw = self.coordinator.data.get("raw_dc_port")
        if not raw:
            return None

        parts = raw.split("-")
        return parts[0] == "01"


class LinkPowerTypeCActiveSensor(LinkPowerBaseBinarySensor):
    """Type-C port status."""

    _attr_name = "LinkPower Type-C Active"
    _attr_unique_id = "linkpower_typec_active"

    @property
    def is_on(self) -> bool | None:
        """Return true if Type-C appears active."""
        raw = self.coordinator.data.get("raw_typec_port")
        if not raw:
            return None

        parts = raw.split("-")
        return parts[0] == "01"
