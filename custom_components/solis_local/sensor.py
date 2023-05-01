"""Sensors for Solis Local."""

from datetime import timedelta
import logging
from collections.abc import Callable
from dataclasses import dataclass

import async_timeout

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower, UnitOfEnergy, PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN
from .solis_local import SolisLocalHttpAPI

_LOGGER = logging.getLogger(__name__)


@dataclass
class SolisEntityDescriptionMixin:
    """Describe a Solis entity."""

    parse: Callable


@dataclass
class SolisEntityDescription(SensorEntityDescription, SolisEntityDescriptionMixin):
    """Describe a Solis entity slot."""


_SOLIS_VARIABLES = (
    SolisEntityDescription(
        key="webdata_now_p",
        name="Solis Power Now",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        parse=float,
    ),
    SolisEntityDescription(
        key="webdata_today_e",
        name="Solis Energy Today",
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        parse=float,
    ),
    SolisEntityDescription(
        key="webdata_total_e",
        name="Solis Energy Total",
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        parse=float,
    ),
    SolisEntityDescription(
        key="cover_sta_rssi",
        name="Solis WiFi connection quality",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        native_unit_of_measurement=PERCENTAGE,
        parse=lambda s: float(s.split("%")[0]),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up an entry."""
    _LOGGER.debug("setup_entry: %s", entry.as_dict())
    my_api = hass.data[DOMAIN][entry.entry_id]
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
    async_add_entities(
        MyEntity(coordinator, description, entry.entry_id)
        for description in _SOLIS_VARIABLES
    )


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
        except (ConnectionError, OSError):
            return {"webdata_now_p": "0"}
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

    def __init__(
        self, coordinator, description: SolisEntityDescription, entry_id: str
    ) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self.var_name = description.key
        # self._attr_name = DOMAIN + "_" + spec["name"]
        # self._attr_state_class = spec["state-class"]
        # self._attr_device_class = spec["device-class"]
        # self._attr_native_unit_of_measurement = spec["unit"]
        self.parser = description.parse
        self.entity_description = description
        self.entity_id = f"sensor.solis_local_{description.key}"
        self._attr_unique_id = f"{entry_id}-{description.key}"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        #        _LOGGER.debug("Entity update: %s", self.coordinator.data)
        if self.var_name in self.coordinator.data:
            value = self.coordinator.data[self.var_name]
            self._attr_native_value = self.parser(value)
            self.async_write_ha_state()
