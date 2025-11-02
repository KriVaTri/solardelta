class SolarCoverageAvgSessionSensor(_AvgBase):
    _file_suffix = "avg_session"

    def __init__(
        self,
        coordinator: SolarDeltaCoordinator,
        entry_id: str,
        display_name: str,
        trigger_entity: Optional[str],
    ) -> None:
        super().__init__(coordinator, entry_id, display_name)
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_avg_session"
        self._trigger_entity = trigger_entity
        self._last_trigger_norm: Optional[str] = None

    ...

    def _maybe_reset_on_update(self, now_utc) -> None:
        """Reset average when trigger changes from any known state to the configured trigger string."""
        if not self._trigger_entity:
            return

        # Normalize current trigger state
        cur_state = self.coordinator.hass.states.get(self._trigger_entity)
        cur_norm = self._normalize_state(cur_state)

        # Normalize configured trigger string (target)
        target = self.coordinator.trigger_string
        target_norm = str(target).strip().lower() if target else None

        prev = self._last_trigger_norm

        # Keep existing semantics: do NOT reset when previous is None/unknown/unavailable/target,
        # reset only when moving from some other known state to the target.
        if target_norm and prev not in (None, "unknown", "unavailable", target_norm) and cur_norm == target_norm:
            self._sum_cov_dt = 0.0
            self._sum_dt = 0.0
            self._current_value = 0

        self._last_trigger_norm = cur_norm
