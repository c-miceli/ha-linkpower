"""Protocol decoder for LinkPower Battery."""

from __future__ import annotations


def hex_bytes(data: bytes) -> str:
    """Return hex string for BLE data."""
    return "-".join(f"{byte:02X}" for byte in data)


def split_raw(raw: str | None) -> list[str]:
    """Split raw hex string into byte parts."""
    if not raw:
        return []
    return raw.split("-")


def get_byte(raw: str | None, index: int) -> str | None:
    """Get a byte from a raw hex string."""
    parts = split_raw(raw)

    if len(parts) <= index:
        return None

    return parts[index]


def decode_charge_state(raw_ext_info: str | None) -> str | None:
    """Decode charge state from Ext Info packet."""
    status = get_byte(raw_ext_info, 1)

    if status == "FF":
        return "Discharging"

    if status == "01":
        return "Charging"

    if status == "00":
        return "Idle"

    if status is None:
        return None

    return f"Unknown ({status})"


def decode_dc_output(raw_dc_port: str | None) -> bool | None:
    """Decode DC output status."""
    status = get_byte(raw_dc_port, 0)

    if status is None:
        return None

    return status == "01"


def decode_typec_active(raw_typec_port: str | None) -> bool | None:
    """Decode Type-C active status."""
    status = get_byte(raw_typec_port, 1)

    if status is None:
        return None

    return status == "01"


def decode_packets(
    battery: int | None,
    raw_ext_info: str | None,
    raw_dc_port: str | None,
    raw_typec_port: str | None,
) -> dict:
    """Decode all known LinkPower packet values."""
    return {
        "battery": battery,

        "raw_ext_info": raw_ext_info,
        "raw_dc_port": raw_dc_port,
        "raw_typec_port": raw_typec_port,

        "charge_state": decode_charge_state(raw_ext_info),
        "dc_output": decode_dc_output(raw_dc_port),
        "typec_active": decode_typec_active(raw_typec_port),

        "ext_status_byte": get_byte(raw_ext_info, 1),
        "dc_status_byte": get_byte(raw_dc_port, 0),
        "typec_status_byte": get_byte(raw_typec_port, 1),
    }
