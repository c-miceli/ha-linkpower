"""Coordinator for LinkPower Battery."""

from __future__ import annotations

import logging
from datetime import timedelta

from bleak import BleakClient
from bleak_retry_connector import establish_connection

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DEVICE_NAME,
    DOMAIN,
    UUID_BATTERY,
    UUID_DC_PORT,
    UUID_EXT_INFO,
    UUID_TYPEC_PORT,
)

_LOGGER = logging.getLogger(__name__)


def _hex(data: bytes) -> str:
    """Return hex string for BLE data."""
    return "-".join(f"{byte:02X}" for byte in data)


class LinkPowerCoordinator(DataUpdateCoordinator):
    """Coordinator for LinkPower Battery."""

    def __init__(self, hass: HomeAssistant, address: str | None = None) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=60),
        )
        self.address = address
        self.name = DEVICE_NAME

    async def _async_find_device(self):
        """Find the battery using Home Assistant Bluetooth."""
        if self.address:
            service_info = bluetooth.async_ble_device_from_address(
                self.hass,
                self.address,
                connectable=True,
            )
            if service_info:
                return service_info

        scanner = bluetooth.async_get_scanner(self.hass)
        devices = await scanner.discover(timeout=10)

        for device in devices:
            if device.name == DEVICE_NAME:
                self.address = device.address
                return device

        return None

    async def _async_update_data(self) -> dict:
        """Fetch data from the battery."""
        device = await self._async_find_device()

        if device is None:
            raise RuntimeError("LinkPower battery not found")

        client = await establish_connection(
            BleakClient,
            device,
            DEVICE_NAME,
        )

        try:
            battery = await client.read_gatt_char(UUID_BATTERY)
            ext_info = await client.read_gatt_char(UUID_EXT_INFO)
            dc_port = await client.read_gatt_char(UUID_DC_PORT)
            typec_port = await client.read_gatt_char(UUID_TYPEC_PORT)

            return {
                "battery": battery[0],
                "raw_ext_info": _hex(ext_info),
                "raw_dc_port": _hex(dc_port),
                "raw_typec_port": _hex(typec_port),
            }
        finally:
            await client.disconnect()
