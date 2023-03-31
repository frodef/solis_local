"""The solis_local integration."""
from __future__ import annotations
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .solis_local import AuthorizationFailed, ConnectionFailed, SolisLocalHttpAPI

_LOGGER = logging.getLogger(__name__)

# List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up solis_local from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    # xTODO 1. Create API instance
    # xTODO 2. Validate the API connection (and authentication)
    # xTODO 3. Store an API object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)
    _LOGGER.debug("setup: %s", entry.as_dict())
    hass.data[DOMAIN][entry.entry_id] = SolisLocalHttpAPI(
        entry.data["host"], entry.data["username"], entry.data["password"]
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
