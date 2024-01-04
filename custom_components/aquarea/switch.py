"""Aquarea Switch Sensors."""
import logging

import aioaquarea

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AquareaBaseEntity
from .const import DEVICES, DOMAIN
from .coordinator import AquareaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Aquarea binary sensors from config entry."""

    data: dict[str, AquareaDataUpdateCoordinator] = hass.data[DOMAIN][
        config_entry.entry_id
    ][DEVICES]

    entities: list[SwitchEntity] = []

    entities.extend(
        [
            AquareaForceDHWSwitch(coordinator)
            for coordinator in data.values()
            if coordinator.device.has_tank
        ]
    )

    entities.extend([AquareaForceHeaterSwitch(coordinator) for coordinator in data.values()])
    entities.extend([AquareaHolidayTimerSwitch(coordinator) for coordinator in data.values()])

    async_add_entities(entities)


class AquareaForceDHWSwitch(AquareaBaseEntity, SwitchEntity):
    """Representation of an Aquarea switch."""

    def __init__(self, coordinator: AquareaDataUpdateCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)

        self._attr_translation_key = "force_dhw"
        self._attr_unique_id = f"{super().unique_id}_force_dhw"

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:water-boiler" if self.is_on else "mdi:water-boiler-off"

    @property
    def is_on(self) -> bool:
        """If force DHW mode is enabled."""
        return self.coordinator.device.force_dhw is aioaquarea.ForceDHW.ON

    async def async_turn_on(self) -> None:
        """Turn on Force DHW."""
        await self.coordinator.device.set_force_dhw(aioaquarea.ForceDHW.ON)

    async def async_turn_off(self) -> None:
        """Turn off Force DHW."""
        await self.coordinator.device.set_force_dhw(aioaquarea.ForceDHW.OFF)


class AquareaForceHeaterSwitch(AquareaBaseEntity, SwitchEntity):
    """Representation of an Aquarea switch."""

    def __init__(self, coordinator: AquareaDataUpdateCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)

        self._attr_translation_key = "force_heater"
        self._attr_unique_id = f"{super().unique_id}_force_heater"

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:hvac" if self.is_on else "mdi:hvac-off"

    @property
    def is_on(self) -> bool:
        """If force heater mode is enabled."""
        return self.coordinator.device.force_heater is aioaquarea.ForceHeater.ON

    async def async_turn_on(self) -> None:
        """Turn on Force heater."""
        await self.coordinator.device.set_force_heater(aioaquarea.ForceHeater.ON)

    async def async_turn_off(self) -> None:
        """Turn off Force heater."""
        await self.coordinator.device.set_force_heater(aioaquarea.ForceHeater.OFF)

class AquareaHolidayTimerSwitch(AquareaBaseEntity, SwitchEntity):
    """Representation of an Aquarea switch."""

    def __init__(self, coordinator: AquareaDataUpdateCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)

        self._attr_translation_key = "holiday_timer"
        self._attr_unique_id = f"{super().unique_id}_holiday_timer"

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:timer-check" if self.is_on else "mdi:timer-off"

    @property
    def is_on(self) -> bool:
        """If the holiday timer mode is enabled."""
        return self.coordinator.device.holiday_timer is aioaquarea.HolidayTimer.ON

    async def async_turn_on(self) -> None:
        """Turn on Holiday Timer."""
        await self.coordinator.device.set_holiday_timer(aioaquarea.HolidayTimer.ON)

    async def async_turn_off(self) -> None:
        """Turn off Holiday Timer."""
        await self.coordinator.device.set_holiday_timer(aioaquarea.HolidayTimer.OFF)
