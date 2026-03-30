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

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        errors: dict[str, str] = {}

        if user_input is not None:
            interval = int(user_input[CONF_SCAN_INTERVAL_MINUTES])
            forecast_today = user_input.get(CONF_FORECAST_TODAY_ENTITY, "").strip()
            forecast_next_hour = user_input.get(CONF_FORECAST_NEXT_HOUR_ENTITY, "").strip()

            if interval < 5 or interval > 120:
                errors["base"] = "invalid_interval"
            elif not forecast_today and not forecast_next_hour:
                errors["base"] = "forecast_required"
            else:
                controllable_raw = user_input.get(CONF_CONTROLLABLE_DEVICES, "")
                controllable = [
                    entity.strip()
                    for entity in controllable_raw.split(",")
                    if entity.strip()
                ]

                payload = {
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_SCAN_INTERVAL_MINUTES: interval,
                    CONF_FORECAST_TODAY_ENTITY: forecast_today,
                    CONF_FORECAST_NEXT_HOUR_ENTITY: forecast_next_hour,
                    CONF_PV_POWER_ENTITY: user_input.get(CONF_PV_POWER_ENTITY, "").strip(),
                    CONF_LOAD_POWER_ENTITY: user_input.get(CONF_LOAD_POWER_ENTITY, "").strip(),
                    CONF_BATTERY_SOC_ENTITY: user_input.get(CONF_BATTERY_SOC_ENTITY, "").strip(),
                    CONF_GRID_IMPORT_ENTITY: user_input.get(CONF_GRID_IMPORT_ENTITY, "").strip(),
                    CONF_GRID_EXPORT_ENTITY: user_input.get(CONF_GRID_EXPORT_ENTITY, "").strip(),
                    CONF_MANUAL_OVERRIDE_ENTITY: user_input.get(
                        CONF_MANUAL_OVERRIDE_ENTITY, ""
                    ).strip(),
                    CONF_CONTROLLABLE_DEVICES: controllable,
                }

                return self.async_create_entry(title=payload[CONF_NAME], data=payload)

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(
                    CONF_SCAN_INTERVAL_MINUTES,
                    default=DEFAULT_SCAN_INTERVAL_MINUTES,
                ): int,
                vol.Optional(CONF_FORECAST_TODAY_ENTITY, default=""): str,
                vol.Optional(CONF_FORECAST_NEXT_HOUR_ENTITY, default=""): str,
                vol.Optional(CONF_PV_POWER_ENTITY, default=""): str,
                vol.Optional(CONF_LOAD_POWER_ENTITY, default=""): str,
                vol.Optional(CONF_BATTERY_SOC_ENTITY, default=""): str,
                vol.Optional(CONF_GRID_IMPORT_ENTITY, default=""): str,
                vol.Optional(CONF_GRID_EXPORT_ENTITY, default=""): str,
                vol.Optional(CONF_MANUAL_OVERRIDE_ENTITY, default=""): str,
                vol.Optional(CONF_CONTROLLABLE_DEVICES, default=""): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

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
