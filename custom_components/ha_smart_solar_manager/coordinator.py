"""Coordinator for Smart Solar Manager."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_BATTERY_SOC_ENTITY,
    CONF_CONTROLLABLE_DEVICES,
    CONF_FORECAST_NEXT_HOUR_ENTITY,
    CONF_FORECAST_TODAY_ENTITY,
    CONF_GRID_EXPORT_ENTITY,
    CONF_GRID_IMPORT_ENTITY,
    CONF_LOAD_POWER_ENTITY,
    CONF_PV_POWER_ENTITY,
    CONF_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    UPDATE_INTERVAL_FALLBACK,
)
from .optimizer import build_recommendation


class SmartSolarCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Track smart solar context and recommendations."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        interval_minutes = int(entry.data.get(CONF_SCAN_INTERVAL_MINUTES, 15))
        update_interval = (
            timedelta(minutes=interval_minutes)
            if interval_minutes >= 5
            else UPDATE_INTERVAL_FALLBACK
        )

        super().__init__(
            hass,
            logger=hass.data[DOMAIN]["logger"],
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

    async def _async_update_data(self) -> dict[str, Any]:
        inputs: dict[str, Any] = {
            "forecast_today_kwh": self._state_float(
                self.entry.data.get(CONF_FORECAST_TODAY_ENTITY)
            ),
            "forecast_next_hour_w": self._state_float(
                self.entry.data.get(CONF_FORECAST_NEXT_HOUR_ENTITY)
            ),
            "pv_power_w": self._state_float(self.entry.data.get(CONF_PV_POWER_ENTITY)),
            "load_power_w": self._state_float(self.entry.data.get(CONF_LOAD_POWER_ENTITY)),
            "battery_soc": self._state_float(self.entry.data.get(CONF_BATTERY_SOC_ENTITY)),
            "grid_import_w": self._state_float(self.entry.data.get(CONF_GRID_IMPORT_ENTITY)),
            "grid_export_w": self._state_float(self.entry.data.get(CONF_GRID_EXPORT_ENTITY)),
        }

        controllable_devices = self.entry.data.get(CONF_CONTROLLABLE_DEVICES, [])

        recommendation = build_recommendation(
            inputs=inputs,
            options=self.entry.options,
            controllable_devices=controllable_devices,
        )

        return {
            "inputs": inputs,
            "recommendation": recommendation,
        }
