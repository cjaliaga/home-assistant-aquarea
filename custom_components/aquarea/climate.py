"""Climate entity to control a zone for a Panasonic Aquarea Device"""
from __future__ import annotations

import logging

from aioaquarea import (
    DeviceAction,
    ExtendedOperationMode,
    OperationStatus,
    UpdateOperationMode,
    QuietMode,
)

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
    ATTR_HVAC_MODE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, PRECISION_WHOLE, UnitOfTemperature
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

    async_add_entities(
        [
            HeatPumpClimate(coordinator, zone_id)
            for coordinator in data.values()
            for zone_id in coordinator.device.zones
        ]
    )


def get_hvac_mode_from_ext_op_mode(
    mode: ExtendedOperationMode, zone_status: OperationStatus
) -> HVACMode:
    """Convert extended operation mode to HVAC mode."""
    if zone_status == OperationStatus.OFF:
        return HVACMode.OFF

    if mode == ExtendedOperationMode.HEAT:
        return HVACMode.HEAT

    if mode == ExtendedOperationMode.COOL:
        return HVACMode.COOL

    if mode in (ExtendedOperationMode.AUTO_COOL, ExtendedOperationMode.AUTO_HEAT):
        return HVACMode.HEAT_COOL

    return HVACMode.OFF


def get_hvac_action_from_ext_action(action: DeviceAction) -> HVACAction:
    """Convert device action to HVAC action."""
    if action == DeviceAction.COOLING:
        return HVACAction.COOLING

    if action == DeviceAction.HEATING:
        return HVACAction.HEATING

    return HVACAction.IDLE


def get_update_operation_mode_from_hvac_mode(mode: HVACMode) -> UpdateOperationMode:
    """Convert HVAC mode to update operation mode."""
    if mode == HVACMode.HEAT:
        return UpdateOperationMode.HEAT

    if mode == HVACMode.COOL:
        return UpdateOperationMode.COOL

    if mode == HVACMode.HEAT_COOL:
        return UpdateOperationMode.AUTO

    return UpdateOperationMode.OFF


def get_quiet_mode_from_preset_mode(preset_mode: str) -> QuietMode:
    """Convert preset mode to quiet mode."""

    if preset_mode == "Quiet Mode Level 1":
        return QuietMode.LEVEL1

    if preset_mode == "Quiet Mode Level 2":
        return QuietMode.LEVEL2

    if preset_mode == "Quiet Mode Level 3":
        return QuietMode.LEVEL3

    return QuietMode.OFF


def get_preset_from_quiet_mode(quiet_mode: QuietMode) -> str:
    """Convert quiet mode to preset mode."""

    if quiet_mode == QuietMode.LEVEL1:
        return "Quiet Mode Level 1"

    if quiet_mode == QuietMode.LEVEL2:
        return "Quiet Mode Level 2"

    if quiet_mode == QuietMode.LEVEL3:
        return "Quiet Mode Level 3"

    return ""


def get_presets() -> list[str]:
    """Return the list of available preset modes."""
    return [
        "Quiet Mode Off",
        "Quiet Mode Level 1",
        "Quiet Mode Level 2",
        "Quiet Mode Level 3",
    ]


class HeatPumpClimate(AquareaBaseEntity, ClimateEntity):
    """The ClimateEntity that controls one zone of the Aquarea heat pump.
    Some settings are shared between zones.
    The entity, the library and the API will keep a consistent state between zones.
    """

    _attr_has_entity_name = True
    zone_id: int

    def __init__(self, coordinator: AquareaDataUpdateCoordinator, zone_id) -> None:
        super().__init__(coordinator)

        device = coordinator.device

        self._zone_id = zone_id
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_name = device.zones.get(zone_id).name
        self._attr_unique_id = f"{super().unique_id}_climate_{zone_id}"

        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
        )
        self._attr_precision = PRECISION_WHOLE
        self._attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
        self._attr_preset_modes = get_presets()
        self._attr_preset_mode = get_preset_from_quiet_mode(device.quiet_mode)

        if device.support_cooling(zone_id):
            self._attr_hvac_modes.extend([HVACMode.COOL, HVACMode.HEAT_COOL])

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        device = self.coordinator.device
        zone = device.zones.get(self._zone_id)

        self._attr_hvac_mode = get_hvac_mode_from_ext_op_mode(
            device.mode, zone.operation_status
        )
        self._attr_hvac_action = get_hvac_action_from_ext_action(device.current_action)
        self._attr_icon = (
            "mdi:hvac-off" if device.mode == ExtendedOperationMode.OFF else "mdi:hvac"
        )

        self._attr_preset_mode = get_preset_from_quiet_mode(device.quiet_mode)

        self._attr_current_temperature = zone.temperature

        # If the device doesn't allow to set the temperature directly
        # We set the max and min to the current temperature.
        # This is a workaround to make the UI work.
        self._attr_max_temp = zone.temperature
        self._attr_min_temp = zone.temperature

        if zone.supports_set_temperature and device.mode != ExtendedOperationMode.OFF:
            self._attr_max_temp = (
                zone.cool_max
                if device.mode
                in (ExtendedOperationMode.COOL, ExtendedOperationMode.AUTO_COOL)
                else zone.heat_max
            )
            self._attr_min_temp = (
                zone.cool_min
                if device.mode
                in (ExtendedOperationMode.COOL, ExtendedOperationMode.AUTO_COOL)
                else zone.heat_min
            )
            self._attr_target_temperature = (
                zone.cool_target_temperature
                if device.mode
                in (
                    ExtendedOperationMode.COOL,
                    ExtendedOperationMode.AUTO_COOL,
                )
                else zone.heat_target_temperature
            )
            self._attr_target_temperature_step = 1

        super()._handle_coordinator_update()

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        if hvac_mode not in self.hvac_modes:
            raise ValueError(f"Unsupported HVAC mode: {hvac_mode}")

        _LOGGER.debug(
            "Setting operation mode of %s to %s",
            self.coordinator.device.device_id,
            hvac_mode,
        )

        await self.coordinator.device.set_mode(
            get_update_operation_mode_from_hvac_mode(hvac_mode), self._zone_id
        )

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature if supported by the zone"""
        zone = self.coordinator.device.zones.get(self._zone_id)
        temperature: float | None = kwargs.get(ATTR_TEMPERATURE)
        hvac_mode: HVACMode | None = kwargs.get(ATTR_HVAC_MODE)

        if hvac_mode is not None:
            await self.async_set_hvac_mode(hvac_mode)

        if temperature is not None and zone.supports_set_temperature:
            _LOGGER.debug(
                "Setting temperature of device:zone == %s:%s to %s",
                self.coordinator.device.device_id,
                zone.name,
                str(temperature),
            )

            await self.coordinator.device.set_temperature(
                int(temperature), zone.zone_id
            )

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        if preset_mode not in self.preset_modes:
            raise ValueError(f"Unsupported preset mode: {preset_mode}")

        _LOGGER.debug(
            "Setting preset mode of %s to %s",
            self.coordinator.device.device_id,
            preset_mode,
        )

        quiet_mode = get_quiet_mode_from_preset_mode(preset_mode)
        await self.coordinator.device.set_quiet_mode(quiet_mode)
