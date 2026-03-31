"""Entity detection helpers for Smart Solar Manager."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_BATTERY_SOC_ENTITY,
    CONF_FORECAST_NEXT_HOUR_ENTITY,
    CONF_FORECAST_REMAINING_TODAY_ENTITY,
    CONF_FORECAST_TODAY_ENTITY,
    CONF_FORECAST_TOMORROW_ENTITY,
    CONF_GRID_EXPORT_ENTITY,
    CONF_GRID_IMPORT_ENTITY,
    CONF_LOAD_POWER_ENTITY,
    CONF_PV_POWER_ENTITY,
)

FORECAST_ENTITY_DEFAULTS = {
    CONF_FORECAST_TODAY_ENTITY: "sensor.energy_production_today",
    CONF_FORECAST_REMAINING_TODAY_ENTITY: "sensor.energy_production_today_remaining",
    CONF_FORECAST_NEXT_HOUR_ENTITY: "sensor.energy_next_hour",
    CONF_FORECAST_TOMORROW_ENTITY: "sensor.energy_production_tomorrow",
}


def _entity_exists(hass: Any, entity_id: str | None) -> bool:
    """Return whether an entity exists in state machine."""
    return bool(entity_id and hass.states.get(entity_id) is not None)


def default_forecast_entity(hass: Any, field_name: str) -> str:
    """Return the standard forecast entity when available."""
    entity_id = FORECAST_ENTITY_DEFAULTS[field_name]
    return entity_id if _entity_exists(hass, entity_id) else ""


def _source_power_entity(hass: Any, source: dict[str, Any]) -> str:
    """Return the normalized power entity for an energy source when available."""
    stat_rate = source.get("stat_rate")
    if _entity_exists(hass, stat_rate):
        return stat_rate

    power_config = source.get("power_config") or {}
    direct_rate = power_config.get("stat_rate")
    if _entity_exists(hass, direct_rate):
        return direct_rate

    return ""


def _source_related_entity_ids(hass: Any, source: dict[str, Any]) -> list[str]:
    """Collect entity IDs related to an Energy Dashboard source."""
    candidates = [
        source.get("stat_energy_from"),
        source.get("stat_energy_to"),
        source.get("stat_rate"),
    ]

    power_config = source.get("power_config") or {}
    candidates.extend(
        [
            power_config.get("stat_rate"),
            power_config.get("stat_rate_inverted"),
            power_config.get("stat_rate_from"),
            power_config.get("stat_rate_to"),
        ]
    )

    related: list[str] = []
    seen: set[str] = set()
    for entity_id in candidates:
        if not _entity_exists(hass, entity_id) or entity_id in seen:
            continue
        seen.add(entity_id)
        related.append(entity_id)
    return related


def _candidate_entities_for_related(
    registry: er.EntityRegistry,
    related_entity_ids: list[str],
) -> list[str]:
    """Return entities on the same devices or config entries as related entities."""
    config_entry_ids: set[str] = set()
    device_ids: set[str] = set()

    for entity_id in related_entity_ids:
        entry = registry.async_get(entity_id)
        if entry is None:
            continue
        if entry.config_entry_id:
            config_entry_ids.add(entry.config_entry_id)
        if entry.device_id:
            device_ids.add(entry.device_id)

    ordered: list[str] = []
    seen: set[str] = set()
    for reg_entry in registry.entities.values():
        if reg_entry.device_id not in device_ids:
            continue
        if reg_entry.entity_id in seen:
            continue
        seen.add(reg_entry.entity_id)
        ordered.append(reg_entry.entity_id)

    for reg_entry in registry.entities.values():
        if reg_entry.config_entry_id not in config_entry_ids:
            continue
        if reg_entry.entity_id in seen:
            continue
        seen.add(reg_entry.entity_id)
        ordered.append(reg_entry.entity_id)

    return ordered


def _pick_matching_entity(
    hass: Any,
    candidates: list[str],
    *,
    keywords: list[str],
    excluded: set[str] | None = None,
    require_power: bool = False,
    prefer_battery_percent: bool = False,
) -> str:
    """Pick the best matching entity from related candidates."""
    best_entity = ""
    best_score = -1
    excluded = excluded or set()

    for entity_id in candidates:
        if entity_id in excluded or not entity_id.startswith("sensor."):
            continue

        state = hass.states.get(entity_id)
        if state is None:
            continue

        device_class = state.attributes.get("device_class")
        unit = state.attributes.get("unit_of_measurement")
        if require_power and device_class != "power" and unit not in {"W", "kW", "MW"}:
            continue

        if prefer_battery_percent and device_class != "battery" and unit != "%":
            continue

        haystack = f"{entity_id} {(state.attributes.get('friendly_name') or '')}".lower()
        score = 0

        if require_power:
            score += 30
            if state.attributes.get("state_class") == "measurement":
                score += 5

        if prefer_battery_percent:
            if device_class == "battery":
                score += 40
            if unit == "%":
                score += 10

        for index, keyword in enumerate(keywords):
            if keyword in haystack:
                score += 20 - index

        if score > best_score:
            best_entity = entity_id
            best_score = score

    return best_entity


async def async_detect_energy_entities(hass: Any) -> dict[str, str]:
    """Detect likely source entities from Energy Dashboard and common defaults."""
    detected: dict[str, str] = {
        field_name: entity_id
        for field_name, entity_id in FORECAST_ENTITY_DEFAULTS.items()
        if _entity_exists(hass, entity_id)
    }

    try:
        from homeassistant.components.energy.data import async_get_manager  # noqa: PLC0415

        manager = await async_get_manager(hass)
        if not manager.data:
            return detected
    except Exception:  # noqa: BLE001
        return detected

    registry = er.async_get(hass)
    related_for_load: list[str] = []
    picked_entities: set[str] = set(detected.values())

    for source in manager.data.get("energy_sources", []):
        stype = source.get("type")
        related = _source_related_entity_ids(hass, source)
        related_for_load.extend(entity_id for entity_id in related if entity_id not in related_for_load)
        related_candidates = _candidate_entities_for_related(registry, related)

        if stype == "battery" and CONF_BATTERY_SOC_ENTITY not in detected:
            battery_soc = _pick_matching_entity(
                hass,
                related_candidates,
                keywords=["soc", "state of charge", "battery", "charge level"],
                excluded=picked_entities,
                prefer_battery_percent=True,
            )
            if battery_soc:
                detected[CONF_BATTERY_SOC_ENTITY] = battery_soc
                picked_entities.add(battery_soc)

        elif stype == "solar" and CONF_PV_POWER_ENTITY not in detected:
            pv_power = _source_power_entity(hass, source)
            if not pv_power:
                pv_power = _pick_matching_entity(
                    hass,
                    related_candidates,
                    keywords=["pv", "solar", "generation", "production"],
                    excluded=picked_entities,
                    require_power=True,
                )
            if pv_power:
                detected[CONF_PV_POWER_ENTITY] = pv_power
                picked_entities.add(pv_power)

        elif stype == "grid":
            power_config = source.get("power_config") or {}

            if CONF_GRID_IMPORT_ENTITY not in detected:
                grid_import = ""
                if _entity_exists(hass, power_config.get("stat_rate_from")):
                    grid_import = power_config["stat_rate_from"]
                elif _entity_exists(hass, source.get("stat_rate")):
                    grid_import = source["stat_rate"]
                elif _entity_exists(hass, power_config.get("stat_rate")):
                    grid_import = power_config["stat_rate"]
                else:
                    grid_import = _pick_matching_entity(
                        hass,
                        related_candidates,
                        keywords=["grid import", "from grid", "import", "consumed", "grid"],
                        excluded=picked_entities,
                        require_power=True,
                    )
                if grid_import:
                    detected[CONF_GRID_IMPORT_ENTITY] = grid_import
                    picked_entities.add(grid_import)

            if CONF_GRID_EXPORT_ENTITY not in detected:
                grid_export = ""
                if _entity_exists(hass, power_config.get("stat_rate_to")):
                    grid_export = power_config["stat_rate_to"]
                elif _entity_exists(hass, power_config.get("stat_rate_inverted")):
                    grid_export = power_config["stat_rate_inverted"]
                else:
                    grid_export = _pick_matching_entity(
                        hass,
                        related_candidates,
                        keywords=["grid export", "to grid", "export", "feed", "return"],
                        excluded=picked_entities,
                        require_power=True,
                    )
                if grid_export:
                    detected[CONF_GRID_EXPORT_ENTITY] = grid_export
                    picked_entities.add(grid_export)

    if CONF_LOAD_POWER_ENTITY not in detected:
        load_candidates = _candidate_entities_for_related(registry, related_for_load)
        load_power = _pick_matching_entity(
            hass,
            load_candidates,
            keywords=["load", "consumption", "house", "home", "usage"],
            excluded=picked_entities,
            require_power=True,
        )
        if load_power:
            detected[CONF_LOAD_POWER_ENTITY] = load_power

    return detected