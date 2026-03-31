# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [Unreleased]

### Added

- **optimizer.py** - Added `confidence_score` to recommendation payload (0-100) based on input completeness.
- **sensor.py** - Added `Smart Solar Confidence Score` sensor to expose recommendation confidence.
- **coordinator.py / services.py** - Added lifecycle bus events for `plan_computed`, `action_executed`, `action_failed`, and `safety_blocked`.

## [0.11.0] - 2026-03-31

### Fixed

- **coordinator.py** - Logger now uses a module-level `_LOGGER` instead of reading from `hass.data`, eliminating a `KeyError` on reload edge cases.
- **sensor.py** - `estimated_savings` unit corrected from `kWh` to unitless (value is a currency amount, not an energy value).
- **binary_sensor.py** - `battery_low` threshold now reads `battery_min_soc` from options instead of a hardcoded 30%.
- **services.py** - `execute_plan` now wraps each individual device `async_call` in `try/except`; a failure on one device no longer aborts the remaining actions.
- **switch.py** - `async_write_ha_state()` is now called after restoring state in `async_added_to_hass`, so the switch state is immediately correct after restart.
- **config_flow.py** - Removed single-instance lock; multiple entries (multi-site) are now supported.
- **optimizer.py** - Priority order corrected: `conserve_battery` now checked before `run_flexible_loads`, preventing flexible load activation on low-forecast days.

### Added

- **device_info** - All sensors, binary sensors, and the switch now declare `device_info`, grouping all 14 entities under a single device card.
- **BinarySensorDeviceClass** - `action_needed` now uses `PROBLEM` device class; `battery_low` uses `BATTERY` device class.
- **strings.json / translations/en.json** - Added missing `options.step.customize` section (custom weight labels were blank in the UI) and added `mode_preset` label to the `init` step.
- **coordinator.py** - Logs a `WARNING` when all power/forecast inputs resolve to `None`, helping diagnose misconfigured entity mappings.
- **optimizer.py** - Now consumes `forecast_remaining_today_kwh` and `grid_export_w` inputs; `conserve_battery` mode additionally triggers when remaining-today forecast drops below 0.5 kWh; `run_flexible_loads` also considers live grid export above 200 W.

### Changed

- **sensor.py** - `extra_state_attributes` restricted to the `mode` sensor only; all other sensors now return an empty dict, reducing HA database write volume significantly.
- ****init**.py** - Removed `hass.data[DOMAIN]["logger"]` storage; coordinator uses its own module-level logger.

## [0.10.0] - 2026-03-31

### Added

- **Binary Sensors** for smart automation triggers:
  - `binary_sensor.*_action_needed` - True when there's a recommended action
  - `binary_sensor.*_battery_low` - True when battery SoC < 30%
  - `binary_sensor.*_high_solar_production` - True when surplus > 500W
  - `binary_sensor.*_high_grid_import` - True when grid import > 1000W
- **Enhanced Sensors** with better integration:
  - `sensor.*_reason` - Explains WHY each recommendation was made
  - `sensor.*_battery_soc` - Real-time battery state of charge
  - `sensor.*_grid_import` - Current grid import power (W)
  - `sensor.*_pv_power` - Current PV power production (W)
  - `sensor.*_efficiency_score` - System efficiency calculation (%)
  - All sensors now have icons, state classes, and proper units
- **Smart Preset Modes** for simplified configuration:
  - Balanced (default)
  - Save Money (prioritize cost reduction)
  - Use Solar (prioritize self-consumption)
  - Protect Battery (minimize battery stress)
  - Custom (for advanced users)
- **Improved Options Flow** with two-step configuration for better UX

### Changed

- Options flow now starts with preset selection instead of weight sliders
- Custom weights are only shown when "Custom" preset is selected

## [0.9.0] - 2026-03-31

### Added

- The integration now creates its own **Manual Override** switch entity (`switch.<name>_manual_override`) automatically. No external `input_boolean` helper is required.
- Switch state is restored on Home Assistant restart via `RestoreEntity`.

### Removed

- `Manual override boolean entity` field removed from the config flow. Existing entries that had an external entity configured will use the new built-in switch instead.

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

- Smart entity auto-detection (keyword matching) - all entity fields now start blank and require manual selection.

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
