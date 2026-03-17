"""Entità button per avvio manuale e stop irrigazione."""
from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SCHEDULER


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities(
        [
            IrrigazioneAvviaButton(hass, entry.entry_id),
            IrrigazioneFermaButton(hass, entry.entry_id),
        ]
    )


class _IrrigazioneButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self.hass = hass
        self._entry_id = entry_id

    @property
    def device_info(self) -> dict[str, Any]:
        return {"identifiers": {(DOMAIN, self._entry_id)}}

    def _get_scheduler(self):
        return self.hass.data[DOMAIN][self._entry_id].get(SCHEDULER)


class IrrigazioneAvviaButton(_IrrigazioneButton):
    # Prefisso "Controllo" → si ordina accanto a "Controllo - Sistema attivo"
    _attr_name = "Controllo - Avvia sequenza"
    _attr_icon = "mdi:play-circle-outline"

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        super().__init__(hass, entry_id)
        self._attr_unique_id = f"{entry_id}_btn_avvia"

    async def async_press(self) -> None:
        scheduler = self._get_scheduler()
        if scheduler:
            await scheduler.async_start_sequence(manual=True)


class IrrigazioneFermaButton(_IrrigazioneButton):
    _attr_name = "Controllo - Ferma tutto"
    _attr_icon = "mdi:stop-circle-outline"

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        super().__init__(hass, entry_id)
        self._attr_unique_id = f"{entry_id}_btn_ferma"

    async def async_press(self) -> None:
        scheduler = self._get_scheduler()
        if scheduler:
            await scheduler.async_stop()
