"""Defines the water heater entity to control the Aquarea water tank."""
import logging

from aioaquarea.data import DeviceAction, OperationStatus

from homeassistant.components.water_heater import (
    STATE_HEAT_PUMP,
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF, TEMP_CELSIUS
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

    entities: list[WaterHeater] = []

    entities.extend(
        [
            WaterHeater(coordinator)
            for coordinator in data.values()
            if coordinator.device.has_tank
        ]
    )

    async_add_entities(entities)


class WaterHeater(AquareaBaseEntity, WaterHeaterEntity):
    """Representation of a Aquarea sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: AquareaDataUpdateCoordinator) -> None:
        super().__init__(coordinator)

        self._attr_name = "Tank"
        self._attr_unique_id = f"{super()._attr_unique_id}"
        self._attr_temperature_unit = TEMP_CELSIUS
        self._attr_supported_features = WaterHeaterEntityFeature.TARGET_TEMPERATURE
        self._attr_min_temp = coordinator.device.tank.heat_min
        self._attr_max_temp = coordinator.device.tank.heat_max
        self._attr_target_temperature = coordinator.device.tank.target_temperature
        self._attr_current_temperature = coordinator.device.tank.temperature
        self._attr_operation_list = [HEATING, IDLE]

        if self.coordinator.device.tank.operation_status == OperationStatus.OFF:
            self._attr_state = STATE_OFF
        else:
            self._attr_state = STATE_HEAT_PUMP
            self._attr_current_operation = (
                HEATING
                if self.coordinator.device.current_action == DeviceAction.HEATING_WATER
                else IDLE
            )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        if self.coordinator.device.tank.operation_status == OperationStatus.OFF:
            self._attr_state = STATE_OFF
        else:
            self._attr_state = STATE_HEAT_PUMP
            self._attr_current_operation = (
                HEATING
                if self.coordinator.device.current_action == DeviceAction.HEATING_WATER
                else IDLE
            )

        self._attr_min_temp = self.coordinator.device.tank.heat_min
        self._attr_max_temp = self.coordinator.device.tank.heat_max
        self._attr_target_temperature = self.coordinator.device.tank.target_temperature
        self._attr_current_temperature = self.coordinator.device.tank.temperature
        super()._handle_coordinator_update()
