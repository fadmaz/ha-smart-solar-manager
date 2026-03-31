"""Binary sensors for HA Smart Solar Manager."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_BATTERY_MIN_SOC, DOMAIN, OPT_BATTERY_MIN_SOC
from .coordinator import SmartSolarCoordinator


@dataclass(frozen=True)
class SmartSolarBinarySensorDescription:
    """Description for a Smart Solar Manager binary sensor."""

    key: str
    name: str
    icon: str = "mdi:help-circle"
    device_class: BinarySensorDeviceClass | None = None


BINARY_SENSORS: tuple[SmartSolarBinarySensorDescription, ...] = (
    SmartSolarBinarySensorDescription(
        "action_needed",
        "Action Needed",
        "mdi:alert-circle",
        BinarySensorDeviceClass.PROBLEM,
    ),
    SmartSolarBinarySensorDescription(
        "battery_low",
        "Battery Low",
        "mdi:battery-alert",
        BinarySensorDeviceClass.BATTERY,
    ),
    SmartSolarBinarySensorDescription(
        "high_solar_production",
        "High Solar Production",
        "mdi:solar-power-variant",
    ),
    SmartSolarBinarySensorDescription(
        "high_grid_import",
        "High Grid Import",
        "mdi:transmission-tower-import",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Solar binary sensor entities."""
    coordinator: SmartSolarCoordinator = hass.data[DOMAIN]["entries"][entry.entry_id]
    async_add_entities(
        SmartSolarBinarySensor(coordinator, entry, description) for description in BINARY_SENSORS
    )


class SmartSolarBinarySensor(CoordinatorEntity[SmartSolarCoordinator], BinarySensorEntity):
    """Smart Solar Manager binary sensor entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SmartSolarCoordinator,
        entry: ConfigEntry,
        description: SmartSolarBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_icon = description.icon
        self._attr_device_class = description.device_class
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Smart Solar Manager",
        )

    @property
    def is_on(self) -> bool:
        """Return True if the condition is active."""
        recommendation = (self.coordinator.data or {}).get("recommendation", {})
        inputs = (self.coordinator.data or {}).get("inputs", {})

        if self.entity_description.key == "action_needed":
            # Action is needed if there are recommendations
            actions = recommendation.get("actions", [])
            return len(actions) > 0

        if self.entity_description.key == "battery_low":
            # Check if battery is below minimum SoC from options
            battery_soc = inputs.get("battery_soc")
            if battery_soc is None:
                return False
            threshold = float(
                self._entry.options.get(OPT_BATTERY_MIN_SOC, DEFAULT_BATTERY_MIN_SOC)
            )
            return battery_soc < threshold

        if self.entity_description.key == "high_solar_production":
            # High solar if surplus is above 500W
            solar_surplus = recommendation.get("solar_surplus_w", 0)
            return solar_surplus > 500

        if self.entity_description.key == "high_grid_import":
            # High grid import if above 1000W
            grid_import = inputs.get("grid_import_w", 0)
            return grid_import > 1000 if grid_import else False

        return False
