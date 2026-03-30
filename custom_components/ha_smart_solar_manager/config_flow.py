"""Config flow for HA Smart Solar Manager."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_BATTERY_SOC_ENTITY,
    CONF_CONTROLLABLE_DEVICES,
    CONF_FORECAST_NEXT_HOUR_ENTITY,
    CONF_FORECAST_TODAY_ENTITY,
    CONF_GRID_EXPORT_ENTITY,
    CONF_GRID_IMPORT_ENTITY,
    CONF_LOAD_POWER_ENTITY,
    CONF_MANUAL_OVERRIDE_ENTITY,
    CONF_NAME,
    CONF_PV_POWER_ENTITY,
    CONF_SCAN_INTERVAL_MINUTES,
    DEFAULT_BATTERY_MIN_SOC,
    DEFAULT_GOAL_BATTERY_HEALTH_WEIGHT,
    DEFAULT_GOAL_COST_WEIGHT,
    DEFAULT_GOAL_GRID_WEIGHT,
    DEFAULT_GOAL_SELF_CONSUMPTION_WEIGHT,
    DEFAULT_GRID_PRICE,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    OPT_AUTO_CONTROL_ENABLED,
    OPT_BATTERY_MIN_SOC,
    OPT_DRY_RUN,
    OPT_GOAL_BATTERY_HEALTH_WEIGHT,
    OPT_GOAL_COST_WEIGHT,
    OPT_GOAL_GRID_WEIGHT,
    OPT_GOAL_SELF_CONSUMPTION_WEIGHT,
    OPT_GRID_PRICE,
)


class SmartSolarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Solar Manager."""

    VERSION = 1
    _draft_data: dict[str, Any]

    def __init__(self) -> None:
        """Initialize config flow."""
        self._draft_data = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle general settings step."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        errors: dict[str, str] = {}

        if user_input is not None:
            interval = int(user_input[CONF_SCAN_INTERVAL_MINUTES])

            if interval < 5 or interval > 120:
                errors["base"] = "invalid_interval"
            else:
                self._draft_data[CONF_NAME] = user_input[CONF_NAME]
                self._draft_data[CONF_SCAN_INTERVAL_MINUTES] = interval
                return await self.async_step_forecast()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_NAME,
                    default=self._draft_data.get(CONF_NAME, DEFAULT_NAME),
                ): str,
                vol.Required(
                    CONF_SCAN_INTERVAL_MINUTES,
                    default=self._draft_data.get(
                        CONF_SCAN_INTERVAL_MINUTES,
                        DEFAULT_SCAN_INTERVAL_MINUTES,
                    ),
                ): int,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_forecast(self, user_input: dict[str, Any] | None = None):
        """Handle forecast fields group."""
        errors: dict[str, str] = {}

        if user_input is not None:
            forecast_today = user_input.get(CONF_FORECAST_TODAY_ENTITY, "").strip()
            forecast_next_hour = user_input.get(CONF_FORECAST_NEXT_HOUR_ENTITY, "").strip()

            if not forecast_today and not forecast_next_hour:
                errors["base"] = "forecast_required"
            else:
                self._draft_data[CONF_FORECAST_TODAY_ENTITY] = forecast_today
                self._draft_data[CONF_FORECAST_NEXT_HOUR_ENTITY] = forecast_next_hour
                return await self.async_step_energy()

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_FORECAST_TODAY_ENTITY,
                    default=self._draft_data.get(CONF_FORECAST_TODAY_ENTITY, ""),
                ): str,
                vol.Optional(
                    CONF_FORECAST_NEXT_HOUR_ENTITY,
                    default=self._draft_data.get(CONF_FORECAST_NEXT_HOUR_ENTITY, ""),
                ): str,
            }
        )
        return self.async_show_form(step_id="forecast", data_schema=schema, errors=errors)

    async def async_step_energy(self, user_input: dict[str, Any] | None = None):
        """Handle energy entity fields group."""
        if user_input is not None:
            self._draft_data[CONF_PV_POWER_ENTITY] = user_input.get(
                CONF_PV_POWER_ENTITY, ""
            ).strip()
            self._draft_data[CONF_LOAD_POWER_ENTITY] = user_input.get(
                CONF_LOAD_POWER_ENTITY, ""
            ).strip()
            self._draft_data[CONF_BATTERY_SOC_ENTITY] = user_input.get(
                CONF_BATTERY_SOC_ENTITY, ""
            ).strip()
            self._draft_data[CONF_GRID_IMPORT_ENTITY] = user_input.get(
                CONF_GRID_IMPORT_ENTITY, ""
            ).strip()
            self._draft_data[CONF_GRID_EXPORT_ENTITY] = user_input.get(
                CONF_GRID_EXPORT_ENTITY, ""
            ).strip()
            return await self.async_step_control()

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_PV_POWER_ENTITY,
                    default=self._draft_data.get(CONF_PV_POWER_ENTITY, ""),
                ): str,
                vol.Optional(
                    CONF_LOAD_POWER_ENTITY,
                    default=self._draft_data.get(CONF_LOAD_POWER_ENTITY, ""),
                ): str,
                vol.Optional(
                    CONF_BATTERY_SOC_ENTITY,
                    default=self._draft_data.get(CONF_BATTERY_SOC_ENTITY, ""),
                ): str,
                vol.Optional(
                    CONF_GRID_IMPORT_ENTITY,
                    default=self._draft_data.get(CONF_GRID_IMPORT_ENTITY, ""),
                ): str,
                vol.Optional(
                    CONF_GRID_EXPORT_ENTITY,
                    default=self._draft_data.get(CONF_GRID_EXPORT_ENTITY, ""),
                ): str,
            }
        )
        return self.async_show_form(step_id="energy", data_schema=schema)

    async def async_step_control(self, user_input: dict[str, Any] | None = None):
        """Handle control and override fields group."""
        if user_input is not None:
            self._draft_data[CONF_MANUAL_OVERRIDE_ENTITY] = user_input.get(
                CONF_MANUAL_OVERRIDE_ENTITY, ""
            ).strip()
            controllable_raw = user_input.get(CONF_CONTROLLABLE_DEVICES, "")
            self._draft_data[CONF_CONTROLLABLE_DEVICES] = [
                entity.strip() for entity in controllable_raw.split(",") if entity.strip()
            ]

            payload = {
                CONF_NAME: self._draft_data[CONF_NAME],
                CONF_SCAN_INTERVAL_MINUTES: self._draft_data[CONF_SCAN_INTERVAL_MINUTES],
                CONF_FORECAST_TODAY_ENTITY: self._draft_data.get(
                    CONF_FORECAST_TODAY_ENTITY, ""
                ),
                CONF_FORECAST_NEXT_HOUR_ENTITY: self._draft_data.get(
                    CONF_FORECAST_NEXT_HOUR_ENTITY, ""
                ),
                CONF_PV_POWER_ENTITY: self._draft_data.get(CONF_PV_POWER_ENTITY, ""),
                CONF_LOAD_POWER_ENTITY: self._draft_data.get(CONF_LOAD_POWER_ENTITY, ""),
                CONF_BATTERY_SOC_ENTITY: self._draft_data.get(
                    CONF_BATTERY_SOC_ENTITY, ""
                ),
                CONF_GRID_IMPORT_ENTITY: self._draft_data.get(CONF_GRID_IMPORT_ENTITY, ""),
                CONF_GRID_EXPORT_ENTITY: self._draft_data.get(CONF_GRID_EXPORT_ENTITY, ""),
                CONF_MANUAL_OVERRIDE_ENTITY: self._draft_data.get(
                    CONF_MANUAL_OVERRIDE_ENTITY, ""
                ),
                CONF_CONTROLLABLE_DEVICES: self._draft_data.get(
                    CONF_CONTROLLABLE_DEVICES, []
                ),
            }
            return self.async_create_entry(title=payload[CONF_NAME], data=payload)

        existing_devices = self._draft_data.get(CONF_CONTROLLABLE_DEVICES, [])
        existing_devices_text = ", ".join(existing_devices)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_MANUAL_OVERRIDE_ENTITY,
                    default=self._draft_data.get(CONF_MANUAL_OVERRIDE_ENTITY, ""),
                ): str,
                vol.Optional(
                    CONF_CONTROLLABLE_DEVICES,
                    default=existing_devices_text,
                ): str,
            }
        )
        return self.async_show_form(step_id="control", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Return options flow handler."""
        return SmartSolarOptionsFlow(config_entry)


class SmartSolarOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Smart Solar Manager."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self._config_entry.options

        schema = vol.Schema(
            {
                vol.Required(
                    OPT_AUTO_CONTROL_ENABLED,
                    default=options.get(OPT_AUTO_CONTROL_ENABLED, False),
                ): bool,
                vol.Required(
                    OPT_DRY_RUN,
                    default=options.get(OPT_DRY_RUN, True),
                ): bool,
                vol.Required(
                    OPT_BATTERY_MIN_SOC,
                    default=options.get(OPT_BATTERY_MIN_SOC, DEFAULT_BATTERY_MIN_SOC),
                ): vol.All(int, vol.Range(min=5, max=95)),
                vol.Required(
                    OPT_GRID_PRICE,
                    default=options.get(OPT_GRID_PRICE, DEFAULT_GRID_PRICE),
                ): vol.All(float, vol.Range(min=0)),
                vol.Required(
                    OPT_GOAL_COST_WEIGHT,
                    default=options.get(OPT_GOAL_COST_WEIGHT, DEFAULT_GOAL_COST_WEIGHT),
                ): vol.All(int, vol.Range(min=0, max=100)),
                vol.Required(
                    OPT_GOAL_SELF_CONSUMPTION_WEIGHT,
                    default=options.get(
                        OPT_GOAL_SELF_CONSUMPTION_WEIGHT,
                        DEFAULT_GOAL_SELF_CONSUMPTION_WEIGHT,
                    ),
                ): vol.All(int, vol.Range(min=0, max=100)),
                vol.Required(
                    OPT_GOAL_BATTERY_HEALTH_WEIGHT,
                    default=options.get(
                        OPT_GOAL_BATTERY_HEALTH_WEIGHT,
                        DEFAULT_GOAL_BATTERY_HEALTH_WEIGHT,
                    ),
                ): vol.All(int, vol.Range(min=0, max=100)),
                vol.Required(
                    OPT_GOAL_GRID_WEIGHT,
                    default=options.get(OPT_GOAL_GRID_WEIGHT, DEFAULT_GOAL_GRID_WEIGHT),
                ): vol.All(int, vol.Range(min=0, max=100)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
