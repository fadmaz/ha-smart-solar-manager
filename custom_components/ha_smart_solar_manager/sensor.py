"""Sensors for HA Smart Solar Manager."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SmartSolarCoordinator


@dataclass(frozen=True)
class SmartSolarSensorDescription(SensorEntityDescription):
    """Description for a Smart Solar Manager sensor."""


SENSORS: tuple[SmartSolarSensorDescription, ...] = (
    SmartSolarSensorDescription(key="mode", name="Mode", icon="mdi:lightbulb"),
    SmartSolarSensorDescription(key="reason", name="Reason", icon="mdi:information"),
    SmartSolarSensorDescription(
        key="next_action",
        name="Next Action",
        icon="mdi:play-circle",
    ),
    SmartSolarSensorDescription(
        key="estimated_savings",
        name="Estimated Savings (Hour)",
        icon="mdi:currency-usd",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SmartSolarSensorDescription(
        key="solar_surplus_w",
        name="Solar Surplus",
        native_unit_of_measurement=UnitOfPower.WATT,
        icon="mdi:solar-power",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SmartSolarSensorDescription(
        key="battery_soc",
        name="Battery SoC",
        native_unit_of_measurement="%",
        icon="mdi:battery",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SmartSolarSensorDescription(
        key="grid_import_w",
        name="Grid Import",
        native_unit_of_measurement=UnitOfPower.WATT,
        icon="mdi:transmission-tower-import",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SmartSolarSensorDescription(
        key="pv_power_w",
        name="PV Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        icon="mdi:solar-power-variant",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SmartSolarSensorDescription(
        key="efficiency_score",
        name="Efficiency Score",
        native_unit_of_measurement="%",
        icon="mdi:gauge",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SmartSolarSensorDescription(
        key="confidence_score",
        name="Confidence Score",
        native_unit_of_measurement="%",
        icon="mdi:check-decagram",
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Solar sensor entities."""
    coordinator: SmartSolarCoordinator = hass.data[DOMAIN]["entries"][entry.entry_id]
    async_add_entities(
        [SmartSolarSensor(coordinator, entry, description) for description in SENSORS]
    )


class SmartSolarSensor(CoordinatorEntity[SmartSolarCoordinator], SensorEntity):
    """Smart Solar Manager sensor entity."""

    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = True
    entity_description: SmartSolarSensorDescription

    def __init__(
        self,
        coordinator: SmartSolarCoordinator,
        entry: ConfigEntry,
        description: SmartSolarSensorDescription,
    ) -> None:
        self.entity_description = description
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Smart Solar Manager",
        )

    @property
    def native_value(self) -> str | float | int | None:
        """Return sensor value from coordinator data."""
        recommendation = (self.coordinator.data or {}).get("recommendation", {})
        inputs = (self.coordinator.data or {}).get("inputs", {})

        if self.entity_description.key == "mode":
            return recommendation.get("mode", "unknown")

        if self.entity_description.key == "reason":
            return recommendation.get("reason", "unknown")

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

        if self.entity_description.key == "battery_soc":
            return inputs.get("battery_soc")

        if self.entity_description.key == "grid_import_w":
            return inputs.get("grid_import_w")

        if self.entity_description.key == "pv_power_w":
            return inputs.get("pv_power_w")

        if self.entity_description.key == "efficiency_score":
            # Calculate efficiency score based on current conditions.
            # Return None when PV is unavailable/zero to avoid misleading values.
            pv_power = inputs.get("pv_power_w", 0) or 0
            grid_import = inputs.get("grid_import_w", 0) or 0
            battery_soc = inputs.get("battery_soc", 50) or 50

            if pv_power <= 0:
                return None

            # Score based on self-consumption and battery optimization.
            self_consumption_ratio = max(0, min(100, (1 - (grid_import / pv_power)) * 100))
            battery_optimization = battery_soc if battery_soc >= 30 else (battery_soc / 30) * 50
            efficiency = (self_consumption_ratio * 0.6 + battery_optimization * 0.4)
            return round(max(0, min(100, efficiency)), 1)

        if self.entity_description.key == "confidence_score":
            return recommendation.get("confidence_score", 0)

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return attributes for context and dashboard cards."""
        if self.entity_description.key != "mode":
            return {}
        recommendation = (self.coordinator.data or {}).get("recommendation", {})
        inputs = (self.coordinator.data or {}).get("inputs", {})
        input_sources = (self.coordinator.data or {}).get("input_sources", {})
        missing_inputs = (self.coordinator.data or {}).get("missing_inputs", [])
        return {
            "reason": recommendation.get("reason", ""),
            "confidence_score": recommendation.get("confidence_score", 0),
            "actions": recommendation.get("actions", []),
            "weights": recommendation.get("weights", {}),
            "weighted_signal": recommendation.get("weighted_signal", 0),
            "inputs": inputs,
            "input_sources": input_sources,
            "missing_inputs": missing_inputs,
        }
