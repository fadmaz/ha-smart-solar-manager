# HA Smart Solar Manager

Smart solar, battery, and grid energy management for Home Assistant using Forecast.Solar and your existing inverter/device entities.

## What This Integration Does

- Creates a forecast-aware recommendation engine for battery, grid, and flexible loads.
- Supports recommendation-only mode or optional automatic actions.
- Uses user-selected entities so it stays generic across inverter and device integrations.
- Exposes smart sensors for dashboard cards and automation logic.

## Current State (v0.8.1)

- Config flow for mapping Forecast.Solar and energy entities.
- Exact-match auto-fill for the four supported forecast sensors when they exist.
- Energy entity fields are pre-filled from your Home Assistant Energy Dashboard configuration when compatible sources are already configured.
- Energy Dashboard autofill now supports Home Assistant's current unified energy source schema for solar, battery, and grid sources.
- Config UI labels are unit-neutral, while supported units are normalized automatically.
- Options flow for goal weights and safety controls.
- Optimization output modes:
  - `protect_battery`
  - `run_flexible_loads`
  - `reduce_grid_import`
  - `conserve_battery`
  - `hold`
- Services:
  - `ha_smart_solar_manager.recompute_plan`
  - `ha_smart_solar_manager.execute_plan`
- Sensors:
  - Smart Solar Mode
  - Smart Solar Next Action
  - Smart Solar Estimated Savings (Hour)
  - Smart Solar Surplus

## Installation (HACS Custom Repository)

1. Open HACS in Home Assistant.
2. Add this repository as a Custom Repository of type Integration.
3. Install `HA Smart Solar Manager`.
4. Restart Home Assistant.

## Configuration

Add the integration from Home Assistant UI:

1. Go to Settings -> Devices & Services.
2. Add Integration -> `HA Smart Solar Manager`.
3. Map at least one forecast entity:

- `Forecast today entity` or
- `Forecast next hour entity`

4. Optionally map additional forecast entities:

- `Forecast remaining today entity`
- `Forecast tomorrow entity`

- These fields auto-fill when Home Assistant has these exact entities:
  `sensor.energy_production_today`, `sensor.energy_production_today_remaining`, `sensor.energy_next_hour`, `sensor.energy_production_tomorrow`

5. Optionally map energy entities:
   - PV power entity
   - Load power entity
   - Battery SoC entity
   - Grid import entity — three usage modes:
     - Dedicated import sensor (positive watts only)
     - Signed net-grid sensor (positive = import, negative = export)
     - Leave blank if not available
   - Grid export entity — optional:
     - Dedicated export sensor (positive watts only)
     - Signed net-grid sensor (positive = export, negative = import)
     - Leave blank if you use a signed import sensor or have no export data
   - Manual override boolean entity
   - Controllable device entities (multi-entity selector)

When Home Assistant Energy Dashboard is configured, the integration attempts to pre-fill these energy fields automatically:

- Battery SoC from configured battery sources
- PV power from the same config entry as your solar energy source
- Grid import/export power from the same config entries as your grid flows
- Load power from related power sensors on the same device or config entry when available

You can still review and override any detected values before saving.

The integration normalizes units automatically:

- Power entities can be in `W`, `kW`, or `MW`
- Energy entities can be in `Wh`, `kWh`, or `MWh`

Then open integration options to tune:

- `Enable automatic control`
- `Dry-run mode`
- `Minimum battery reserve`
- Goal weights for cost, self-consumption, battery health, and grid strategy

## Safety Model

- Automatic control is disabled by default.
- Dry-run is enabled by default.
- Manual override entity can block execution.
- `execute_plan` can be forced explicitly per call.

## Dashboard

An example Lovelace YAML dashboard section is provided in:

- `dashboard/smart_solar_dashboard.yaml`

It includes:

- Strategy mode and reason
- Next action
- Estimated savings
- Manual controls for recompute/execute services

## Service Examples

Recompute immediately:

```yaml
service: ha_smart_solar_manager.recompute_plan
data: {}
```

Execute action plan with safety options:

```yaml
service: ha_smart_solar_manager.execute_plan
data:
	force: false
	dry_run: true
```

## Notes

- This project is generic by design and does not hard-code one inverter vendor.
- It works best when your existing integrations already provide reliable entities.
- Future phases will add richer scheduling, cooldown windows, and broader adapter support.
