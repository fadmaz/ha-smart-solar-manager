# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [Unreleased]

## [0.4.0] - 2026-03-31

### Added

- Two new forecast entity fields in config flow: `Forecast remaining today (kWh)` and `Forecast tomorrow (kWh)`.
- Both new entities are read by the coordinator and passed to the optimizer as `forecast_remaining_today_kwh` and `forecast_tomorrow_kwh`.

### Removed

- Smart entity auto-detection (keyword matching) — all entity fields now start blank and require manual selection.

## [0.3.0] - 2026-03-31

### Fixed

- `Controllable device entities` field in config flow now uses a searchable multi-entity selector dropdown instead of a plain text comma-separated input.

## [0.2.0] - 2026-03-31

### Added

- Entity selector dropdowns for all entity field mappings in config flow.
- Smart entity auto-detection using keyword matching on entity IDs and friendly names.
- Pre-populated default values from detected entities in configuration forms.
- Improved configuration UI with searchable entity dropdowns for sensor and input_boolean domains.

## [0.1.0] - 2026-03-30

### Added

- Initial HACS integration scaffold for HA Smart Solar Manager.
- Home Assistant integration package under custom_components/ha_smart_solar_manager.
- Config flow and options flow for mapping entities and tuning optimization weights.
- Coordinator-based data refresh and recommendation engine.
- Smart solar sensors for mode, next action, estimated savings, and solar surplus.
- Domain services for plan recompute and safe execution.
- English translation strings and base UI text resources.
- Example dashboard YAML for strategy view and service controls.
- Initial optimizer unit test and local syntax validation workflow.
