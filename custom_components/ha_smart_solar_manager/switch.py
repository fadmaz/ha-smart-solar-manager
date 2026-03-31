"""Switch platform for HA Smart Solar Manager."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .coordinator import SmartSolarCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Solar switch entities."""
    coordinator: SmartSolarCoordinator = hass.data[DOMAIN]["entries"][entry.entry_id]
    async_add_entities([ManualOverrideSwitchEntity(coordinator, entry)])


class ManualOverrideSwitchEntity(RestoreEntity, SwitchEntity):
    """Switch to manually pause automatic solar control."""

    _attr_has_entity_name = True
    _attr_name = "Manual Override"
    _attr_icon = "mdi:hand-back-right"

    def __init__(self, coordinator: SmartSolarCoordinator, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_manual_override"
        self._is_on = False

    @property
    def is_on(self) -> bool:
        """Return True when manual override is active."""
        return self._is_on

    async def async_turn_on(self, **kwargs) -> None:
        """Activate manual override — blocks automatic execution."""
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Deactivate manual override — re-enables automatic execution."""
        self._is_on = False
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Restore previous state on startup."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._is_on = last_state.state.lower() == "on"
