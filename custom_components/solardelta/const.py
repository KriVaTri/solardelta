from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "solardelta"
PLATFORMS: list[Platform] = [Platform.SENSOR]

# Config keys
CONF_NAME = "name"
CONF_SOLAR_ENTITY = "solar_entity"

# Grid config: either one net grid sensor, or two separate sensors
CONF_GRID_ENTITY = "grid_entity"  # single net grid sensor (export +, import -)
CONF_GRID_SEPARATE = "grid_separate"  # bool: use separate import/export sensors
CONF_GRID_IMPORT_ENTITY = "grid_import_entity"  # positive import
CONF_GRID_EXPORT_ENTITY = "grid_export_entity"  # positive export

CONF_DEVICE_ENTITY = "device_entity"
CONF_STATUS_ENTITY = "status_entity"
CONF_STATUS_STRING = "status_string"
CONF_RESET_ENTITY = "reset_entity"
CONF_RESET_STRING = "reset_string"
