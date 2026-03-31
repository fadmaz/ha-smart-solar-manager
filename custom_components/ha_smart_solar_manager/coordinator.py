"""Coordinator for Smart Solar Manager."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

_LOGGER = logging.getLogger(__name__)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_BATTERY_SOC_ENTITY,
    CONF_CONTROLLABLE_DEVICES,
    CONF_FORECAST_NEXT_HOUR_ENTITY,
    CONF_FORECAST_REMAINING_TODAY_ENTITY,
    CONF_FORECAST_TODAY_ENTITY,
    CONF_FORECAST_TOMORROW_ENTITY,
    CONF_GRID_EXPORT_ENTITY,
    CONF_GRID_IMPORT_ENTITY,
    CONF_LOAD_POWER_ENTITY,
    CONF_PV_POWER_ENTITY,
    CONF_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    EVENT_PLAN_COMPUTED,
    UPDATE_INTERVAL_FALLBACK,
)
from .optimizer import build_recommendation


class SmartSolarCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Track smart solar context and recommendations."""

    _POWER_UNIT_FACTORS = {
        "w": 1.0,
        "kw": 1000.0,
        "mw": 1000000.0,
    }
    _ENERGY_UNIT_FACTORS = {
        "wh": 0.001,
        "kwh": 1.0,
        "mwh": 1000.0,
    }

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        interval_minutes = int(entry.data.get(CONF_SCAN_INTERVAL_MINUTES, 15))
        update_interval = (
            timedelta(minutes=interval_minutes)
            if interval_minutes >= 5
            else UPDATE_INTERVAL_FALLBACK
        )

        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=update_interval,
        )
        self.entry = entry

    def _state_float(self, entity_id: str | None) -> float | None:
        if not entity_id:
            return None
        state_obj = self.hass.states.get(entity_id)
        if state_obj is None:
            return None
        try:
            return float(state_obj.state)
        except (TypeError, ValueError):
            return None

    def _normalized_state_float(
        self,
        entity_id: str | None,
        *,
        unit_factors: dict[str, float],
    ) -> float | None:
        """Return state normalized to the target unit when possible."""
        if not entity_id:
            return None

        state_obj = self.hass.states.get(entity_id)
        if state_obj is None:
            return None

        try:
            value = float(state_obj.state)
        except (TypeError, ValueError):
            return None

        raw_unit = str(state_obj.attributes.get("unit_of_measurement", "")).strip().lower()
        normalized_unit = raw_unit.replace(" ", "")
        factor = unit_factors.get(normalized_unit)
        if factor is None:
            return value

        return value * factor

    def _state_power_w(self, entity_id: str | None) -> float | None:
        """Return a power entity normalized to watts."""
        return self._normalized_state_float(entity_id, unit_factors=self._POWER_UNIT_FACTORS)

    def _state_energy_kwh(self, entity_id: str | None) -> float | None:
        """Return an energy entity normalized to kWh."""
        return self._normalized_state_float(entity_id, unit_factors=self._ENERGY_UNIT_FACTORS)

    def _grid_channels_from_import_entity(
        self, entity_id: str | None
    ) -> tuple[float | None, float | None]:
        """Interpret an import field as dedicated import or signed net grid power."""
        value = self._state_power_w(entity_id)
        if value is None:
            return None, None
        if value >= 0:
            return value, 0.0
        return 0.0, abs(value)

    def _grid_channels_from_export_entity(
        self, entity_id: str | None
    ) -> tuple[float | None, float | None]:
        """Interpret an export field as dedicated export or signed net grid power."""
        value = self._state_power_w(entity_id)
        if value is None:
            return None, None
        if value >= 0:
            return 0.0, value
        return abs(value), 0.0

    async def _async_update_data(self) -> dict[str, Any]:
        import_from_import, export_from_import = self._grid_channels_from_import_entity(
            self.entry.data.get(CONF_GRID_IMPORT_ENTITY)
        )
        import_from_export, export_from_export = self._grid_channels_from_export_entity(
            self.entry.data.get(CONF_GRID_EXPORT_ENTITY)
        )

        grid_import_w: float | None = None
        for candidate in (import_from_import, import_from_export):
            if candidate is not None:
                grid_import_w = max(grid_import_w or 0.0, candidate)

        grid_export_w: float | None = None
        for candidate in (export_from_import, export_from_export):
            if candidate is not None:
                grid_export_w = max(grid_export_w or 0.0, candidate)

        inputs: dict[str, Any] = {
            "forecast_today_kwh": self._state_energy_kwh(
                self.entry.data.get(CONF_FORECAST_TODAY_ENTITY)
            ),
            "forecast_remaining_today_kwh": self._state_energy_kwh(
                self.entry.data.get(CONF_FORECAST_REMAINING_TODAY_ENTITY)
            ),
            "forecast_next_hour_w": self._state_power_w(
                self.entry.data.get(CONF_FORECAST_NEXT_HOUR_ENTITY)
            ),
            "forecast_tomorrow_kwh": self._state_energy_kwh(
                self.entry.data.get(CONF_FORECAST_TOMORROW_ENTITY)
            ),
            "pv_power_w": self._state_power_w(self.entry.data.get(CONF_PV_POWER_ENTITY)),
            "load_power_w": self._state_power_w(self.entry.data.get(CONF_LOAD_POWER_ENTITY)),
            "battery_soc": self._state_float(self.entry.data.get(CONF_BATTERY_SOC_ENTITY)),
            "grid_import_w": grid_import_w,
            "grid_export_w": grid_export_w,
        }

        if all(v is None for v in inputs.values()):
            _LOGGER.warning(
                "All solar inputs are None for entry %s; check entity configuration",
                self.entry.entry_id,
            )

        controllable_devices = self.entry.data.get(CONF_CONTROLLABLE_DEVICES, [])

        recommendation = build_recommendation(
            inputs=inputs,
            options=self.entry.options,
            controllable_devices=controllable_devices,
        )

        self.hass.bus.async_fire(
            EVENT_PLAN_COMPUTED,
            {
                "entry_id": self.entry.entry_id,
                "mode": recommendation.get("mode", "unknown"),
                "confidence_score": recommendation.get("confidence_score", 0),
                "action_count": len(recommendation.get("actions", [])),
            },
        )

        return {
            "inputs": inputs,
            "recommendation": recommendation,
        }
