"""Constants for HA Smart Solar Manager."""

from datetime import timedelta

DOMAIN = "ha_smart_solar_manager"
PLATFORMS = ["sensor", "switch", "binary_sensor"]

DEFAULT_NAME = "Smart Solar Manager"
DEFAULT_SCAN_INTERVAL_MINUTES = 15
DEFAULT_BATTERY_MIN_SOC = 20
DEFAULT_GOAL_COST_WEIGHT = 40
DEFAULT_GOAL_SELF_CONSUMPTION_WEIGHT = 30
DEFAULT_GOAL_BATTERY_HEALTH_WEIGHT = 20
DEFAULT_GOAL_GRID_WEIGHT = 10
DEFAULT_GRID_PRICE = 0.20

CONF_NAME = "name"
CONF_SCAN_INTERVAL_MINUTES = "scan_interval_minutes"
CONF_FORECAST_TODAY_ENTITY = "forecast_today_entity"
CONF_FORECAST_NEXT_HOUR_ENTITY = "forecast_next_hour_entity"
CONF_FORECAST_REMAINING_TODAY_ENTITY = "forecast_remaining_today_entity"
CONF_FORECAST_TOMORROW_ENTITY = "forecast_tomorrow_entity"
CONF_PV_POWER_ENTITY = "pv_power_entity"
CONF_LOAD_POWER_ENTITY = "load_power_entity"
CONF_BATTERY_SOC_ENTITY = "battery_soc_entity"
CONF_GRID_IMPORT_ENTITY = "grid_import_entity"
CONF_GRID_EXPORT_ENTITY = "grid_export_entity"
CONF_MANUAL_OVERRIDE_ENTITY = "manual_override_entity"
CONF_CONTROLLABLE_DEVICES = "controllable_devices"

OPT_AUTO_CONTROL_ENABLED = "auto_control_enabled"
OPT_DRY_RUN = "dry_run"
OPT_MODE_PRESET = "mode_preset"
OPT_BATTERY_MIN_SOC = "battery_min_soc"
OPT_GRID_PRICE = "grid_price"
OPT_GOAL_COST_WEIGHT = "goal_cost_weight"
OPT_GOAL_SELF_CONSUMPTION_WEIGHT = "goal_self_consumption_weight"
OPT_GOAL_BATTERY_HEALTH_WEIGHT = "goal_battery_health_weight"
OPT_GOAL_GRID_WEIGHT = "goal_grid_weight"

# Smart preset modes
PRESET_BALANCED = "balanced"
PRESET_SAVE_MONEY = "save_money"
PRESET_USE_SOLAR = "use_solar"
PRESET_PROTECT_BATTERY = "protect_battery"
PRESET_CUSTOM = "custom"

# Preset weight configurations
PRESET_WEIGHTS = {
    PRESET_BALANCED: {
        OPT_GOAL_COST_WEIGHT: 40,
        OPT_GOAL_SELF_CONSUMPTION_WEIGHT: 30,
        OPT_GOAL_BATTERY_HEALTH_WEIGHT: 20,
        OPT_GOAL_GRID_WEIGHT: 10,
    },
    PRESET_SAVE_MONEY: {
        OPT_GOAL_COST_WEIGHT: 60,
        OPT_GOAL_SELF_CONSUMPTION_WEIGHT: 15,
        OPT_GOAL_BATTERY_HEALTH_WEIGHT: 15,
        OPT_GOAL_GRID_WEIGHT: 10,
    },
    PRESET_USE_SOLAR: {
        OPT_GOAL_COST_WEIGHT: 20,
        OPT_GOAL_SELF_CONSUMPTION_WEIGHT: 50,
        OPT_GOAL_BATTERY_HEALTH_WEIGHT: 20,
        OPT_GOAL_GRID_WEIGHT: 10,
    },
    PRESET_PROTECT_BATTERY: {
        OPT_GOAL_COST_WEIGHT: 20,
        OPT_GOAL_SELF_CONSUMPTION_WEIGHT: 20,
        OPT_GOAL_BATTERY_HEALTH_WEIGHT: 50,
        OPT_GOAL_GRID_WEIGHT: 10,
    },
}

SERVICE_RECOMPUTE_PLAN = "recompute_plan"
SERVICE_EXECUTE_PLAN = "execute_plan"

ATTR_MODE = "mode"
ATTR_REASON = "reason"
ATTR_ACTIONS = "actions"
ATTR_ESTIMATED_SAVINGS = "estimated_savings"
ATTR_CONFIDENCE_SCORE = "confidence_score"

EVENT_PLAN_COMPUTED = f"{DOMAIN}_plan_computed"
EVENT_ACTION_EXECUTED = f"{DOMAIN}_action_executed"
EVENT_ACTION_FAILED = f"{DOMAIN}_action_failed"
EVENT_SAFETY_BLOCKED = f"{DOMAIN}_safety_blocked"

UPDATE_INTERVAL_FALLBACK = timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES)
