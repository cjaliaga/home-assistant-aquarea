"""Defines the water heater entity to control the Aquarea water tank."""
from __future__ import annotations

import logging

from aioaquarea.data import DeviceAction, OperationStatus

from homeassistant.components.water_heater import (
    STATE_HEAT_PUMP,
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    PRECISION_WHOLE,
    STATE_OFF,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AquareaBaseEntity
from .const import DEVICES, DOMAIN, HEATING, IDLE
from .coordinator import AquareaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Aquarea sensors from config entry."""

    data: dict[str, AquareaDataUpdateCoordinator] = hass.data[DOMAIN][
        config_entry.entry_id
    ][DEVICES]

    async_add_entities(
        [
            WaterHeater(coordinator)
            for coordinator in data.values()
            if coordinator.device.has_tank
        ]
    )


class WaterHeater(AquareaBaseEntity, WaterHeaterEntity):
    """Representation of a Aquarea sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: AquareaDataUpdateCoordinator) -> None:
        super().__init__(coordinator)

        self._attr_name = "Tank"
        self._attr_unique_id = f"{super().unique_id}_tank"
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_supported_features = (
            WaterHeaterEntityFeature.TARGET_TEMPERATURE
            | WaterHeaterEntityFeature.OPERATION_MODE
        )
        self._attr_operation_list = [HEATING, STATE_OFF]
        self._attr_precision = PRECISION_WHOLE
        self._attr_target_temperature_step = 1
        self._update_temperature()
        self._update_operation_state()

    @property
    def target_temperature_step(self) -> float | None:
        """Return the supported step of target temperature."""
        return self._attr_target_temperature_step

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        self._update_temperature()
        self._update_operation_state()
        super()._handle_coordinator_update()

    def _update_operation_state(self) -> None:
        if self.coordinator.device.tank.operation_status == OperationStatus.OFF:
            self._attr_state = STATE_OFF
            self._attr_current_operation = STATE_OFF
            self._attr_icon = (
                "mdi:water-boiler-alert"
                if self.coordinator.device.is_on_error
                else "mdi:water-boiler-off"
            )
        else:
            self._attr_icon = "mdi:water-boiler"
            self._attr_state = STATE_HEAT_PUMP
            self._attr_current_operation = (
                HEATING
                if self.coordinator.device.current_action == DeviceAction.HEATING_WATER
                else IDLE
            )

    def _update_temperature(self) -> None:
        self._attr_min_temp = self.coordinator.device.tank.heat_min
        self._attr_max_temp = self.coordinator.device.tank.heat_max
        self._attr_target_temperature = self.coordinator.device.tank.target_temperature
        self._attr_current_temperature = self.coordinator.device.tank.temperature

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature: float | None = kwargs.get(ATTR_TEMPERATURE)
        if temperature is not None:
            _LOGGER.debug(
                "Setting %s water tank temperature to %s",
                self.coordinator.device.device_id,
                str(temperature),
            )
            await self.coordinator.device.tank.set_target_temperature(int(temperature))

    async def async_set_operation_mode(self, operation_mode):
        _LOGGER.debug(
            "Turning %s water tank %s",
            self.coordinator.device.device_id,
            operation_mode,
        )
        if operation_mode == HEATING:
            await self.coordinator.device.tank.turn_on()
        elif operation_mode == STATE_OFF:
            await self.coordinator.device.tank.turn_off()
