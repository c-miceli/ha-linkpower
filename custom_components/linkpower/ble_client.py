from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Callable

from bleak import BleakClient

from .const import (
    UUID_BATTERY,
    UUID_EXT_INFO,
    UUID_DC_PORT,
    UUID_TYPEC_PORT,
    UUID_MODEL,
    UUID_FIRMWARE,
    UUID_MANUFACTURER,
)


def hexify(data: bytes | bytearray | None) -> str:
    if not data:
        return ""
    return "-".join(f"{b:02X}" for b in data)


@dataclass
class LinkPowerData:
    battery: int | None = None
    raw_4303: str | None = None
    raw_4304: str | None = None
    raw_4305: str | None = None
    status: str | None = None
    dc_output: bool | None = None
    typec_active: bool | None = None
    model: str | None = None
    firmware: str | None = None
    manufacturer: str | None = None


class LinkPowerClient:
    def __init__(self, address: str, callback: Callable[[LinkPowerData], None] | None = None) -> None:
        self.address = address
        self.callback = callback
        self.data = LinkPowerData()
        self._client: BleakClient | None = None

    def _decode_4303_status(self, data: bytes | bytearray) -> str | None:
        if len(data) < 2:
            return None
        # Based on Chandler's captured logs:
        # FF appeared during output/discharge, 01 while plugged in/charging, 00 during idle/transition.
        return {0xFF: "discharging", 0x01: "charging", 0x00: "idle"}.get(data[1], f"unknown_{data[1]:02X}")

    def _update_4303(self, data: bytes | bytearray) -> None:
        self.data.raw_4303 = hexify(data)
        self.data.status = self._decode_4303_status(data)
        if self.callback:
            self.callback(self.data)

    async def read_once(self) -> LinkPowerData:
        async with BleakClient(self.address) as client:
            self._client = client
            self.data.battery = (await client.read_gatt_char(UUID_BATTERY))[0]
            self.data.raw_4303 = hexify(await client.read_gatt_char(UUID_EXT_INFO))
            self.data.raw_4304 = hexify(await client.read_gatt_char(UUID_DC_PORT))
            self.data.raw_4305 = hexify(await client.read_gatt_char(UUID_TYPEC_PORT))
            try:
                self.data.model = bytes(await client.read_gatt_char(UUID_MODEL)).decode(errors="ignore")
                self.data.firmware = bytes(await client.read_gatt_char(UUID_FIRMWARE)).decode(errors="ignore")
                self.data.manufacturer = bytes(await client.read_gatt_char(UUID_MANUFACTURER)).decode(errors="ignore")
            except Exception:
                pass

            raw4303 = bytes.fromhex(self.data.raw_4303.replace("-", "")) if self.data.raw_4303 else b""
            raw4304 = bytes.fromhex(self.data.raw_4304.replace("-", "")) if self.data.raw_4304 else b""
            raw4305 = bytes.fromhex(self.data.raw_4305.replace("-", "")) if self.data.raw_4305 else b""
            self.data.status = self._decode_4303_status(raw4303)
            if len(raw4304) >= 1:
                self.data.dc_output = raw4304[0] == 0x01
            if len(raw4305) >= 1:
                self.data.typec_active = raw4305[0] == 0x01
            return self.data

    async def listen(self) -> None:
        async with BleakClient(self.address) as client:
            self._client = client
            await self.read_once()
            await client.start_notify(UUID_EXT_INFO, lambda _, d: self._update_4303(d))
            while True:
                await asyncio.sleep(60)
