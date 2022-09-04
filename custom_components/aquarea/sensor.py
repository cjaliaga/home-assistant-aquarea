import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
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
    """Set up the Aquarea sensors from config entry."""

    data: dict[str, AquareaDataUpdateCoordinator] = hass.data[DOMAIN][
        config_entry.entry_id
    ][DEVICES]

    entities: list[OutDoorTemperatureSensor] = []

    entities.extend(
        [OutDoorTemperatureSensor(coordinator) for coordinator in data.values()]
    )

    async_add_entities(entities)


class OutDoorTemperatureSensor(AquareaBaseEntity, SensorEntity):
    """Representation of a Aquarea sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: AquareaDataUpdateCoordinator) -> None:
        super().__init__(coordinator)

        self._attr_name = "Outdoor Temperature"
        self._attr_unique_id = f"{super()._attr_unique_id}_outdoor_temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "°C"

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
