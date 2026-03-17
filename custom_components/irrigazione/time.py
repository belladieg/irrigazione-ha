"""Entità time per gli orari delle fasce di irrigazione."""
from __future__ import annotations

import datetime
from typing import Any

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DOMAIN, ENTITIES,
    DEFAULT_SLOT_1, DEFAULT_SLOT_2, DEFAULT_SLOT_3,
    KEY_ORA_SLOT_1, KEY_ORA_SLOT_2, KEY_ORA_SLOT_3,
)

# Prefisso "Fascia N" → si ordina con i switch "Fascia N - Attiva"
TIMES = (
    (KEY_ORA_SLOT_1, "Fascia 1 - Orario", DEFAULT_SLOT_1),
    (KEY_ORA_SLOT_2, "Fascia 2 - Orario", DEFAULT_SLOT_2),
    (KEY_ORA_SLOT_3, "Fascia 3 - Orario", DEFAULT_SLOT_3),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entities = [IrrigazioneTime(entry.entry_id, key, name, default) for key, name, default in TIMES]
    async_add_entities(entities)
    store = hass.data[DOMAIN][entry.entry_id].setdefault(ENTITIES, {})
    for entity in entities:
        store[entity.key] = entity


class IrrigazioneTime(RestoreEntity, TimeEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_icon = "mdi:clock-time-four-outline"

    def __init__(self, entry_id: str, key: str, name: str, default: str) -> None:
        self._entry_id = entry_id
        self.key = key
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_name = name
        h, m = map(int, default.split(":"))
        self._attr_native_value = datetime.time(h, m, 0)

    @property
    def device_info(self) -> dict[str, Any]:
        return {"identifiers": {(DOMAIN, self._entry_id)}}

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if last_state := await self.async_get_last_state():
            try:
                parts = last_state.state.split(":")
                self._attr_native_value = datetime.time(int(parts[0]), int(parts[1]), 0)
            except (ValueError, IndexError):
                pass

    async def async_set_value(self, value: datetime.time) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()
