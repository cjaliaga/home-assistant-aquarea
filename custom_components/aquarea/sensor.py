"""Adds Aquarea sensors."""
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Any, Self

from aioaquarea import ConsumptionType, DataNotAvailableError

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorExtraStoredData,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from . import AquareaBaseEntity
from .const import DEVICES, DOMAIN
from .coordinator import AquareaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

@dataclass(kw_only=True)
class AquareaEnergyConsumptionSensorDescription(SensorEntityDescription):
    """Entity Description for Aquarea Energy Consumption Sensors."""

    consumption_type: ConsumptionType
    exists_fn: Callable[[AquareaDataUpdateCoordinator],bool] = lambda _: True

ACCUMULATED_ENERGY_SENSORS: list[AquareaEnergyConsumptionSensorDescription] = [
    AquareaEnergyConsumptionSensorDescription(
        key="heating_accumulated_energy_consumption",
        translation_key="heating_accumulated_energy_consumption",
        name="Heating Accumulated Consumption",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        consumption_type=ConsumptionType.HEAT,
    ),
    AquareaEnergyConsumptionSensorDescription(
        key="cooling_accumulated_energy_consumption",
        translation_key="cooling_accumulated_energy_consumption",
        name= "Cooling Accumulated Consumption",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        consumption_type=ConsumptionType.COOL,
        exists_fn=lambda coordinator: any(zone.cool_mode for zone in coordinator.device.zones.values())
    ),
    AquareaEnergyConsumptionSensorDescription(
        key="tank_accumulated_energy_consumption",
        translation_key = "tank_accumulated_energy_consumption",
        name= "Tank Accumulated Consumption",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        consumption_type=ConsumptionType.WATER_TANK,
        exists_fn=lambda coordinator: coordinator.device.has_tank
    ),
    AquareaEnergyConsumptionSensorDescription(
        key="accumulated_energy_consumption",
        translation_key="accumulated_energy_consumption",
        name= "Accumulated Consumption",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        consumption_type=ConsumptionType.TOTAL
    ),
]

ENERGY_SENSORS: list[AquareaEnergyConsumptionSensorDescription] = [
    AquareaEnergyConsumptionSensorDescription(
        key="heating_energy_consumption",
        translation_key="heating_energy_consumption",
        name="Heating Consumption",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        consumption_type=ConsumptionType.HEAT,
        entity_registry_enabled_default=False
    ),
    AquareaEnergyConsumptionSensorDescription(
        key="tank_energy_consumption",
        translation_key="tank_energy_consumption",
        name= "Tank Consumption",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        consumption_type=ConsumptionType.WATER_TANK,
        exists_fn=lambda coordinator: coordinator.device.has_tank,
        entity_registry_enabled_default=False
    ),
    AquareaEnergyConsumptionSensorDescription(
        key="cooling_energy_consumption",
        translation_key="cooling_energy_consumption",
        name= "Cooling Consumption",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        consumption_type=ConsumptionType.COOL,
        exists_fn=lambda coordinator: any(zone.cool_mode for zone in coordinator.device.zones.values()),
        entity_registry_enabled_default=False
    ),
    AquareaEnergyConsumptionSensorDescription(
        key="energy_consumption",
        translation_key="energy_consumption",
        name= "Consumption",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        consumption_type=ConsumptionType.TOTAL,
        entity_registry_enabled_default=False
    ),
]

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Aquarea sensors from config entry."""

    data: dict[str, AquareaDataUpdateCoordinator] = hass.data[DOMAIN][
        config_entry.entry_id
    ][DEVICES]

    entities: list[SensorEntity] = []

    for coordinator in data.values():
        entities.append(OutdoorTemperatureSensor(coordinator))
        entities.extend(
            [
                EnergyAccumulatedConsumptionSensor(description,coordinator)
                for description in ACCUMULATED_ENERGY_SENSORS
                if description.exists_fn(coordinator)
            ]
        )
        entities.extend(
            [
                EnergyConsumptionSensor(description,coordinator)
                for description in ENERGY_SENSORS
                if description.exists_fn(coordinator)
            ]
        )

    async_add_entities(entities)


@dataclass
class AquareaSensorExtraStoredData(SensorExtraStoredData):
    """Class to hold Aquarea sensor specific state data."""

    period_being_processed: datetime | None = None

    @classmethod
    def from_dict(cls, restored: dict[str, Any]) -> Self:
        """Return AquareaSensorExtraStoredData from dict."""
        sensor_data = super().from_dict(restored)
        return cls(
            native_value=sensor_data.native_value,
            native_unit_of_measurement=sensor_data.native_unit_of_measurement,
            period_being_processed=dt_util.parse_datetime(
                restored.get("period_being_processed","")
            ),
        )

    def as_dict(self) -> dict[str, Any]:
        """Return AquareaSensorExtraStoredData as dict."""
        data = super().as_dict()

        if self.period_being_processed is not None:
            data["period_being_processed"] = dt_util.as_local(
                self.period_being_processed
            ).isoformat()

        return data


@dataclass
class AquareaAccumulatedSensorExtraStoredData(AquareaSensorExtraStoredData):
    """Class to hold Aquarea sensor specific state data."""

    accumulated_period_being_processed: float | None = None

    @classmethod
    def from_dict(cls, restored: dict[str, Any]) -> Self:
        """Return AquareaSensorExtraStoredData from dict."""
        sensor_data = super().from_dict(restored)
        return cls(
            native_value=sensor_data.native_value,
            native_unit_of_measurement=sensor_data.native_unit_of_measurement,
            period_being_processed=sensor_data.period_being_processed,
            accumulated_period_being_processed=restored[
                "accumulated_period_being_processed"
            ],
        )

    def as_dict(self) -> dict[str, Any]:
        """Return AquareaAccumulatedSensorExtraStoredData as dict."""
        data = super().as_dict()
        data[
            "accumulated_period_being_processed"
        ] = self.accumulated_period_being_processed
        return data


class OutdoorTemperatureSensor(AquareaBaseEntity, SensorEntity):
    """Representation of a Aquarea sensor."""

    def __init__(self, coordinator: AquareaDataUpdateCoordinator) -> None:
        """Initialize outdoor temperature sensor."""
        super().__init__(coordinator)

        self._attr_translation_key = "outdoor_temperature"
        self._attr_unique_id = f"{super().unique_id}_outdoor_temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug(
            "Updating sensor '%s' of %s",
            "outdoor_temperature",
            self.coordinator.device.name,
        )

        self._attr_native_value = self.coordinator.device.temperature_outdoor
        super()._handle_coordinator_update()

class EnergyAccumulatedConsumptionSensor(
    AquareaBaseEntity, SensorEntity, RestoreEntity
):
    """Representation of a Aquarea sensor."""

    entity_description: AquareaEnergyConsumptionSensorDescription

    def __init__(self, description: AquareaEnergyConsumptionSensorDescription, coordinator: AquareaDataUpdateCoordinator) -> None:
        """Initialize an accumulated energy consumption sensor."""
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{super().unique_id}_{description.key}"
        )
        self._period_being_processed: datetime | None = None
        self._accumulated_period_being_processed: float | None = None
        self.entity_description = description

    async def async_added_to_hass(self) -> None:
        """Call when entity about to be added to hass."""
        if (sensor_data := await self.async_get_last_sensor_data()) is not None:
            self._attr_native_value = sensor_data.native_value
            self._period_being_processed = sensor_data.period_being_processed
            self._accumulated_period_being_processed = (
                sensor_data.accumulated_period_being_processed
            )

        if self._attr_native_value is None:
            self._attr_native_value = 0

        if self._accumulated_period_being_processed is None:
            self._accumulated_period_being_processed = 0

        await super().async_added_to_hass()

    @property
    def extra_restore_state_data(self) -> AquareaAccumulatedSensorExtraStoredData:
        """Return sensor specific state data to be restored."""
        return AquareaAccumulatedSensorExtraStoredData(
            self.native_value,
            self.native_unit_of_measurement,
            self.period_being_processed,
        )

    async def async_get_last_sensor_data(
        self,
    ) -> AquareaAccumulatedSensorExtraStoredData | None:
        """Restore native_value and native_unit_of_measurement."""
        if (restored_last_extra_data := await self.async_get_last_extra_data()) is None:
            return None
        return AquareaAccumulatedSensorExtraStoredData.from_dict(
            restored_last_extra_data.as_dict()
        )

    @property
    def period_being_processed(self) -> datetime | None:
        """Return the period being processed."""
        return self._period_being_processed

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug(
            "Updating sensor '%s' of %s",
            self.unique_id,
            self.coordinator.device.name,
        )

        # we need to check the value for the current hour. If the device returns None means that we don't have yet data for the current hour. However the device might still update the previous hour data.
        device = self.coordinator.device
        now = dt_util.now().replace(minute=0, second=0, microsecond=0)
        previous_hour = now - timedelta(hours=1)

        try:
            current_hour_consumption = device.get_or_schedule_consumption(
                now, self.entity_description.consumption_type
            )

            previous_hour_consumption = device.get_or_schedule_consumption(
                previous_hour, self.entity_description.consumption_type
            )

        except DataNotAvailableError:
            # we don't have yet data for the current hour but should be available on next refresh
            return

        # Stale data
        if self._period_being_processed not in [now, previous_hour]:
            self._period_being_processed = now
            self._accumulated_period_being_processed = 0

        # 1. When we already have data for the current hour and we were still updating the previous one. This means that the previous hour data is now complete and we can update the sensor value
        if (
            current_hour_consumption is not None
            and previous_hour_consumption is not None
            and self._period_being_processed == previous_hour
        ):
            to_add = abs(previous_hour_consumption - self._accumulated_period_being_processed)
            self._attr_native_value += to_add
            # Store the previous period as completed and move to next one
            self._period_being_processed = now
            self._accumulated_period_being_processed = 0
            super()._handle_coordinator_update()
            return

        # 2. We're still processing the previous hour data and we don't have yet the current hour data. This means that we need to update the sensor value with the previous hour data
        if (
            current_hour_consumption is None
            and previous_hour_consumption is not None
            and self._period_being_processed == previous_hour
        ):
            to_add = abs(previous_hour_consumption - self._accumulated_period_being_processed)
            self._attr_native_value += to_add
            self._accumulated_period_being_processed = previous_hour_consumption
            super()._handle_coordinator_update()
            return

        # 3. We're processing the current hour
        if current_hour_consumption is not None:
            self._period_being_processed = now
            to_add = abs(current_hour_consumption - self._accumulated_period_being_processed)
            self._attr_native_value += to_add
            self._accumulated_period_being_processed = current_hour_consumption
            super()._handle_coordinator_update()
            return

class EnergyConsumptionSensor(AquareaBaseEntity, SensorEntity, RestoreEntity):
    """Representation of a Aquarea sensor."""

    entity_description: AquareaEnergyConsumptionSensorDescription

    def __init__(self, description: AquareaEnergyConsumptionSensorDescription, coordinator: AquareaDataUpdateCoordinator) -> None:
        """Initialize an accumulated energy consumption sensor."""
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{super().unique_id}_{description.key}"
        )
        self._period_being_processed: datetime | None = None
        self.entity_description = description

    async def async_added_to_hass(self) -> None:
        """Call when entity about to be added to hass."""
        if (sensor_data := await self.async_get_last_sensor_data()) is not None:
            self._attr_native_value = sensor_data.native_value
            self._period_being_processed = sensor_data.period_being_processed

        if self._attr_native_value is None:
            self._attr_native_value = 0

        await super().async_added_to_hass()

    @property
    def extra_restore_state_data(self) -> AquareaSensorExtraStoredData:
        """Return sensor specific state data to be restored."""
        return AquareaSensorExtraStoredData(
            self.native_value,
            self.native_unit_of_measurement,
            self.period_being_processed,
        )

    async def async_get_last_sensor_data(self) -> AquareaSensorExtraStoredData | None:
        """Restore native_value and native_unit_of_measurement."""
        if (restored_last_extra_data := await self.async_get_last_extra_data()) is None:
            return None
        return AquareaSensorExtraStoredData.from_dict(
            restored_last_extra_data.as_dict()
        )

    @property
    def period_being_processed(self) -> datetime | None:
        """Return the period being processed."""
        return self._period_being_processed

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug(
            "Updating sensor '%s' of %s",
            self.unique_id,
            self.coordinator.device.name,
        )

        # we need to check the value for the current hour. If the device returns None means that we don't have yet data for the current hour. However the device might still update the previous hour data.
        device = self.coordinator.device
        now = dt_util.now().replace(minute=0, second=0, microsecond=0)
        previous_hour = now - timedelta(hours=1)

        try:
            current_hour_consumption = device.get_or_schedule_consumption(
                now, self.entity_description.consumption_type
            )

            previous_hour_consumption = device.get_or_schedule_consumption(
                previous_hour, self.entity_description.consumption_type
            )

        except DataNotAvailableError:
            # we don't have yet data for the current hour but should be available on next refresh
            return

        # Stale data, we reset to 0 to start a new cycle
        if self._period_being_processed not in [now, previous_hour]:
            self._period_being_processed = now
            self._attr_native_value = 0
            super()._handle_coordinator_update()
            return

        # 1. When we already have data for the current hour and we were still updating the previous one. This means that the previous hour data is now complete and we can update the sensor value
        if (
            current_hour_consumption is not None
            and previous_hour_consumption is not None
            and self._period_being_processed == previous_hour
        ):
            self._attr_native_value = previous_hour_consumption
            self._period_being_processed = now
            # Store the previous period as completed
            super()._handle_coordinator_update()
            # Reset the value to 0 to start the new period
            self._attr_native_value = 0
            super()._handle_coordinator_update()
            # Update the value with the current hour data
            self._attr_native_value = current_hour_consumption
            super()._handle_coordinator_update()
            return

        # 2. We're still processing the previous hour data and we don't have yet the current hour data. This means that we need to update the sensor value with the previous hour data
        if (
            current_hour_consumption is None
            and previous_hour_consumption is not None
            and self._period_being_processed == previous_hour
        ):
            self._attr_native_value = previous_hour_consumption
            super()._handle_coordinator_update()
            return

        # 3. We're processing the current hour
        if current_hour_consumption is not None:
            self._period_being_processed = now
            self._attr_native_value = current_hour_consumption
            super()._handle_coordinator_update()
            return
