"""Sensors for HA Smart Solar Manager."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SmartSolarCoordinator


@dataclass(frozen=True)
class SmartSolarSensorDescription:
    """Description for a Smart Solar Manager sensor."""

    key: str
    name: str
    unit: str | None = None


SENSORS: tuple[SmartSolarSensorDescription, ...] = (
    SmartSolarSensorDescription("mode", "Smart Solar Mode"),
    SmartSolarSensorDescription("next_action", "Smart Solar Next Action"),
    SmartSolarSensorDescription("estimated_savings", "Smart Solar Estimated Savings (Hour)"),
    SmartSolarSensorDescription("solar_surplus_w", "Smart Solar Surplus", UnitOfPower.WATT),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Solar sensor entities."""
    coordinator: SmartSolarCoordinator = hass.data[DOMAIN]["entries"][entry.entry_id]
    async_add_entities(
        SmartSolarSensor(coordinator, entry, description) for description in SENSORS
    )


class SmartSolarSensor(CoordinatorEntity[SmartSolarCoordinator], SensorEntity):
    """Smart Solar Manager sensor entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SmartSolarCoordinator,
        entry: ConfigEntry,
        description: SmartSolarSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = description.name
        self._entry = entry
        if description.unit:
            self._attr_native_unit_of_measurement = description.unit

    @property
    def native_value(self) -> str | float | int | None:
        """Return sensor value from coordinator data."""
        recommendation = (self.coordinator.data or {}).get("recommendation", {})

        if self.entity_description.key == "mode":
            return recommendation.get("mode", "unknown")

        if self.entity_description.key == "next_action":
            actions = recommendation.get("actions", [])
            if not actions:
                return "none"
            action = actions[0]
            return f"{action.get('command', 'none')} {action.get('entity_id', '')}".strip()

        if self.entity_description.key == "estimated_savings":
            return recommendation.get("estimated_savings", 0.0)

        if self.entity_description.key == "solar_surplus_w":
            return recommendation.get("solar_surplus_w", 0.0)

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return attributes for context and dashboard cards."""
        recommendation = (self.coordinator.data or {}).get("recommendation", {})
        inputs = (self.coordinator.data or {}).get("inputs", {})
        return {
            "reason": recommendation.get("reason", ""),
            "actions": recommendation.get("actions", []),
            "weights": recommendation.get("weights", {}),
            "weighted_signal": recommendation.get("weighted_signal", 0),
            "inputs": inputs,
        }
