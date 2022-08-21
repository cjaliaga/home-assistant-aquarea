import logging

from aioaquarea.data import DeviceAction, ExtendedOperationMode, OperationStatus

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import TEMP_CELSIUS
from homeassistant.core import HomeAssistant, callback
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
    """Set up the Aquarea climate entities from config entry."""

    data: dict[str, AquareaDataUpdateCoordinator] = hass.data[DOMAIN][
        config_entry.entry_id
    ][DEVICES]

    entities: list[HeatPumpClimate] = []

    entities.extend([HeatPumpClimate(coordinator) for coordinator in data.values()])

    async_add_entities(entities)


def get_hvac_mode_from_ext_op_mode(mode: ExtendedOperationMode) -> HVACMode:
    if mode == ExtendedOperationMode.HEAT:
        return HVACMode.HEAT

    if mode == ExtendedOperationMode.COOL:
        return HVACMode.COOL

    if mode in (ExtendedOperationMode.AUTO_COOL, ExtendedOperationMode.AUTO_HEAT):
        return HVACMode.HEAT_COOL

    return HVACMode.OFF


def get_hvac_action_from_ext_action(action: DeviceAction) -> HVACAction:
    if action == DeviceAction.COOLING:
        return HVACAction.COOLING

    if action == DeviceAction.HEATING:
        return HVACAction.HEATING

    return HVACAction.IDLE


class HeatPumpClimate(AquareaBaseEntity, ClimateEntity):
    def __init__(self, coordinator: AquareaDataUpdateCoordinator) -> None:
        super().__init__(coordinator)

        self._attr_temperature_unit = TEMP_CELSIUS
        self._attr_name = self.coordinator.device.name
        self._attr_unique_id = f"{super()._attr_unique_id}_heatpump"

        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE

        self._attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]

        if self.coordinator.device.support_cooling():
            self._attr_hvac_modes.extend([HVACMode.COOL, HVACMode.HEAT_COOL])

        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        device = self.coordinator.device

        self._attr_hvac_mode = get_hvac_mode_from_ext_op_mode(device.mode)

        self._attr_current_temperature = device.zones.get(1).temperature
        self._attr_hvac_action = get_hvac_action_from_ext_action(device.current_action)

        self._attr_max_temp = device.zones.get(1).temperature
        self._attr_min_temp = device.zones.get(1).temperature

        super()._handle_coordinator_update()

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""

    async def async_set_temperature(self, **kwargs) -> None:
        """The device doesn't allow to set the temperature directly."""
