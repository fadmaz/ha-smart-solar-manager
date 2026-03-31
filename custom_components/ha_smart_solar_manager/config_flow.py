"""Config flow for HA Smart Solar Manager."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers import entity_registry as er

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


FORECAST_ENTITY_DEFAULTS = {
    CONF_FORECAST_TODAY_ENTITY: "sensor.energy_production_today",
    CONF_FORECAST_REMAINING_TODAY_ENTITY: "sensor.energy_production_today_remaining",
    CONF_FORECAST_NEXT_HOUR_ENTITY: "sensor.energy_next_hour",
    CONF_FORECAST_TOMORROW_ENTITY: "sensor.energy_production_tomorrow",
}


def _forecast_default_entity(hass: Any, field_name: str) -> str:
    """Return the exact forecast entity default if it exists."""
    entity_id = FORECAST_ENTITY_DEFAULTS[field_name]
    return entity_id if hass.states.get(entity_id) is not None else ""


async def _detect_from_energy_dashboard(hass: Any) -> dict[str, str]:
    """Pre-fill entity mappings from the HA Energy Dashboard configuration."""
    detected: dict[str, str] = {}
    try:
        from homeassistant.components.energy.data import async_get_manager  # noqa: PLC0415

        manager = await async_get_manager(hass)
        if not manager.data:
            return detected
    except Exception:  # noqa: BLE001
        return detected

    registry = er.async_get(hass)

    def _config_entry_for_entity(entity_id: str) -> str | None:
        entry = registry.async_get(entity_id)
        return entry.config_entry_id if entry else None

    def _power_entities_for_config_entry(config_entry_id: str, keywords: list[str]) -> str | None:
        """Find a power-class sensor from a config entry, preferring keyword matches."""
        candidates: list[str] = []
        for reg_entry in registry.entities.values():
            if reg_entry.config_entry_id != config_entry_id:
                continue
            state = hass.states.get(reg_entry.entity_id)
            if state is None:
                continue
            if state.attributes.get("device_class") == "power":
                candidates.append(reg_entry.entity_id)
        if not candidates:
            return None
        for keyword in keywords:
            for c in candidates:
                name = (hass.states.get(c).attributes.get("friendly_name") or c).lower()
                if keyword in name:
                    return c
        return candidates[0]

    for source in manager.data.get("energy_sources", []):
        stype = source.get("type")

        if stype == "battery":
            soc = source.get("stat_percentage")
            if soc and CONF_BATTERY_SOC_ENTITY not in detected:
                detected[CONF_BATTERY_SOC_ENTITY] = soc

        elif stype == "solar" and CONF_PV_POWER_ENTITY not in detected:
            energy_entity = source.get("stat_energy_from")
            entry_id = _config_entry_for_entity(energy_entity) if energy_entity else None
            if entry_id:
                found = _power_entities_for_config_entry(
                    entry_id, ["pv", "solar", "generation", "production"]
                )
                if found:
                    detected[CONF_PV_POWER_ENTITY] = found

        elif stype == "grid":
            for flow in source.get("flow_from", []):
                energy_entity = flow.get("stat_energy_from")
                entry_id = _config_entry_for_entity(energy_entity) if energy_entity else None
                if entry_id and CONF_GRID_IMPORT_ENTITY not in detected:
                    found = _power_entities_for_config_entry(
                        entry_id, ["import", "grid", "from grid", "consumed"]
                    )
                    if found:
                        detected[CONF_GRID_IMPORT_ENTITY] = found
            for flow in source.get("flow_to", []):
                energy_entity = flow.get("stat_energy_to")
                entry_id = _config_entry_for_entity(energy_entity) if energy_entity else None
                if entry_id and CONF_GRID_EXPORT_ENTITY not in detected:
                    found = _power_entities_for_config_entry(
                        entry_id, ["export", "to grid", "feed"]
                    )
                    if found:
                        detected[CONF_GRID_EXPORT_ENTITY] = found

    return detected


class SmartSolarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Solar Manager."""

    VERSION = 1
    _draft_data: dict[str, Any]
    _energy_hints: dict[str, str]

    def __init__(self) -> None:
        """Initialize config flow."""
        self._draft_data = {}
        self._energy_hints = {}

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

        forecast_defaults = {
            field_name: self._draft_data.get(
                field_name,
                _forecast_default_entity(self.hass, field_name),
            )
            for field_name in FORECAST_ENTITY_DEFAULTS
        }

        if user_input is not None:
            forecast_today = user_input.get(CONF_FORECAST_TODAY_ENTITY, "")
            forecast_next_hour = user_input.get(CONF_FORECAST_NEXT_HOUR_ENTITY, "")
            if not forecast_today and not forecast_next_hour:
                errors["base"] = "forecast_required"
            else:
                self._draft_data[CONF_FORECAST_TODAY_ENTITY] = forecast_today
                self._draft_data[CONF_FORECAST_NEXT_HOUR_ENTITY] = forecast_next_hour
                self._draft_data[CONF_FORECAST_REMAINING_TODAY_ENTITY] = user_input.get(
                    CONF_FORECAST_REMAINING_TODAY_ENTITY, ""
                )
                self._draft_data[CONF_FORECAST_TOMORROW_ENTITY] = user_input.get(
                    CONF_FORECAST_TOMORROW_ENTITY, ""
                )
                return await self.async_step_energy()

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_FORECAST_TODAY_ENTITY,
                    default=forecast_defaults[CONF_FORECAST_TODAY_ENTITY],
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(
                    CONF_FORECAST_REMAINING_TODAY_ENTITY,
                    default=forecast_defaults[CONF_FORECAST_REMAINING_TODAY_ENTITY],
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(
                    CONF_FORECAST_NEXT_HOUR_ENTITY,
                    default=forecast_defaults[CONF_FORECAST_NEXT_HOUR_ENTITY],
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(
                    CONF_FORECAST_TOMORROW_ENTITY,
                    default=forecast_defaults[CONF_FORECAST_TOMORROW_ENTITY],
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
            }
        )
        return self.async_show_form(step_id="forecast", data_schema=schema, errors=errors)

    async def async_step_energy(self, user_input: dict[str, Any] | None = None):
        """Handle energy entity fields group."""
        if not self._energy_hints:
            self._energy_hints = await _detect_from_energy_dashboard(self.hass)

        if user_input is not None:
            self._draft_data[CONF_PV_POWER_ENTITY] = user_input.get(CONF_PV_POWER_ENTITY, "")
            self._draft_data[CONF_LOAD_POWER_ENTITY] = user_input.get(CONF_LOAD_POWER_ENTITY, "")
            self._draft_data[CONF_BATTERY_SOC_ENTITY] = user_input.get(CONF_BATTERY_SOC_ENTITY, "")
            self._draft_data[CONF_GRID_IMPORT_ENTITY] = user_input.get(CONF_GRID_IMPORT_ENTITY, "")
            self._draft_data[CONF_GRID_EXPORT_ENTITY] = user_input.get(CONF_GRID_EXPORT_ENTITY, "")
            return await self.async_step_control()

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_PV_POWER_ENTITY,
                    default=self._draft_data.get(
                        CONF_PV_POWER_ENTITY,
                        self._energy_hints.get(CONF_PV_POWER_ENTITY, ""),
                    ),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(
                    CONF_LOAD_POWER_ENTITY,
                    default=self._draft_data.get(CONF_LOAD_POWER_ENTITY, ""),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(
                    CONF_BATTERY_SOC_ENTITY,
                    default=self._draft_data.get(
                        CONF_BATTERY_SOC_ENTITY,
                        self._energy_hints.get(CONF_BATTERY_SOC_ENTITY, ""),
                    ),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(
                    CONF_GRID_IMPORT_ENTITY,
                    default=self._draft_data.get(
                        CONF_GRID_IMPORT_ENTITY,
                        self._energy_hints.get(CONF_GRID_IMPORT_ENTITY, ""),
                    ),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(
                    CONF_GRID_EXPORT_ENTITY,
                    default=self._draft_data.get(
                        CONF_GRID_EXPORT_ENTITY,
                        self._energy_hints.get(CONF_GRID_EXPORT_ENTITY, ""),
                    ),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
            }
        )
        return self.async_show_form(step_id="energy", data_schema=schema)

    async def async_step_control(self, user_input: dict[str, Any] | None = None):
        """Handle control and override fields group."""
        if user_input is not None:
            self._draft_data[CONF_MANUAL_OVERRIDE_ENTITY] = user_input.get(
                CONF_MANUAL_OVERRIDE_ENTITY, ""
            )
            self._draft_data[CONF_CONTROLLABLE_DEVICES] = user_input.get(
                CONF_CONTROLLABLE_DEVICES, []
            )

            payload = {
                CONF_NAME: self._draft_data[CONF_NAME],
                CONF_SCAN_INTERVAL_MINUTES: self._draft_data[CONF_SCAN_INTERVAL_MINUTES],
                CONF_FORECAST_TODAY_ENTITY: self._draft_data.get(CONF_FORECAST_TODAY_ENTITY, ""),
                CONF_FORECAST_REMAINING_TODAY_ENTITY: self._draft_data.get(CONF_FORECAST_REMAINING_TODAY_ENTITY, ""),
                CONF_FORECAST_NEXT_HOUR_ENTITY: self._draft_data.get(CONF_FORECAST_NEXT_HOUR_ENTITY, ""),
                CONF_FORECAST_TOMORROW_ENTITY: self._draft_data.get(CONF_FORECAST_TOMORROW_ENTITY, ""),
                CONF_PV_POWER_ENTITY: self._draft_data.get(CONF_PV_POWER_ENTITY, ""),
                CONF_LOAD_POWER_ENTITY: self._draft_data.get(CONF_LOAD_POWER_ENTITY, ""),
                CONF_BATTERY_SOC_ENTITY: self._draft_data.get(CONF_BATTERY_SOC_ENTITY, ""),
                CONF_GRID_IMPORT_ENTITY: self._draft_data.get(CONF_GRID_IMPORT_ENTITY, ""),
                CONF_GRID_EXPORT_ENTITY: self._draft_data.get(CONF_GRID_EXPORT_ENTITY, ""),
                CONF_MANUAL_OVERRIDE_ENTITY: self._draft_data.get(CONF_MANUAL_OVERRIDE_ENTITY, ""),
                CONF_CONTROLLABLE_DEVICES: self._draft_data.get(CONF_CONTROLLABLE_DEVICES, []),
            }
            return self.async_create_entry(title=payload[CONF_NAME], data=payload)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_MANUAL_OVERRIDE_ENTITY,
                    default=self._draft_data.get(CONF_MANUAL_OVERRIDE_ENTITY, ""),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="input_boolean")
                ),
                vol.Optional(
                    CONF_CONTROLLABLE_DEVICES,
                    default=self._draft_data.get(CONF_CONTROLLABLE_DEVICES, []),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(multiple=True)
                ),
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
