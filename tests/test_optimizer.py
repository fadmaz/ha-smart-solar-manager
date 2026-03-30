"""Unit tests for Smart Solar optimizer."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_optimizer_module():
    optimizer_path = (
        Path(__file__).resolve().parents[1]
        / "custom_components"
        / "ha_smart_solar_manager"
        / "optimizer.py"
    )
    spec = spec_from_file_location("ha_smart_solar_optimizer", optimizer_path)
    module = module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


optimizer_module = _load_optimizer_module()
build_recommendation = optimizer_module.build_recommendation


def test_build_recommendation_prefers_flexible_loads_on_surplus() -> None:
    """Surplus solar should produce flexible load recommendation."""
    result = build_recommendation(
        inputs={
            "forecast_today_kwh": 8,
            "forecast_next_hour_w": 1500,
            "pv_power_w": 2400,
            "load_power_w": 900,
            "battery_soc": 55,
            "grid_import_w": 0,
        },
        options={
            "battery_min_soc": 20,
            "grid_price": 0.2,
            "goal_cost_weight": 40,
            "goal_self_consumption_weight": 30,
            "goal_battery_health_weight": 20,
            "goal_grid_weight": 10,
        },
        controllable_devices=["switch.pool_pump"],
    )

    assert result["mode"] == "run_flexible_loads"
    assert result["actions"]
    assert result["actions"][0]["entity_id"] == "switch.pool_pump"
