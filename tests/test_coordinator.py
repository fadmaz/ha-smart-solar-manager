"""Unit tests for Smart Solar Coordinator utilities and optimizer weight handling."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import pytest


def test_normalize_weights_default():
    """Test weight normalization with defaults."""
    optimizer_module = _load_optimizer_module()
    normalize_weights = optimizer_module._normalize_weights
    
    weights = normalize_weights({})
    
    # All weights should sum to 1.0
    total = weights["cost"] + weights["self_consumption"] + weights["battery_health"] + weights["grid"]
    assert abs(total - 1.0) < 0.001
    
    # Check defaults are used
    assert weights["cost"] == pytest.approx(0.4, rel=0.01)
    assert weights["self_consumption"] == pytest.approx(0.3, rel=0.01)
    assert weights["battery_health"] == pytest.approx(0.2, rel=0.01)
    assert weights["grid"] == pytest.approx(0.1, rel=0.01)


def test_normalize_weights_custom():
    """Test weight normalization with custom values."""
    optimizer_module = _load_optimizer_module()
    normalize_weights = optimizer_module._normalize_weights
    
    weights = normalize_weights({
        "goal_cost_weight": 50,
        "goal_self_consumption_weight": 30,
        "goal_battery_health_weight": 10,
        "goal_grid_weight": 10,
    })
    
    # All weights should sum to 1.0
    total = weights["cost"] + weights["self_consumption"] + weights["battery_health"] + weights["grid"]
    assert abs(total - 1.0) < 0.001
    
    # Check proportions
    assert weights["cost"] == pytest.approx(0.5, rel=0.01)


def test_normalize_weights_zero_sum():
    """Test weight normalization with all zero weights."""
    optimizer_module = _load_optimizer_module()
    normalize_weights = optimizer_module._normalize_weights
    
    weights = normalize_weights({
        "goal_cost_weight": 0,
        "goal_self_consumption_weight": 0,
        "goal_battery_health_weight": 0,
        "goal_grid_weight": 0,
    })
    
    # Should fall back to defaults
    assert weights["cost"] == pytest.approx(0.4, rel=0.01)
    assert weights["self_consumption"] == pytest.approx(0.3, rel=0.01)
    assert weights["battery_health"] == pytest.approx(0.2, rel=0.01)
    assert weights["grid"] == pytest.approx(0.1, rel=0.01)


def _load_optimizer_module():
    """Load optimizer module without Home Assistant dependencies."""
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
