"""Binary sensor platform for the Eaton AbleEdge Breakers integration."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import EatonAbleEdgeConfigEntry
from .entity import EatonAbleEdgeEntity


@dataclass(frozen=True, kw_only=True)
class EatonAbleEdgeBinarySensorDescription(BinarySensorEntityDescription):
    """Describes an Eaton AbleEdge binary sensor entity."""

    value_path: tuple[str, ...] = ()


BINARY_SENSOR_DESCRIPTIONS: tuple[EatonAbleEdgeBinarySensorDescription, ...] = (
    EatonAbleEdgeBinarySensorDescription(
        key="is_connected",
        translation_key="is_connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_path=("telemetryData", "isConnected", "val"),
    ),
    EatonAbleEdgeBinarySensorDescription(
        key="load_status",
        translation_key="load_status",
        device_class=BinarySensorDeviceClass.POWER,
        value_path=("status", "loadStatus", "val"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EatonAbleEdgeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Eaton AbleEdge binary sensors from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        EatonAbleEdgeBinarySensor(coordinator, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class EatonAbleEdgeBinarySensor(EatonAbleEdgeEntity, BinarySensorEntity):
    """Representation of an Eaton AbleEdge breaker binary sensor."""

    entity_description: EatonAbleEdgeBinarySensorDescription

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        value = self._get_value(self.entity_description.value_path)
        if value is None:
            return None
        return bool(value)
