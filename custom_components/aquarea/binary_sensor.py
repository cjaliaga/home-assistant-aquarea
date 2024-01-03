"""Binary sensors for the Aquarea integration."""
import logging

import aioaquarea

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
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

    entities: list[BinarySensorEntity] = []

    entities.extend([AquareaStatusBinarySensor(coordinator) for coordinator in data.values()])
    entities.extend([AquareaDefrostBinarySensor(coordinator) for coordinator in data.values()])

    async_add_entities(entities)


class AquareaStatusBinarySensor(AquareaBaseEntity, BinarySensorEntity):
    """Representation of a Aquarea sensor that indicates if the device is on error."""

    def __init__(self, coordinator: AquareaDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._attr_unique_id = f"{super().unique_id}_status"
        self._attr_translation_key = "status"
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return self.coordinator.device.is_on_error

class AquareaDefrostBinarySensor(AquareaBaseEntity, BinarySensorEntity):
    """Representation of a Aquarea sensor that indicates if the device is on defrost mode."""

    def __init__(self, coordinator: AquareaDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._attr_unique_id = f"{super().unique_id}_defrost"
        self._attr_translation_key = "defrost"
        self._attr_device_class = BinarySensorDeviceClass.RUNNING

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:snowflake-melt" if self.is_on else "mdi:snowflake-off"

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return self.coordinator.device.device_mode_status is aioaquarea.DeviceModeStatus.DEFROST
