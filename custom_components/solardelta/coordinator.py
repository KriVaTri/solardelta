from __future__ import annotations

from typing import Any, Optional
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

def _state_matches(state, candidates: list[str]) -> bool:
    if state is None:
        return False
    val = str(state.state).strip().lower()
    if not candidates:
        return True
    for c in candidates:
        if val == str(c).strip().lower():
            return True
    return False

class SolarDeltaCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(
        self,
        hass: HomeAssistant,
        solar_entity: str,
        device_entity: str,
        status_entity: Optional[str] = None,
        status_string: Optional[str] = None,
        trigger_entity: Optional[str] = None,
        trigger_string_1: Optional[str] = None,
        scan_interval_seconds: int = 0,
    ) -> None:
        super().__init__(hass, name="solardelta", update_interval=None)
        self.hass = hass
        self._solar_entity = solar_entity
        self._device_entity = device_entity
        self._status_entity = status_entity
        self._status_string = status_string
        self._trigger_entity = trigger_entity
        self._trigger_string_1 = trigger_string_1
        self._periodic = bool(scan_interval_seconds and scan_interval_seconds > 0)
        self._interval_seconds = int(scan_interval_seconds or 0)
        self._unsub: list[callable] = []

    def _conditions_ok(self) -> tuple[bool, bool, bool]:
        """Return (allowed, status_ok, trigger_ok) based on configured conditions."""
        # Status check: one required string
        status_ok = True
        if self._status_entity:
            status_state = self.hass.states.get(self._status_entity)
            status_ok = _state_matches(status_state, [self._status_string] if self._status_string else [])

        # Trigger check: one required string
        trigger_ok = True
        if self._trigger_entity:
            trigger_state = self.hass.states.get(self._trigger_entity)
            trigger_ok = _state_matches(trigger_state, [self._trigger_string_1] if self._trigger_string_1 else [])

        allowed = status_ok and trigger_ok
        return allowed, status_ok, trigger_ok

    async def async_config_entry_first_refresh(self) -> None:
        # existing implementation...
        return

    async def async_shutdown(self) -> None:
        for u in self._unsub:
            try:
                u()
            except Exception:
                pass
        self._unsub.clear()

    async def async_reset_avg_year(self) -> None:
        # existing implementation...
        return
