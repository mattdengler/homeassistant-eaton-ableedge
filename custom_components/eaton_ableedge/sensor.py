"""Sensor platform for the Eaton AbleEdge Breakers integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfElectricCurrent,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import EatonAbleEdgeConfigEntry
from .entity import EatonAbleEdgeEntity


@dataclass(frozen=True, kw_only=True)
class EatonAbleEdgeSensorDescription(SensorEntityDescription):
    """Describes an Eaton AbleEdge sensor entity."""

    value_path: tuple[str, ...] = ()


SENSOR_DESCRIPTIONS: tuple[EatonAbleEdgeSensorDescription, ...] = (
    EatonAbleEdgeSensorDescription(
        key="remote_contact_position",
        translation_key="remote_contact_position",
        value_path=("status", "remoteContactPosition", "val"),
    ),
    EatonAbleEdgeSensorDescription(
        key="main_handle_position",
        translation_key="main_handle_position",
        value_path=("status", "mainHandlePosition", "val"),
    ),
    EatonAbleEdgeSensorDescription(
        key="rssi",
        translation_key="rssi",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        value_path=("telemetryData", "rssi", "val"),
    ),
    EatonAbleEdgeSensorDescription(
        key="rated_current",
        translation_key="rated_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_path=("staticData", "ratedCurrent"),
    ),
    EatonAbleEdgeSensorDescription(
        key="firmware_version",
        translation_key="firmware_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_path=("configuration", "firmwareVersion", "val"),
    ),
    EatonAbleEdgeSensorDescription(
        key="ip_address",
        translation_key="ip_address",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_path=("configuration", "ipAddress", "val"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EatonAbleEdgeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Eaton AbleEdge sensors from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        EatonAbleEdgeSensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    )


class EatonAbleEdgeSensor(EatonAbleEdgeEntity, SensorEntity):
    """Representation of an Eaton AbleEdge breaker sensor."""

    entity_description: EatonAbleEdgeSensorDescription

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        return self._get_value(self.entity_description.value_path)
