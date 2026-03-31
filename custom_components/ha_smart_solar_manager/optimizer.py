"""Recommendation and optimization logic for Smart Solar Manager."""

from __future__ import annotations

from typing import Any, Mapping

try:
    from .const import (
        DEFAULT_BATTERY_MIN_SOC,
        DEFAULT_GOAL_BATTERY_HEALTH_WEIGHT,
        DEFAULT_GOAL_COST_WEIGHT,
        DEFAULT_GOAL_GRID_WEIGHT,
        DEFAULT_GOAL_SELF_CONSUMPTION_WEIGHT,
        DEFAULT_GRID_PRICE,
        OPT_BATTERY_MIN_SOC,
        OPT_GOAL_BATTERY_HEALTH_WEIGHT,
        OPT_GOAL_COST_WEIGHT,
        OPT_GOAL_GRID_WEIGHT,
        OPT_GOAL_SELF_CONSUMPTION_WEIGHT,
        OPT_GRID_PRICE,
    )
except ImportError:
    DEFAULT_BATTERY_MIN_SOC = 20
    DEFAULT_GOAL_COST_WEIGHT = 40
    DEFAULT_GOAL_SELF_CONSUMPTION_WEIGHT = 30
    DEFAULT_GOAL_BATTERY_HEALTH_WEIGHT = 20
    DEFAULT_GOAL_GRID_WEIGHT = 10
    DEFAULT_GRID_PRICE = 0.20
    OPT_BATTERY_MIN_SOC = "battery_min_soc"
    OPT_GRID_PRICE = "grid_price"
    OPT_GOAL_COST_WEIGHT = "goal_cost_weight"
    OPT_GOAL_SELF_CONSUMPTION_WEIGHT = "goal_self_consumption_weight"
    OPT_GOAL_BATTERY_HEALTH_WEIGHT = "goal_battery_health_weight"
    OPT_GOAL_GRID_WEIGHT = "goal_grid_weight"


def _normalize_weights(options: Mapping[str, Any]) -> dict[str, float]:
    raw_cost = float(options.get(OPT_GOAL_COST_WEIGHT, DEFAULT_GOAL_COST_WEIGHT))
    raw_self = float(
        options.get(OPT_GOAL_SELF_CONSUMPTION_WEIGHT, DEFAULT_GOAL_SELF_CONSUMPTION_WEIGHT)
    )
    raw_batt = float(
        options.get(OPT_GOAL_BATTERY_HEALTH_WEIGHT, DEFAULT_GOAL_BATTERY_HEALTH_WEIGHT)
    )
    raw_grid = float(options.get(OPT_GOAL_GRID_WEIGHT, DEFAULT_GOAL_GRID_WEIGHT))

    total = raw_cost + raw_self + raw_batt + raw_grid
    if total <= 0:
        return {
            "cost": 0.4,
            "self_consumption": 0.3,
            "battery_health": 0.2,
            "grid": 0.1,
        }

    return {
        "cost": raw_cost / total,
        "self_consumption": raw_self / total,
        "battery_health": raw_batt / total,
        "grid": raw_grid / total,
    }


def _safe_float(value: Any, fallback: float = 0.0) -> float:
    try:
        if value is None:
            return fallback
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _confidence_score(inputs: Mapping[str, Any]) -> int:
    """Return recommendation confidence from data completeness (0-100)."""
    tracked_keys = (
        "forecast_today_kwh",
        "forecast_remaining_today_kwh",
        "forecast_next_hour_w",
        "forecast_now_w",
        "pv_power_w",
        "load_power_w",
        "battery_soc",
        "grid_import_w",
        "grid_export_w",
    )
    available = sum(1 for key in tracked_keys if inputs.get(key) is not None)
    return int(round((available / len(tracked_keys)) * 100))


def _should_run_flexible_loads(
    effective_surplus_w: float,
    grid_export_w: float,
    forecast_next_hour_w: float,
    forecast_now_w: float,
) -> bool:
    """Return True when there is enough surplus to justify running flexible loads."""
    # Strong live signal — no forecast confirmation needed.
    if effective_surplus_w > 400 or grid_export_w > 300:
        return True
    # Moderate surplus + at least one forecast confirmation.
    moderate_surplus = effective_surplus_w > 150 or grid_export_w > 100
    forecast_confirms = forecast_next_hour_w > 200 or forecast_now_w > 300
    return moderate_surplus and forecast_confirms


def build_recommendation(
    inputs: Mapping[str, Any], options: Mapping[str, Any], controllable_devices: list[str]
) -> dict[str, Any]:
    """Build a recommendation and optional actions from current energy context."""
    battery_min_soc = _safe_float(
        options.get(OPT_BATTERY_MIN_SOC, DEFAULT_BATTERY_MIN_SOC),
        DEFAULT_BATTERY_MIN_SOC,
    )
    grid_price = _safe_float(options.get(OPT_GRID_PRICE, DEFAULT_GRID_PRICE), DEFAULT_GRID_PRICE)
    weights = _normalize_weights(options)

    forecast_today_kwh_raw = inputs.get("forecast_today_kwh")
    forecast_remaining_today_kwh_raw = inputs.get("forecast_remaining_today_kwh")
    forecast_tomorrow_kwh_raw = inputs.get("forecast_tomorrow_kwh")

    forecast_today_kwh = _safe_float(forecast_today_kwh_raw)
    forecast_remaining_today_kwh = _safe_float(forecast_remaining_today_kwh_raw)
    forecast_next_hour_w = _safe_float(inputs.get("forecast_next_hour_w"))
    forecast_now_w = _safe_float(inputs.get("forecast_now_w"))
    forecast_tomorrow_kwh = _safe_float(forecast_tomorrow_kwh_raw)
    pv_power_w = _safe_float(inputs.get("pv_power_w"))
    load_power_w = _safe_float(inputs.get("load_power_w"))
    battery_soc = _safe_float(inputs.get("battery_soc"), fallback=50.0)
    grid_import_w = _safe_float(inputs.get("grid_import_w"))
    grid_export_w = _safe_float(inputs.get("grid_export_w"))

    # --- Effective solar surplus with a prioritised source hierarchy ---
    # 1. Grid export > 0 is the most reliable real-time ground truth.
    # 2. PV - load gives measured net production.
    # 3. Forecast-now - load when PV sensor is absent.
    # 4. Forecast-now alone if load is also unavailable.
    if grid_export_w > 0:
        effective_surplus_w = grid_export_w
        surplus_source = "grid_export"
    elif inputs.get("pv_power_w") is not None:
        effective_surplus_w = pv_power_w - load_power_w
        surplus_source = "pv_minus_load"
    elif inputs.get("forecast_now_w") is not None:
        effective_surplus_w = forecast_now_w - load_power_w
        surplus_source = "forecast_now_minus_load"
    else:
        effective_surplus_w = forecast_now_w
        surplus_source = "forecast_now"

    mode = "hold"
    reason = "No strong optimization signal."

    # Battery below minimum: protect first, unconditionally.
    if battery_soc < battery_min_soc:
        mode = "protect_battery"
        reason = "Battery is below minimum reserve. Avoid extra discharge and flexible loads."

    # Conserve battery only when forecast data is actually present.
    elif (
        forecast_today_kwh_raw is not None
        and forecast_remaining_today_kwh_raw is not None
        and (forecast_today_kwh < 2 or forecast_remaining_today_kwh < 0.5)
        and battery_soc < battery_min_soc + 15
        # Relax conservation if tomorrow has plenty of sun.
        and forecast_tomorrow_kwh < 5.0
    ):
        mode = "conserve_battery"
        reason = "Low forecast day detected. Preserve battery for critical demand."

    # Run flexible loads: strong live surplus requires no forecast confirmation.
    # Moderate surplus is accepted when at least one forecast signal confirms.
    elif _should_run_flexible_loads(
        effective_surplus_w, grid_export_w, forecast_next_hour_w, forecast_now_w
    ):
        mode = "run_flexible_loads"
        reason = "Solar surplus is available. Shift flexible consumption now."

    elif grid_import_w > 500 and battery_soc > battery_min_soc + 10:
        mode = "reduce_grid_import"
        reason = "Grid import is elevated while battery reserve allows support."

    actions: list[dict[str, str]] = []
    if mode == "run_flexible_loads":
        for entity_id in controllable_devices:
            actions.append(
                {
                    "entity_id": entity_id,
                    "command": "turn_on",
                    "reason": "Solar surplus available",
                }
            )

    weighted_signal = (
        weights["cost"] * max(grid_import_w, 0.0)
        + weights["self_consumption"] * max(effective_surplus_w, 0.0)
        + weights["battery_health"] * max(battery_soc - battery_min_soc, 0.0)
        + weights["grid"] * max(forecast_next_hour_w, 0.0)
    )

    estimated_savings = 0.0
    if mode == "run_flexible_loads" and effective_surplus_w > 0:
        estimated_savings = round((effective_surplus_w / 1000.0) * grid_price, 4)
    elif mode == "reduce_grid_import" and grid_import_w > 0:
        estimated_savings = round((min(grid_import_w, 800.0) / 1000.0) * grid_price, 4)

    return {
        "mode": mode,
        "reason": reason,
        "actions": actions,
        "estimated_savings": estimated_savings,
        "confidence_score": _confidence_score(inputs),
        "solar_surplus_w": round(effective_surplus_w, 2),
        "surplus_source": surplus_source,
        "weighted_signal": round(weighted_signal, 2),
        "weights": weights,
    }
