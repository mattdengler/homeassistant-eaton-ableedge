"""Shared entity helpers for the Eaton AbleEdge Breakers integration."""
from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import EatonAbleEdgeCoordinator


def _get_path(data: dict[str, Any], path: tuple[str, ...]) -> Any:
    """Return a nested value from breaker data, or None if missing."""
    value: Any = data
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


class EatonAbleEdgeEntity(CoordinatorEntity[EatonAbleEdgeCoordinator]):
    """Base entity for Eaton AbleEdge breaker sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EatonAbleEdgeCoordinator,
        description: Any,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = description
        breaker_id = coordinator.breaker_id
        self._attr_unique_id = f"{breaker_id}_{description.key}"
        self._attr_device_info = self._build_device_info()

    def _build_device_info(self) -> DeviceInfo:
        """Build device info from the breaker's static data, when available."""
        data = self.coordinator.data or {}
        static_data = data.get("staticData") or {}
        configuration = data.get("configuration") or {}

        firmware_version = _get_path(
            configuration, ("firmwareVersion", "val")
        )

        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.breaker_id)},
            manufacturer=MANUFACTURER,
            model=static_data.get("partNumber"),
            name=f"Eaton Breaker {self.coordinator.breaker_id}",
            serial_number=static_data.get("serialNumber"),
            sw_version=firmware_version,
            connections=(
                {("mac", static_data["macAddress"])}
                if static_data.get("macAddress")
                else set()
            ),
        )

    def _get_value(self, path: tuple[str, ...]) -> Any:
        """Get a nested value from the coordinator's breaker data."""
        return _get_path(self.coordinator.data or {}, path)
