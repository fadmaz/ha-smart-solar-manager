"""Constants for HA Smart Solar Manager."""

from datetime import timedelta

DOMAIN = "ha_smart_solar_manager"
PLATFORMS = ["sensor"]

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
CONF_PV_POWER_ENTITY = "pv_power_entity"
CONF_LOAD_POWER_ENTITY = "load_power_entity"
CONF_BATTERY_SOC_ENTITY = "battery_soc_entity"
CONF_GRID_IMPORT_ENTITY = "grid_import_entity"
CONF_GRID_EXPORT_ENTITY = "grid_export_entity"
CONF_MANUAL_OVERRIDE_ENTITY = "manual_override_entity"
CONF_CONTROLLABLE_DEVICES = "controllable_devices"

OPT_AUTO_CONTROL_ENABLED = "auto_control_enabled"
OPT_DRY_RUN = "dry_run"
OPT_BATTERY_MIN_SOC = "battery_min_soc"
OPT_GRID_PRICE = "grid_price"
OPT_GOAL_COST_WEIGHT = "goal_cost_weight"
OPT_GOAL_SELF_CONSUMPTION_WEIGHT = "goal_self_consumption_weight"
OPT_GOAL_BATTERY_HEALTH_WEIGHT = "goal_battery_health_weight"
OPT_GOAL_GRID_WEIGHT = "goal_grid_weight"

SERVICE_RECOMPUTE_PLAN = "recompute_plan"
SERVICE_EXECUTE_PLAN = "execute_plan"

ATTR_MODE = "mode"
ATTR_REASON = "reason"
ATTR_ACTIONS = "actions"
ATTR_ESTIMATED_SAVINGS = "estimated_savings"

UPDATE_INTERVAL_FALLBACK = timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES)
