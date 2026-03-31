# HA Smart Solar Manager

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/fadmaz/ha-smart-solar-manager)](https://github.com/fadmaz/ha-smart-solar-manager/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A forecast-aware solar energy optimization integration for Home Assistant. It reads your solar forecast, live power metrics, and battery state, then recommends and optionally executes the best action for your system at any given moment.

> [!WARNING]
> **This integration is under active development. Breaking changes may occur before v1.0. Do not use in production without thorough testing.**

---

## Table of Contents

- [What It Does](#what-it-does)
- [Key Features](#key-features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Options](#options)
- [Entities Reference](#entities-reference)
- [Optimization Modes](#optimization-modes)
- [Services](#services)
- [Automation Examples](#automation-examples)
- [Safety Model](#safety-model)
- [Dashboard](#dashboard)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## What It Does

HA Smart Solar Manager acts as a lightweight decision engine between your solar/battery setup and Home Assistant automations. It:

1. Reads solar forecast data from [Forecast.Solar](https://www.home-assistant.io/integrations/forecast_solar/) or any compatible integration
2. Reads live power metrics: PV generation, home load, battery SoC, grid import/export
3. Calculates a weighted optimization signal based on your configured goals
4. Publishes a mode and recommended actions as HA entities every N minutes
5. Optionally executes those actions automatically via the `execute_plan` service

It does not communicate with inverters directly. It works through entities already exposed by your existing integrations (Solarman, GivEnergy, Victron, SolarEdge, Solax, and others).

---

## Key Features

- 5 optimization modes: protect battery, conserve battery, run flexible loads, reduce grid import, hold
- 4 strategy presets: Balanced, Save Money, Use Solar, Protect Battery, plus fully customizable weights
- 14 entities created automatically: 9 sensors, 4 binary sensors, 1 switch
- Single device card: all entities grouped under one HA device
- Energy Dashboard auto-fill: entity fields pre-populated from existing HA Energy Dashboard configuration
- Flexible grid sensors: supports dedicated import/export sensors or a single signed net-grid sensor
- Unit-agnostic input: accepts W/kW/MW for power and Wh/kWh/MWh for energy with automatic conversion
- Safe by default: automatic control is off and dry-run is on
- Multi-instance support: add multiple entries to manage multiple sites independently

---

## Requirements

| Requirement | Notes |
|---|---|
| Home Assistant | 2024.1 or newer recommended |
| HACS | Recommended installation method |
| Solar forecast entities | At least one entity from [Forecast.Solar](https://www.home-assistant.io/integrations/forecast_solar/) or equivalent |
| Live power entities | Optional but strongly recommended for meaningful optimization |

---

## Installation

### Via HACS (Recommended)

1. Open HACS in Home Assistant.
2. Click the menu (top-right) and select Custom repositories.
3. Add `https://github.com/fadmaz/ha-smart-solar-manager` as type Integration.
4. Search for HA Smart Solar Manager and click Download.
5. Restart Home Assistant.

### Manual

1. Download the latest release archive from [GitHub Releases](https://github.com/fadmaz/ha-smart-solar-manager/releases).
2. Copy `custom_components/ha_smart_solar_manager` to `config/custom_components/ha_smart_solar_manager/`.
3. Restart Home Assistant.

---

## Configuration

Go to Settings -> Devices & Services -> Add Integration and search for HA Smart Solar Manager.

The setup wizard has four steps:

### Step 1: General Settings

| Field | Description | Default |
|---|---|---|
| Name | Friendly profile name | `Smart Solar Manager` |
| Refresh interval (minutes) | How often optimizer recalculates | `15` |

### Step 2: Forecast Inputs

At least one of the first two fields is required.

| Field | Description | Unit |
|---|---|---|
| Forecast today | Total expected solar production today | Wh or kWh |
| Forecast remaining today | Remaining production for the rest of today | Wh or kWh |
| Forecast next hour | Expected production in the next hour | W or kW |
| Forecast tomorrow | Total expected production tomorrow | Wh or kWh |

Tip: These fields auto-populate when Forecast.Solar standard entities are present:
`sensor.energy_production_today`, `sensor.energy_production_today_remaining`, `sensor.energy_next_hour`, `sensor.energy_production_tomorrow`.

### Step 3: Energy Signals

All fields are optional but improve optimizer accuracy.

| Field | Description | Unit |
|---|---|---|
| PV power entity | Current solar generation | W / kW / MW |
| Load power entity | Current total home consumption | W / kW / MW |
| Battery SoC entity | Battery charge level | 0-100 % |
| Grid import entity | Grid power drawn from network | W / kW / MW |
| Grid export entity | Power exported to network | W / kW / MW |

Grid sensor modes:

| Your setup | Grid import field | Grid export field |
|---|---|---|
| Separate import + export sensors | Import sensor | Export sensor |
| Signed net-grid sensor (positive = import) | Net-grid sensor | Leave blank |
| Signed net-grid sensor (positive = export) | Leave blank | Net-grid sensor |
| Import only, no export data | Import sensor | Leave blank |

When your Energy Dashboard is configured, these fields are pre-filled from detected sources. Review and override before saving.

### Step 4: Controllable Devices

Select entities the integration may turn on during `run_flexible_loads` mode (for example: water heater, EV charger, washing machine).

A Manual Override switch is created automatically. No extra helper entity is required.

---

## Options

Open options via Settings -> Devices & Services -> HA Smart Solar Manager -> Configure.

### General

| Option | Description | Default |
|---|---|---|
| Enable automatic control | Allow `execute_plan` to apply actions automatically | Off |
| Dry-run mode | Log actions but do not execute device service calls | On |
| Strategy preset | Auto-configure optimization weights | `Balanced` |
| Minimum battery reserve (%) | Battery SoC floor | `20` |
| Grid energy price (per kWh) | Used for estimated savings | `0.20` |

### Strategy Presets

| Preset | Best for | Cost | Self-use | Battery | Grid |
|---|---|---|---|---|---|
| Balanced | General household use | 40 | 30 | 20 | 10 |
| Save Money | High electricity tariffs | 60 | 15 | 15 | 10 |
| Use Solar | Maximize self-consumption | 20 | 50 | 20 | 10 |
| Protect Battery | Extend battery lifespan | 20 | 20 | 50 | 10 |
| Custom | Advanced manual tuning | - | - | - | - |

Selecting Custom opens a second page for manual weight values (0-100). Weights are normalized internally.

---

## Entities Reference

All entities are grouped under one HA device named after your profile.

### Sensors

| Entity | Description | Unit | Attributes |
|---|---|---|---|
| `sensor.*_smart_solar_mode` | Current optimization mode | - | `reason`, `actions`, `weights`, `weighted_signal`, `inputs` |
| `sensor.*_smart_solar_reason` | Explanation for the current mode | - | - |
| `sensor.*_smart_solar_next_action` | First recommended action (`command entity_id`) | - | - |
| `sensor.*_smart_solar_estimated_savings_hour` | Estimated cost savings for this hour | currency | - |
| `sensor.*_smart_solar_surplus` | Solar generation minus current load | W | - |
| `sensor.*_smart_solar_battery_soc` | Battery state of charge | % | - |
| `sensor.*_smart_solar_grid_import` | Grid import power | W | - |
| `sensor.*_smart_solar_pv_power` | PV generation power | W | - |
| `sensor.*_smart_solar_efficiency_score` | Self-consumption efficiency score | % | - |

### Binary Sensors

| Entity | Device Class | Turns ON when |
|---|---|---|
| `binary_sensor.*_action_needed` | Problem | Recommended actions list is non-empty |
| `binary_sensor.*_battery_low` | Battery | Battery SoC is below configured minimum reserve |
| `binary_sensor.*_high_solar_production` | - | Solar surplus exceeds 500 W |
| `binary_sensor.*_high_grid_import` | - | Grid import exceeds 1000 W |

### Switch

| Entity | Description |
|---|---|
| `switch.*_manual_override` | Turn ON to block automatic execution. State is restored after restart. |

---

## Optimization Modes

| Mode | Triggered when | Effect |
|---|---|---|
| `protect_battery` | Battery SoC below minimum reserve | Blocks flexible loads (highest priority) |
| `conserve_battery` | Low forecast day and battery near reserve | Avoids non-essential consumption |
| `run_flexible_loads` | Solar surplus > 300 W and strong next-hour forecast | Turns on configured controllable devices |
| `reduce_grid_import` | Grid import > 500 W while battery above reserve | Signals load shifting or battery support |
| `hold` | No other condition matched | No action recommended |

Priority order: `protect_battery` -> `conserve_battery` -> `run_flexible_loads` -> `reduce_grid_import` -> `hold`

---

## Services

### `ha_smart_solar_manager.recompute_plan`

Forces an immediate optimizer recalculation.

```yaml
service: ha_smart_solar_manager.recompute_plan
data: {}
```

Target one entry:

```yaml
service: ha_smart_solar_manager.recompute_plan
data:
  entry_id: "abc123def456"
```

### `ha_smart_solar_manager.execute_plan`

Executes recommended actions with safety checks.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `entry_id` | string | all entries | Limit execution to one entry |
| `force` | boolean | `false` | Bypass manual override and auto-control check |
| `dry_run` | boolean | options value | Override dry-run for one call |

```yaml
service: ha_smart_solar_manager.execute_plan
data: {}
```

```yaml
service: ha_smart_solar_manager.execute_plan
data:
  force: true
  dry_run: false
```

---

## Automation Examples

### Turn on water heater during solar surplus

```yaml
alias: Solar surplus heat water
trigger:
  - platform: state
    entity_id: binary_sensor.smart_solar_high_solar_production
    to: "on"
condition:
  - condition: state
    entity_id: switch.smart_solar_manual_override
    state: "off"
action:
  - service: switch.turn_on
    target:
      entity_id: switch.water_heater
```

### Auto-execute plan on mode updates

```yaml
alias: Auto execute solar plan
trigger:
  - platform: state
    entity_id: sensor.smart_solar_mode
action:
  - service: ha_smart_solar_manager.execute_plan
    data:
      force: false
      dry_run: false
```

### Notify on low battery

```yaml
alias: Battery low notification
trigger:
  - platform: state
    entity_id: binary_sensor.smart_solar_battery_low
    to: "on"
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "Battery Low"
      message: "Solar battery is below the configured minimum reserve."
```

### Recompute before automation run

```yaml
alias: Pre automation recompute
trigger:
  - platform: time
    at: "07:00:00"
action:
  - service: ha_smart_solar_manager.recompute_plan
    data: {}
  - delay: "00:00:10"
  - service: ha_smart_solar_manager.execute_plan
    data:
      dry_run: false
```

---

## Safety Model

Safe defaults:

| Safety Layer | Default | How to change |
|---|---|---|
| Automatic control | Disabled | Enable `auto_control_enabled` |
| Dry-run mode | Enabled | Disable `dry_run` in options or pass `dry_run: false` |
| Manual Override switch | Off | Turn `switch.*_manual_override` ON to pause execution |
| Per-device error isolation | Always active | Failing device action is logged; remaining actions continue |

`force: true` on `execute_plan` bypasses manual override and auto-control checks. Use for explicit testing only.

---

## Dashboard

Example Lovelace configuration is available in [dashboard/smart_solar_dashboard.yaml](dashboard/smart_solar_dashboard.yaml).

It includes:
- Mode and reason
- Binary sensor status cards
- Estimated savings and solar surplus
- Manual Override control
- Recompute and execute service buttons

To use:
1. Open Lovelace dashboard in edit mode.
2. Add Card -> Manual.
3. Paste the content from `dashboard/smart_solar_dashboard.yaml`.
4. Adjust entity names to match your profile.

---

## Troubleshooting

**Only mode sensor appears**
Check logs for platform setup errors under `ha_smart_solar_manager`.

**All sensors are unknown or unavailable**
At least one forecast entity must be mapped and have a valid state. Check for warning:
`All solar inputs are None for entry <id>; check entity configuration`

**Cannot add a second integration instance**
Multi-instance support requires v0.11.0 or newer.

**Estimated savings always 0**
Savings are only calculated in `run_flexible_loads` and `reduce_grid_import`. Ensure `grid_price` is positive.

**Actions are not executing**
1. Ensure `auto_control_enabled` is ON or use `force: true`
2. Ensure `dry_run` is OFF or pass `dry_run: false`
3. Ensure `switch.*_manual_override` is OFF
4. Ensure target entities exist and are controllable

---

## Contributing

Issues and pull requests are welcome at [github.com/fadmaz/ha-smart-solar-manager](https://github.com/fadmaz/ha-smart-solar-manager/issues).

## License

[MIT](LICENSE)
