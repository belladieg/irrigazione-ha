"""Entità number per impostazioni durate e soglie."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DOMAIN,
    ENTITIES,
    DEFAULT_DURATA,
    DEFAULT_ATTESA,
    DEFAULT_SOGLIA_PREVISTA,
    DEFAULT_SOGLIA_STORICA,
    DEFAULT_GIORNI,
    KEY_ZONA_1_DURATA,
    KEY_ZONA_2_DURATA,
    KEY_ZONA_3_DURATA,
    KEY_ZONA_4_DURATA,
    KEY_ATTESA,
    KEY_SOGLIA_PREVISTA,
    KEY_SOGLIA_STORICA,
    KEY_GIORNI,
)


@dataclass
class IrrigazioneNumberDescription(NumberEntityDescription):
    key: str = ""
    default: float = 0.0


NUMBERS: tuple[IrrigazioneNumberDescription, ...] = (
    IrrigazioneNumberDescription(
        key=KEY_ZONA_1_DURATA,
        name="Zona 1 - Durata base",
        native_min_value=1,
        native_max_value=120,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        mode=NumberMode.BOX,
        icon="mdi:timer-outline",
        default=DEFAULT_DURATA,
    ),
    IrrigazioneNumberDescription(
        key=KEY_ZONA_2_DURATA,
        name="Zona 2 - Durata base",
        native_min_value=1,
        native_max_value=120,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        mode=NumberMode.BOX,
        icon="mdi:timer-outline",
        default=DEFAULT_DURATA,
    ),
    IrrigazioneNumberDescription(
        key=KEY_ZONA_3_DURATA,
        name="Zona 3 - Durata base",
        native_min_value=1,
        native_max_value=120,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        mode=NumberMode.BOX,
        icon="mdi:timer-outline",
        default=DEFAULT_DURATA,
    ),
    IrrigazioneNumberDescription(
        key=KEY_ZONA_4_DURATA,
        name="Zona 4 - Durata base",
        native_min_value=1,
        native_max_value=120,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        mode=NumberMode.BOX,
        icon="mdi:timer-outline",
        default=DEFAULT_DURATA,
    ),
    IrrigazioneNumberDescription(
        key=KEY_ATTESA,
        name="Attesa tra zone",
        native_min_value=0,
        native_max_value=600,
        native_step=5,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        mode=NumberMode.SLIDER,
        icon="mdi:timer-pause-outline",
        default=DEFAULT_ATTESA,
    ),
    IrrigazioneNumberDescription(
        key=KEY_SOGLIA_PREVISTA,
        name="Soglia pioggia prevista",
        native_min_value=0.5,
        native_max_value=30,
        native_step=0.5,
        native_unit_of_measurement="mm",
        mode=NumberMode.BOX,
        icon="mdi:weather-rainy",
        default=DEFAULT_SOGLIA_PREVISTA,
    ),
    IrrigazioneNumberDescription(
        key=KEY_SOGLIA_STORICA,
        name="Soglia pioggia storica",
        native_min_value=1,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement="mm",
        mode=NumberMode.BOX,
        icon="mdi:weather-pouring",
        default=DEFAULT_SOGLIA_STORICA,
    ),
    IrrigazioneNumberDescription(
        key=KEY_GIORNI,
        name="Giorni da analizzare",
        native_min_value=1,
        native_max_value=7,
        native_step=1,
        native_unit_of_measurement="giorni",
        mode=NumberMode.SLIDER,
        icon="mdi:calendar-range",
        default=DEFAULT_GIORNI,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entities = [IrrigazioneNumber(entry.entry_id, desc) for desc in NUMBERS]
    async_add_entities(entities)

    # Registra le entità nel dizionario condiviso
    store = hass.data[DOMAIN][entry.entry_id].setdefault(ENTITIES, {})
    for entity in entities:
        store[entity.key] = entity


class IrrigazioneNumber(RestoreEntity, NumberEntity):
    """Entità number con persistenza dello stato."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry_id: str, description: IrrigazioneNumberDescription) -> None:
        self._entry_id = entry_id
        self._description = description
        self.key = description.key
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_native_min_value = description.native_min_value
        self._attr_native_max_value = description.native_max_value
        self._attr_native_step = description.native_step
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_mode = description.mode
        self._attr_icon = description.icon
        self._attr_native_value = description.default

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": "Sistema Irrigazione",
            "manufacturer": "ESPHome",
            "model": "Sonoff RM4",
        }

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if last_state := await self.async_get_last_state():
            try:
                self._attr_native_value = float(last_state.state)
            except (ValueError, TypeError):
                pass

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()
