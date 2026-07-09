"""The LinkPower Battery integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import LinkPowerCoordinator

type LinkPowerConfigEntry = ConfigEntry


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the LinkPower integration."""
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LinkPowerConfigEntry,
) -> bool:
    """Set up LinkPower from a config entry."""

    coordinator = LinkPowerCoordinator(hass, entry.data.get("address"))

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    # Try refresh after entities exist.
    await coordinator.async_request_refresh()

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: LinkPowerConfigEntry,
) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
