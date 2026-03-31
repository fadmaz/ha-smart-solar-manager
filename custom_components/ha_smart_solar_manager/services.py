"""Services for HA Smart Solar Manager."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er

_LOGGER = logging.getLogger(__name__)

from .const import (
    ATTR_ACTIONS,
    DOMAIN,
    EVENT_ACTION_EXECUTED,
    EVENT_ACTION_FAILED,
    EVENT_SAFETY_BLOCKED,
    OPT_AUTO_CONTROL_ENABLED,
    OPT_DRY_RUN,
    SERVICE_EXECUTE_PLAN,
    SERVICE_RECOMPUTE_PLAN,
)


async def async_register_services(hass: HomeAssistant) -> None:
    """Register domain services."""
    if hass.services.has_service(DOMAIN, SERVICE_RECOMPUTE_PLAN):
        return

    recompute_schema = vol.Schema({vol.Optional("entry_id"): str})
    execute_schema = vol.Schema(
        {
            vol.Optional("entry_id"): str,
            vol.Optional("force", default=False): bool,
            vol.Optional("dry_run"): bool,
        }
    )

    async def _iter_target(entry_id: str | None) -> list[Any]:
        entries = hass.data[DOMAIN]["entries"]
        if entry_id:
            coordinator = entries.get(entry_id)
            return [coordinator] if coordinator else []
        return list(entries.values())

    async def handle_recompute(call: ServiceCall) -> None:
        """Force refresh recommendation data."""
        targets = await _iter_target(call.data.get("entry_id"))
        for coordinator in targets:
            await coordinator.async_request_refresh()

    async def handle_execute(call: ServiceCall) -> None:
        """Execute current recommended actions if allowed."""
        force = bool(call.data.get("force", False))
        service_dry_run = call.data.get("dry_run")
        targets = await _iter_target(call.data.get("entry_id"))

        for coordinator in targets:
            entry = coordinator.entry
            options = entry.options
            data = coordinator.data or {}
            recommendation = data.get("recommendation", {})
            actions = recommendation.get(ATTR_ACTIONS, [])

            auto_control = bool(options.get(OPT_AUTO_CONTROL_ENABLED, False))
            dry_run = bool(options.get(OPT_DRY_RUN, True))
            if service_dry_run is not None:
                dry_run = bool(service_dry_run)

            registry = er.async_get(hass)
            override_entity_id = registry.async_get_entity_id(
                "switch", DOMAIN, f"{entry.entry_id}_manual_override"
            )
            if override_entity_id:
                state = hass.states.get(override_entity_id)
                if state and state.state.lower() == "on" and not force:
                    hass.bus.async_fire(
                        EVENT_SAFETY_BLOCKED,
                        {
                            "entry_id": entry.entry_id,
                            "reason": "manual_override_enabled",
                        },
                    )
                    continue

            if not auto_control and not force:
                hass.bus.async_fire(
                    EVENT_SAFETY_BLOCKED,
                    {
                        "entry_id": entry.entry_id,
                        "reason": "auto_control_disabled",
                    },
                )
                continue

            for action in actions:
                entity_id = action.get("entity_id")
                command = action.get("command")
                if not entity_id or command not in ("turn_on", "turn_off"):
                    continue
                if dry_run:
                    continue
                domain = entity_id.split(".", 1)[0]
                try:
                    await hass.services.async_call(
                        domain,
                        command,
                        {"entity_id": entity_id},
                        blocking=True,
                    )
                    hass.bus.async_fire(
                        EVENT_ACTION_EXECUTED,
                        {
                            "entry_id": entry.entry_id,
                            "entity_id": entity_id,
                            "command": command,
                            "dry_run": dry_run,
                        },
                    )
                except Exception as err:  # noqa: BLE001
                    _LOGGER.error(
                        "Failed to execute %s on %s: %s",
                        command,
                        entity_id,
                        err,
                    )
                    hass.bus.async_fire(
                        EVENT_ACTION_FAILED,
                        {
                            "entry_id": entry.entry_id,
                            "entity_id": entity_id,
                            "command": command,
                            "error": str(err),
                        },
                    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_RECOMPUTE_PLAN,
        handle_recompute,
        schema=recompute_schema,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXECUTE_PLAN,
        handle_execute,
        schema=execute_schema,
    )


async def async_unregister_services(hass: HomeAssistant) -> None:
    """Unregister domain services."""
    if hass.services.has_service(DOMAIN, SERVICE_RECOMPUTE_PLAN):
        hass.services.async_remove(DOMAIN, SERVICE_RECOMPUTE_PLAN)
    if hass.services.has_service(DOMAIN, SERVICE_EXECUTE_PLAN):
        hass.services.async_remove(DOMAIN, SERVICE_EXECUTE_PLAN)
