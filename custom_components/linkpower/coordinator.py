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
    UUID_BATTERY,
    UUID_DC_PORT,
    UUID_EXT_INFO,
    UUID_TYPEC_PORT,
)
from .decoder import decode_packets, hex_bytes
from .diagnostics import packet_diff

_LOGGER = logging.getLogger(__name__)


class LinkPowerCoordinator(DataUpdateCoordinator):
    """Coordinator for LinkPower Battery."""

    def __init__(self, hass: HomeAssistant, address: str | None = None) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DEVICE_NAME,
            update_interval=timedelta(minutes=5),
        )
        self.address = address
        self._previous_ext_info: str | None = None
        self._previous_dc_port: str | None = None
        self._previous_typec_port: str | None = None

    async def _async_find_device(self):
        """Find the battery using Home Assistant Bluetooth."""
        if self.address:
            device = bluetooth.async_ble_device_from_address(
                self.hass,
                self.address,
                connectable=True,
            )
            if device:
                return device

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
            battery_data = await client.read_gatt_char(UUID_BATTERY)
            ext_info = await client.read_gatt_char(UUID_EXT_INFO)
            dc_port = await client.read_gatt_char(UUID_DC_PORT)
            typec_port = await client.read_gatt_char(UUID_TYPEC_PORT)

            raw_ext_info = hex_bytes(ext_info)
            raw_dc_port = hex_bytes(dc_port)
            raw_typec_port = hex_bytes(typec_port)

            decoded = decode_packets(
                battery=battery_data[0],
                raw_ext_info=raw_ext_info,
                raw_dc_port=raw_dc_port,
                raw_typec_port=raw_typec_port,
            )

            decoded["ext_info_diff"] = packet_diff(
                self._previous_ext_info,
                raw_ext_info,
            )
            decoded["dc_port_diff"] = packet_diff(
                self._previous_dc_port,
                raw_dc_port,
            )
            decoded["typec_port_diff"] = packet_diff(
                self._previous_typec_port,
                raw_typec_port,
            )

            self._previous_ext_info = raw_ext_info
            self._previous_dc_port = raw_dc_port
            self._previous_typec_port = raw_typec_port

            return decoded

        finally:
            await client.disconnect()
