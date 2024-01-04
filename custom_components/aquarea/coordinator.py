"""Coordinator for Aquarea."""
from __future__ import annotations

from datetime import timedelta
import logging

import aioaquarea

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DOMAIN

DEFAULT_SCAN_INTERVAL_SECONDS = 10
SCAN_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL_SECONDS)
CONSUMPTION_REFRESH_INTERVAL_MINUTES = 1
CONSUMPTION_REFRESH_INTERVAL = timedelta(minutes=CONSUMPTION_REFRESH_INTERVAL_MINUTES)
_LOGGER = logging.getLogger(__name__)


class AquareaDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Aquarea data."""

    _device: aioaquarea.Device

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: aioaquarea.Client,
        device_info: aioaquarea.data.DeviceInfo,
    ) -> None:
        """Initialize a data updater per Device."""

        self._client = client
        self._entry = entry
        self._device_info = device_info
        self._device = None

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}-{entry.data[CONF_USERNAME]}-{device_info.device_id}",
            update_interval=SCAN_INTERVAL,
        )

    @property
    def device(self) -> aioaquarea.Device:
        """Return the device."""
        return self._device

    async def _async_update_data(self) -> None:
        """Fetch data from Aquarea Smart Cloud Service."""
        try:
            # We are not getting consumption data on the first refresh, we'll get it on the next ones
            if not self._device:
                self._device = await self._client.get_device(
                    device_info=self._device_info,
                    consumption_refresh_interval=CONSUMPTION_REFRESH_INTERVAL,
                    timezone=dt_util.DEFAULT_TIME_ZONE,
                )
            else:
                await self.device.refresh_data()
        except aioaquarea.AuthenticationError as err:
            if err.error_code in (
                aioaquarea.AuthenticationErrorCodes.INVALID_USERNAME_OR_PASSWORD,
                aioaquarea.AuthenticationErrorCodes.INVALID_CREDENTIALS,
            ):
                raise ConfigEntryAuthFailed from err
        except aioaquarea.errors.RequestFailedError as err:
            raise UpdateFailed(
                f"Error communicating with Aquarea Smart Cloud API: {err}"
            ) from err
