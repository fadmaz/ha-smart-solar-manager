# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [Unreleased]

## [0.8.1] - 2026-03-31

### Fixed

- Energy Dashboard autofill now reads Home Assistant's current unified energy source schema instead of legacy-only fields.
- Grid import/export and PV power hints now resolve from `stat_rate` and `power_config` when those are present in Energy Dashboard sources.
- Battery SoC and load power hints now fall back to related sensors on the same device or config entry when Energy Dashboard does not store those entities directly.

## [0.8.0] - 2026-03-31

### Added

- Energy entity fields in the config flow are now pre-filled from your Home Assistant Energy Dashboard configuration where possible.

### Changed

- Energy Signals step text now explains that compatible fields are auto-populated from Energy Dashboard settings.

## [0.7.0] - 2026-03-31

### Added

- Flexible grid sensor support. You can now use:
  - Separate dedicated grid import and export entities.
  - A single import-only entity (leave export blank).
  - A signed net-grid sensor in the import field (positive = import, negative = export).
  - A signed net-grid sensor in the export field (positive = export, negative = import).
- Config flow descriptions for grid import and export fields now explain that the export field is optional and that signed sensors are accepted.

## [0.6.0] - 2026-03-31

### Changed

- Config flow field labels no longer ask for specific units like `W` or `kWh`.
- Forecast and energy field descriptions remain unit-aware and explain that supported units are converted automatically.

## [0.5.0] - 2026-03-31

### Added

- Exact-match auto-selection for forecast entities when these sensors exist: `sensor.energy_production_today`, `sensor.energy_production_today_remaining`, `sensor.energy_next_hour`, and `sensor.energy_production_tomorrow`.

### Changed

- Power entities are now normalized automatically from `W`, `kW`, or `MW` into watts before optimization.
- Energy entities are now normalized automatically from `Wh`, `kWh`, or `MWh` into kWh before optimization.
- Config flow descriptions now explain that unit conversion is handled automatically.

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
