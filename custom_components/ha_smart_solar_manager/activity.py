"""Activity logging helpers for Smart Solar Manager."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN


async def async_log_activity(
    hass: HomeAssistant,
    *,
    entry_id: str,
    name: str,
    message: str,
    entity_key: str = "mode",
) -> None:
    """Write a logbook entry linked to an integration entity when possible."""
    if not hass.services.has_service("logbook", "log"):
        return

    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id("sensor", DOMAIN, f"{entry_id}_{entity_key}")
    if entity_id is None:
        entity_id = registry.async_get_entity_id("switch", DOMAIN, f"{entry_id}_manual_override")

    data = {
        "name": name,
        "message": message,
    }
    if entity_id is not None:
        data["entity_id"] = entity_id

    await hass.services.async_call("logbook", "log", data, blocking=True)