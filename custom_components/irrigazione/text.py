"""Entità text per i nomi delle zone."""
from __future__ import annotations

from typing import Any

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DOMAIN, ENTITIES,
    KEY_NOME_ZONA_1, KEY_NOME_ZONA_2, KEY_NOME_ZONA_3, KEY_NOME_ZONA_4,
)

# Prefisso "Zona N" → si ordina con "Zona N - Durata base" e "Zona N - Durata effettiva"
ZONE_NAMES = (
    (KEY_NOME_ZONA_1, "Zona 1 - Nome", "Zona 1"),
    (KEY_NOME_ZONA_2, "Zona 2 - Nome", "Zona 2"),
    (KEY_NOME_ZONA_3, "Zona 3 - Nome", "Zona 3"),
    (KEY_NOME_ZONA_4, "Zona 4 - Nome", "Zona 4"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entities = [IrrigazioneText(entry.entry_id, key, name, default) for key, name, default in ZONE_NAMES]
    async_add_entities(entities)
    store = hass.data[DOMAIN][entry.entry_id].setdefault(ENTITIES, {})
    for entity in entities:
        store[entity.key] = entity


class IrrigazioneText(RestoreEntity, TextEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_icon = "mdi:sprinkler"
    _attr_native_min = 1
    _attr_native_max = 40

    def __init__(self, entry_id: str, key: str, name: str, default: str) -> None:
        self._entry_id = entry_id
        self.key = key
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_name = name
        self._attr_native_value = default

    @property
    def device_info(self) -> dict[str, Any]:
        return {"identifiers": {(DOMAIN, self._entry_id)}}

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if last_state := await self.async_get_last_state():
            if last_state.state not in ("unknown", "unavailable", ""):
                self._attr_native_value = last_state.state

    async def async_set_value(self, value: str) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()
