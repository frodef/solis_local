"""Sensors for Solis Local."""

from datetime import timedelta
import logging

import async_timeout

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .solis_local import SolisLocalHttpAPI

_LOGGER = logging.getLogger(__name__)


# async def async_setup_platform(
#     hass: HomeAssistant,
#     config: ConfigType,
#     async_add_entities: AddEntitiesCallback = None,
#     discovery_info: DiscoveryInfoType | None = None,
# ) -> None:
#     """Set up Solis Local platform."""
#     pass


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up an entry."""
    _LOGGER.debug("setup_entry: %s", entry.as_dict())
    #    my_api = hass.data[DOMAIN][entry.entry_id]
    my_api = SolisLocalHttpAPI(
        data={"host": "192.168.1.166", "username": "admin", "password": "gbgfvf"}
    )
    coordinator = MyCoordinator(hass, my_api)

    # Fetch initial data so we have data when entities subscribe
    #
    # If the refresh fails, async_config_entry_first_refresh will
    # raise ConfigEntryNotReady and setup will try again later
    #
    # If you do not want to retry setup on failure, use
    # coordinator.async_refresh() instead
    #
    await coordinator.async_config_entry_first_refresh()
    async_add_entities([MyEntity(coordinator)])


class MyCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass: HomeAssistant, my_api) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="Solis Local Sensor",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=14),
        )
        self.my_api: SolisLocalHttpAPI = my_api

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(10):
                #                return await self.my_api.fetch_data()
                #                return {'value': 5}
                return await self.my_api.load_status()
        #        except ApiAuthError as err:
        # Raising ConfigEntryAuthFailed will cancel future updates
        # and start a config flow with SOURCE_REAUTH (async_step_reauth)
        #           raise ConfigEntryAuthFailed from err
        #       except ApiError as err:
        #           raise UpdateFailed(f"Error communicating with API: {err}")
        finally:
            pass


class MyEntity(CoordinatorEntity, SensorEntity):
    """An entity using CoordinatorEntity.

    The CoordinatorEntity class provides:
      should_poll
      async_update
      async_added_to_hass
      available

    """

    _attr_name = "Solis Local Entity FVF"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT

    # def __init__(self, coordinator):
    #     """Pass coordinator to CoordinatorEntity."""
    #     super().__init__(coordinator)
    #     self.idx = idx

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        #        _LOGGER.debug("Entity update: %s", self.coordinator.data)
        value = self.coordinator.data["webdata_now_p"]
        if value:
            self._attr_native_value = float(value)
            self.async_write_ha_state()
