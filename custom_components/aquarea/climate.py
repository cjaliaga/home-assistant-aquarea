import logging

from aioaquarea import DeviceAction, ExtendedOperationMode, UpdateOperationMode
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (ClimateEntityFeature,
                                                    HVACAction, HVACMode)
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

    entities.extend(
        [
            HeatPumpClimate(coordinator, zone_id)
            for coordinator in data.values()
            for zone_id in coordinator.device.zones
        ]
    )

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


def get_update_operation_mode_from_hvac_mode(mode: HVACMode) -> UpdateOperationMode:
    if mode == HVACMode.HEAT:
        return UpdateOperationMode.HEAT

    if mode == HVACMode.COOL:
        return UpdateOperationMode.COOL

    if mode == HVACMode.HEAT_COOL:
        return UpdateOperationMode.AUTO

    return UpdateOperationMode.OFF


class HeatPumpClimate(AquareaBaseEntity, ClimateEntity):
    """The ClimateEntity that controls one zone of the Aquarea heat pump.
    Some settings are shared between zones.
    The entity, the library and the API will keep a consistent state between zones.
    """

    zone_id: int

    def __init__(self, coordinator: AquareaDataUpdateCoordinator, zone_id) -> None:
        super().__init__(coordinator)

        device = coordinator.device

        self._zone_id = zone_id
        self._attr_temperature_unit = TEMP_CELSIUS
        self._attr_name = f"{device.name} {device.zones.get(zone_id).name}"
        self._attr_unique_id = f"{super()._attr_unique_id}_heatpump"

        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE

        self._attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]

        if device.support_cooling(zone_id):
            self._attr_hvac_modes.extend([HVACMode.COOL, HVACMode.HEAT_COOL])

        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        device = self.coordinator.device

        self._attr_hvac_mode = get_hvac_mode_from_ext_op_mode(device.mode)
        self._attr_hvac_action = get_hvac_action_from_ext_action(device.current_action)

        # The device doesn't allow to set the temperature directly
        # So we set the max and min to the current temperature.
        # This is a workaround to make the UI work
        # We need to study if other devices allow to set the temperature and detect that
        # programatelly to make this work for all devices.
        current_temperature = device.zones.get(self._zone_id).temperature
        self._attr_current_temperature = current_temperature
        self._attr_max_temp = current_temperature
        self._attr_min_temp = current_temperature

        super()._handle_coordinator_update()

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        await self.coordinator.device.set_mode(
            get_update_operation_mode_from_hvac_mode(hvac_mode), self._zone_id
        )

    async def async_set_temperature(self, **kwargs) -> None:
        """The device doesn't allow to set the temperature directly."""
