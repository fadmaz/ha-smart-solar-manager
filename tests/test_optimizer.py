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


def test_build_recommendation_protects_battery_below_minimum() -> None:
    """Battery below minimum should trigger protect mode."""
    result = build_recommendation(
        inputs={
            "forecast_today_kwh": 8,
            "forecast_next_hour_w": 1500,
            "pv_power_w": 1000,
            "load_power_w": 900,
            "battery_soc": 15,
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

    assert result["mode"] == "protect_battery"
    assert not result["actions"]
    assert "Battery is below minimum" in result["reason"]


def test_build_recommendation_reduces_grid_import() -> None:
    """High grid import with sufficient battery should reduce import."""
    result = build_recommendation(
        inputs={
            "forecast_today_kwh": 8,
            "forecast_next_hour_w": 1500,
            "pv_power_w": 500,
            "load_power_w": 1000,
            "battery_soc": 70,
            "grid_import_w": 600,
        },
        options={
            "battery_min_soc": 20,
            "grid_price": 0.2,
            "goal_cost_weight": 40,
            "goal_self_consumption_weight": 30,
            "goal_battery_health_weight": 20,
            "goal_grid_weight": 10,
        },
        controllable_devices=[],
    )

    assert result["mode"] == "reduce_grid_import"
    assert "Grid import is elevated" in result["reason"]
    assert result["estimated_savings"] > 0


def test_build_recommendation_conserves_battery_low_forecast() -> None:
    """Low forecast with low battery buffer should conserve."""
    result = build_recommendation(
        inputs={
            "forecast_today_kwh": 1,
            "forecast_remaining_today_kwh": 0.3,
            "forecast_next_hour_w": 100,
            "pv_power_w": 500,
            "load_power_w": 400,
            "battery_soc": 32,
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

    assert result["mode"] == "conserve_battery"
    assert "Low forecast" in result["reason"]
    assert not result["actions"]


def test_build_recommendation_default_hold_mode() -> None:
    """Balanced conditions should result in hold mode."""
    result = build_recommendation(
        inputs={
            "forecast_today_kwh": 8,
            "forecast_next_hour_w": 1500,
            "pv_power_w": 1000,
            "load_power_w": 900,
            "battery_soc": 50,
            "grid_import_w": 100,
        },
        options={
            "battery_min_soc": 20,
            "grid_price": 0.2,
            "goal_cost_weight": 40,
            "goal_self_consumption_weight": 30,
            "goal_battery_health_weight": 20,
            "goal_grid_weight": 10,
        },
        controllable_devices=[],
    )

    assert result["mode"] == "hold"
    assert "No strong optimization signal" in result["reason"]


def test_build_recommendation_normalized_weights() -> None:
    """Weights should be normalized to sum to 1."""
    result = build_recommendation(
        inputs={
            "forecast_today_kwh": 8,
            "forecast_next_hour_w": 1500,
            "pv_power_w": 1000,
            "load_power_w": 900,
            "battery_soc": 50,
            "grid_import_w": 100,
        },
        options={
            "battery_min_soc": 20,
            "grid_price": 0.2,
            "goal_cost_weight": 40,
            "goal_self_consumption_weight": 30,
            "goal_battery_health_weight": 20,
            "goal_grid_weight": 10,
        },
        controllable_devices=[],
    )

    weights = result["weights"]
    total_weight = (
        weights["cost"]
        + weights["self_consumption"]
        + weights["battery_health"]
        + weights["grid"]
    )
    assert abs(total_weight - 1.0) < 0.001


def test_build_recommendation_handles_missing_inputs() -> None:
    """Should handle gracefully when inputs are missing."""
    result = build_recommendation(
        inputs={},
        options={
            "battery_min_soc": 20,
            "grid_price": 0.2,
            "goal_cost_weight": 40,
            "goal_self_consumption_weight": 30,
            "goal_battery_health_weight": 20,
            "goal_grid_weight": 10,
        },
        controllable_devices=[],
    )

    assert result["mode"] in ["hold", "protect_battery", "conserve_battery"]
    assert "solar_surplus_w" in result
    assert "weighted_signal" in result


def test_build_recommendation_multiple_controllable_devices() -> None:
    """Should add all controllable devices to actions when in flexible load mode."""
    result = build_recommendation(
        inputs={
            "forecast_today_kwh": 8,
            "forecast_next_hour_w": 1500,
            "pv_power_w": 3000,
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
        controllable_devices=["switch.pool_pump", "switch.water_heater", "switch.ev_charger"],
    )

    assert result["mode"] == "run_flexible_loads"
    assert len(result["actions"]) == 3
    assert result["actions"][0]["entity_id"] == "switch.pool_pump"
    assert result["actions"][1]["entity_id"] == "switch.water_heater"
    assert result["actions"][2]["entity_id"] == "switch.ev_charger"


def test_build_recommendation_savings_calculation() -> None:
    """Should calculate estimated savings correctly."""
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
            "grid_price": 0.25,
            "goal_cost_weight": 40,
            "goal_self_consumption_weight": 30,
            "goal_battery_health_weight": 20,
            "goal_grid_weight": 10,
        },
        controllable_devices=["switch.pool_pump"],
    )

    # Solar surplus: 2400 - 900 = 1500W
    # Estimated savings: (1500 / 1000) * 0.25 = 0.375
    assert result["mode"] == "run_flexible_loads"
    assert result["estimated_savings"] == 0.375


def test_build_recommendation_confidence_score_complete_inputs() -> None:
    """All core inputs present should yield full confidence."""
    result = build_recommendation(
        inputs={
            "forecast_today_kwh": 7.0,
            "forecast_remaining_today_kwh": 4.0,
            "forecast_next_hour_w": 900,
            "forecast_now_w": 950,
            "pv_power_w": 1200,
            "load_power_w": 800,
            "battery_soc": 65,
            "grid_import_w": 100,
            "grid_export_w": 50,
        },
        options={
            "battery_min_soc": 20,
            "grid_price": 0.2,
            "goal_cost_weight": 40,
            "goal_self_consumption_weight": 30,
            "goal_battery_health_weight": 20,
            "goal_grid_weight": 10,
        },
        controllable_devices=[],
    )

    assert result["confidence_score"] == 100


def test_build_recommendation_confidence_score_partial_inputs() -> None:
    """Sparse inputs should produce reduced confidence."""
    result = build_recommendation(
        inputs={
            "forecast_today_kwh": None,
            "forecast_remaining_today_kwh": None,
            "forecast_next_hour_w": None,
            "pv_power_w": 1200,
            "load_power_w": 800,
            "battery_soc": None,
            "grid_import_w": None,
            "grid_export_w": None,
        },
        options={
            "battery_min_soc": 20,
            "grid_price": 0.2,
            "goal_cost_weight": 40,
            "goal_self_consumption_weight": 30,
            "goal_battery_health_weight": 20,
            "goal_grid_weight": 10,
        },
        controllable_devices=[],
    )

    assert result["confidence_score"] == 22
