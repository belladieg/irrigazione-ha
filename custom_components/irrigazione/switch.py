"""Entità switch virtuali per i toggle del sistema irrigazione."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DOMAIN,
    ENTITIES,
    KEY_ABILITATA,
    KEY_SLOT_1_ATTIVO, KEY_SLOT_2_ATTIVO, KEY_SLOT_3_ATTIVO,
    KEY_LUN, KEY_MAR, KEY_MER, KEY_GIO, KEY_VEN, KEY_SAB, KEY_DOM,
    KEY_SKIP_PREVISTA, KEY_SKIP_RECENTE, KEY_RIDUCI,
)


@dataclass
class IrrigazioneSwitchDescription(SwitchEntityDescription):
    key: str = ""
    default: bool = False


# Prefissi logici → ordine alfabetico: Controllo, Fascia 1/2/3, Giorni, Meteo
SWITCHES: tuple[IrrigazioneSwitchDescription, ...] = (
    # ── Controllo ──────────────────────────────────────────
    IrrigazioneSwitchDescription(
        key=KEY_ABILITATA,
        name="Controllo - Sistema attivo",
        icon="mdi:sprinkler-variant",
        default=True,
    ),
    # ── Fasce orarie ───────────────────────────────────────
    IrrigazioneSwitchDescription(
        key=KEY_SLOT_1_ATTIVO,
        name="Fascia 1 - Attiva",
        icon="mdi:clock-check-outline",
        default=True,
    ),
    IrrigazioneSwitchDescription(
        key=KEY_SLOT_2_ATTIVO,
        name="Fascia 2 - Attiva",
        icon="mdi:clock-check-outline",
        default=False,
    ),
    IrrigazioneSwitchDescription(
        key=KEY_SLOT_3_ATTIVO,
        name="Fascia 3 - Attiva",
        icon="mdi:clock-check-outline",
        default=False,
    ),
    # ── Giorni ─────────────────────────────────────────────
    IrrigazioneSwitchDescription(key=KEY_LUN, name="Giorni - Lunedì",    icon="mdi:calendar-today", default=True),
    IrrigazioneSwitchDescription(key=KEY_MAR, name="Giorni - Martedì",   icon="mdi:calendar-today", default=True),
    IrrigazioneSwitchDescription(key=KEY_MER, name="Giorni - Mercoledì", icon="mdi:calendar-today", default=True),
    IrrigazioneSwitchDescription(key=KEY_GIO, name="Giorni - Giovedì",   icon="mdi:calendar-today", default=True),
    IrrigazioneSwitchDescription(key=KEY_VEN, name="Giorni - Venerdì",   icon="mdi:calendar-today", default=True),
    IrrigazioneSwitchDescription(key=KEY_SAB, name="Giorni - Sabato",    icon="mdi:calendar-today", default=False),
    IrrigazioneSwitchDescription(key=KEY_DOM, name="Giorni - Domenica",  icon="mdi:calendar-today", default=False),
    # ── Meteo ──────────────────────────────────────────────
    IrrigazioneSwitchDescription(
        key=KEY_SKIP_PREVISTA,
        name="Meteo - Salta se pioggia prevista",
        icon="mdi:weather-rainy",
        default=True,
    ),
    IrrigazioneSwitchDescription(
        key=KEY_SKIP_RECENTE,
        name="Meteo - Salta se pioggia recente",
        icon="mdi:weather-pouring",
        default=True,
    ),
    IrrigazioneSwitchDescription(
        key=KEY_RIDUCI,
        name="Meteo - Riduci se ha piovuto",
        icon="mdi:water-minus",
        default=True,
    ),
)

WEEKDAY_KEY_MAP = {
    0: KEY_LUN, 1: KEY_MAR, 2: KEY_MER, 3: KEY_GIO,
    4: KEY_VEN, 5: KEY_SAB, 6: KEY_DOM,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entities = [IrrigazioneSwitch(entry.entry_id, desc) for desc in SWITCHES]
    async_add_entities(entities)
    store = hass.data[DOMAIN][entry.entry_id].setdefault(ENTITIES, {})
    for entity in entities:
        store[entity.key] = entity


class IrrigazioneSwitch(RestoreEntity, SwitchEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry_id: str, description: IrrigazioneSwitchDescription) -> None:
        self._entry_id = entry_id
        self.key = description.key
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_icon = description.icon
        self._attr_is_on = description.default

    @property
    def device_info(self) -> dict[str, Any]:
        return {"identifiers": {(DOMAIN, self._entry_id)}}

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if last_state := await self.async_get_last_state():
            self._attr_is_on = last_state.state == STATE_ON

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._attr_is_on = False
        self.async_write_ha_state()
