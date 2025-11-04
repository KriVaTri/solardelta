from __future__ import annotations

import asyncio
import contextlib

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.util import slugify

from .const import (
    CONF_DEVICE_ENTITY,
    CONF_GRID_ENTITY,
    CONF_GRID_EXPORT_ENTITY,
    CONF_GRID_IMPORT_ENTITY,
    CONF_GRID_SEPARATE,
    CONF_NAME,
    CONF_RESET_ENTITY,
    CONF_RESET_STRING,
    CONF_SOLAR_ENTITY,
    CONF_STATUS_ENTITY,
    CONF_STATUS_STRING,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import SolarDeltaCoordinator

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    entry_name = entry.data.get(CONF_NAME) or entry.title or "SolarDelta"

    solar_entity = entry.options.get(CONF_SOLAR_ENTITY) or entry.data.get(CONF_SOLAR_ENTITY)

    # Grid config
    grid_separate = bool(
        entry.options.get(CONF_GRID_SEPARATE)
        if entry.options.get(CONF_GRID_SEPARATE) is not None
        else entry.data.get(CONF_GRID_SEPARATE) or False
    )
    grid_entity = entry.options.get(CONF_GRID_ENTITY) or entry.data.get(CONF_GRID_ENTITY)
    grid_import = entry.options.get(CONF_GRID_IMPORT_ENTITY) or entry.data.get(CONF_GRID_IMPORT_ENTITY)
    grid_export = entry.options.get(CONF_GRID_EXPORT_ENTITY) or entry.data.get(CONF_GRID_EXPORT_ENTITY)

    device_entity = entry.options.get(CONF_DEVICE_ENTITY) or entry.data.get(CONF_DEVICE_ENTITY)

    status_entity = entry.options.get(CONF_STATUS_ENTITY) or entry.data.get(CONF_STATUS_ENTITY)
    status_string = entry.options.get(CONF_STATUS_STRING) or entry.data.get(CONF_STATUS_STRING)

    reset_entity = entry.options.get(CONF_RESET_ENTITY) or entry.data.get(CONF_RESET_ENTITY)
    reset_string = entry.options.get(CONF_RESET_STRING) or entry.data.get(CONF_RESET_STRING)

    scan_interval = entry.options.get(CONF_SCAN_INTERVAL)
    if scan_interval is None:
        scan_interval = entry.data.get(CONF_SCAN_INTERVAL, 0)

    coordinator = SolarDeltaCoordinator(
        hass=hass,
        solar_entity=solar_entity,
        grid_entity=grid_entity,
        grid_separate=grid_separate,
        grid_import_entity=grid_import,
        grid_export_entity=grid_export,
        device_entity=device_entity,
        status_entity=status_entity,
        status_string=status_string,
        reset_entity=reset_entity,
        reset_string=reset_string,
        scan_interval_seconds=int(scan_interval or 0),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "name": entry_name,
        "status_entity": status_entity,
        "reset_entity": reset_entity,
        "per_entry_services": [],
    }

    suffix = slugify(entry_name).lower() or slugify(entry.entry_id).lower()

    # Build service names
    service_names = {
        "reset_avg_session": f"reset_avg_session_{suffix}",
        "reset_avg_year": f"reset_avg_year_{suffix}",
        "reset_avg_lifetime": f"reset_avg_lifetime_{suffix}",
        "reset_avg_session_grid": f"reset_avg_session_grid_{suffix}",
        "reset_avg_year_grid": f"reset_avg_year_grid_{suffix}",
        "reset_avg_lifetime_grid": f"reset_avg_lifetime_grid_{suffix}",
        "reset_all_averages": f"reset_all_averages_{suffix}",
    }

    # Map services to the entity key/method operations they should perform
    ops_by_service: dict[str, list[tuple[str, str]]] = {
        service_names["reset_avg_session"]: [("avg_session_entity", "async_reset_avg_session")],
        service_names["reset_avg_year"]: [("avg_year_entity", "async_reset_avg_year")],
        service_names["reset_avg_lifetime"]: [("avg_lifetime_entity", "async_reset_avg_lifetime")],
        service_names["reset_avg_session_grid"]: [("avg_session_grid_entity", "async_reset_avg_session")],
        service_names["reset_avg_year_grid"]: [("avg_year_grid_entity", "async_reset_avg_year")],
        service_names["reset_avg_lifetime_grid"]: [("avg_lifetime_grid_entity", "async_reset_avg_lifetime")],
        service_names["reset_all_averages"]: [
            ("avg_session_entity", "async_reset_avg_session"),
            ("avg_year_entity", "async_reset_avg_year"),
            ("avg_lifetime_entity", "async_reset_avg_lifetime"),
            ("avg_session_grid_entity", "async_reset_avg_session"),
            ("avg_year_grid_entity", "async_reset_avg_year"),
            ("avg_lifetime_grid_entity", "async_reset_avg_lifetime"),
        ],
    }

    async def _handle_reset(call: ServiceCall) -> None:
        data = hass.data[DOMAIN].get(entry.entry_id) or {}
        ops = ops_by_service.get(call.service, [])
        tasks = []
        for key, method in ops:
            ent = data.get(key)
            if ent and hasattr(ent, method):
                tasks.append(getattr(ent, method)())
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    # Register all services with the same handler
    for svc_name in service_names.values():
        hass.services.async_register(DOMAIN, svc_name, _handle_reset)

    hass.data[DOMAIN][entry.entry_id]["per_entry_services"] = list(service_names.values())

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    for svc in data.get("per_entry_services", []):
        with contextlib.suppress(Exception):
            hass.services.async_remove(DOMAIN, svc)

    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        data = hass.data[DOMAIN].pop(entry.entry_id, None)
        coordinator = data.get("coordinator") if data else None
        if coordinator:
            await coordinator.async_shutdown()
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN, None)
    return unloaded


async def _update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
