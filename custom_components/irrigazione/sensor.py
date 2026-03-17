"""Sensori meteo e calcolati per il sistema irrigazione."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    COORDINATOR,
    ENTITIES,
    IDX_TODAY,
    IDX_TOMORROW,
    KEY_ZONA_1_DURATA, KEY_ZONA_2_DURATA, KEY_ZONA_3_DURATA, KEY_ZONA_4_DURATA,
    KEY_GIORNI,
    KEY_SOGLIA_PREVISTA,
    KEY_SOGLIA_STORICA,
    KEY_SKIP_PREVISTA,
    KEY_SKIP_RECENTE,
    KEY_RIDUCI,
    KEY_NOME_ZONA_1, KEY_NOME_ZONA_2, KEY_NOME_ZONA_3, KEY_NOME_ZONA_4,
    CONF_ZONA_1, CONF_ZONA_2, CONF_ZONA_3, CONF_ZONA_4,
    DEFAULT_DURATA,
    DEFAULT_GIORNI,
    DEFAULT_SOGLIA_PREVISTA,
    DEFAULT_SOGLIA_STORICA,
)
from .coordinator import IrrigazioneCoordinator

_LOGGER = logging.getLogger(__name__)

# Giorni da mostrare nel pannello storico (label, offset da oggi)
GIORNI_STORICI = [
    ("Pioggia oggi",     0),
    ("Pioggia ieri",     1),
    ("2 giorni fa",      2),
    ("3 giorni fa",      3),
    ("4 giorni fa",      4),
    ("5 giorni fa",      5),
    ("6 giorni fa",      6),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: IrrigazioneCoordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]

    entities: list[SensorEntity] = []

    # Sensori dati grezzi Open-Meteo
    for label, offset in GIORNI_STORICI:
        entities.append(PioggiaStoricaSensor(coordinator, entry, label, offset))

    entities.append(PioggiaPrevistoSensor(coordinator, entry))
    entities.append(ProbabilitaPioggiaSensor(coordinator, entry))

    # Sensori calcolati (dipendono da coordinator + entità number/switch)
    entities.append(PioggiaStoricaTotaleSensor(coordinator, entry))
    entities.append(FattoreRiduzioneSensor(coordinator, entry))
    entities.append(StatoSensor(coordinator, entry))

    # Durate effettive per zona
    for zona in range(1, 5):
        entities.append(DurataEffettivaSensor(coordinator, entry, zona))

    async_add_entities(entities)


# ─────────────────────────────────────────────────────────────────────────────
# Base class per sensori coordinator
# ─────────────────────────────────────────────────────────────────────────────

class _CoordSensor(CoordinatorEntity[IrrigazioneCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator: IrrigazioneCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._entry_id = entry.entry_id

    @property
    def device_info(self) -> dict[str, Any]:
        return {"identifiers": {(DOMAIN, self._entry_id)}}

    def _get_entity(self, key: str):
        return self.hass.data[DOMAIN][self._entry_id].get(ENTITIES, {}).get(key)

    def _number_value(self, key: str, default: float = 0.0) -> float:
        e = self._get_entity(key)
        if e is not None and e.native_value is not None:
            return float(e.native_value)
        return default

    def _is_on(self, key: str) -> bool:
        e = self._get_entity(key)
        return bool(e and e.is_on)

    def _text_value(self, key: str, default: str = "") -> str:
        e = self._get_entity(key)
        if e is not None and e.native_value:
            return str(e.native_value)
        return default


# ─────────────────────────────────────────────────────────────────────────────
# Sensori dati meteo
# ─────────────────────────────────────────────────────────────────────────────

class PioggiaStoricaSensor(_CoordSensor):
    _attr_native_unit_of_measurement = "mm"
    _attr_device_class = SensorDeviceClass.PRECIPITATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:weather-rainy"

    def __init__(self, coordinator, entry, label: str, offset: int) -> None:
        super().__init__(coordinator, entry)
        self._offset = offset
        self._attr_name = label
        self._attr_unique_id = f"{entry.entry_id}_pioggia_{offset}gg"

    @property
    def native_value(self) -> float:
        return self.coordinator.get_precip(IDX_TODAY - self._offset)


class PioggiaPrevistoSensor(_CoordSensor):
    _attr_name = "Pioggia prevista domani"
    _attr_native_unit_of_measurement = "mm"
    _attr_device_class = SensorDeviceClass.PRECIPITATION
    _attr_icon = "mdi:weather-partly-rainy"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_pioggia_domani"

    @property
    def native_value(self) -> float:
        return self.coordinator.get_precip(IDX_TOMORROW)


class ProbabilitaPioggiaSensor(_CoordSensor):
    _attr_name = "Probabilità pioggia domani"
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:water-percent"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_prob_pioggia"

    @property
    def native_value(self) -> int:
        return self.coordinator.get_precip_probability(IDX_TOMORROW)


# ─────────────────────────────────────────────────────────────────────────────
# Sensori calcolati
# ─────────────────────────────────────────────────────────────────────────────

class _CalcolataSensor(_CoordSensor):
    """Sensore che si aggiorna anche quando cambiano le entità dipendenti."""

    _DIPENDENZE: list[str] = []  # chiavi entità da monitorare

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # Aggiorna anche quando cambiano number/switch/text correlati
        @callback
        def _on_entity_change(event):
            self.async_write_ha_state()

        # Ascolta cambiamenti di state su tutte le piattaforme dell'integrazione
        # (modo semplice: track_state_change per il dominio intero)
        self.async_on_remove(
            self.hass.bus.async_listen(
                "state_changed",
                _on_entity_change,
            )
        )


class PioggiaStoricaTotaleSensor(_CalcolataSensor):
    _attr_name = "Pioggia storica totale"
    _attr_native_unit_of_measurement = "mm"
    _attr_device_class = SensorDeviceClass.PRECIPITATION
    _attr_icon = "mdi:weather-pouring"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_pioggia_storica_totale"

    @property
    def native_value(self) -> float:
        giorni = int(self._number_value(KEY_GIORNI, DEFAULT_GIORNI))
        return round(self.coordinator.get_historical_total(giorni), 1)


class FattoreRiduzioneSensor(_CalcolataSensor):
    _attr_name = "Fattore riduzione irrigazione"
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:percent"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_fattore_riduzione"

    @property
    def native_value(self) -> int:
        return calcola_fattore_riduzione(self.coordinator, self)


class StatoSensor(_CalcolataSensor):
    _attr_name = "Stato irrigazione"
    _attr_icon = "mdi:sprinkler-variant"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_stato"

    @property
    def native_value(self) -> str:
        entities_map = self.hass.data[DOMAIN][self._entry_id].get(ENTITIES, {})
        abilitata = entities_map.get("abilitata")
        if abilitata and not abilitata.is_on:
            return "Disabilitata"

        fattore = calcola_fattore_riduzione(self.coordinator, self)
        if fattore == 0:
            return "Sospesa (pioggia)"

        # Controlla zone hardware
        zone_keys = [CONF_ZONA_1, CONF_ZONA_2, CONF_ZONA_3, CONF_ZONA_4]
        nome_keys = [KEY_NOME_ZONA_1, KEY_NOME_ZONA_2, KEY_NOME_ZONA_3, KEY_NOME_ZONA_4]
        conf = {**self._entry.data, **self._entry.options}

        for i, (ck, nk) in enumerate(zip(zone_keys, nome_keys), start=1):
            entity_id = conf.get(ck, "")
            if entity_id:
                state = self.hass.states.get(entity_id)
                if state and state.state == "on":
                    nome = self._text_value(nk, f"Zona {i}")
                    return f"{nome} in corso"

        if fattore < 100:
            return f"Standby (ridotta al {fattore}%)"
        return "Standby"


class DurataEffettivaSensor(_CalcolataSensor):
    _attr_native_unit_of_measurement = "min"
    _attr_icon = "mdi:timer"
    _attr_state_class = SensorStateClass.MEASUREMENT

    _DURATA_KEYS = [
        KEY_ZONA_1_DURATA, KEY_ZONA_2_DURATA,
        KEY_ZONA_3_DURATA, KEY_ZONA_4_DURATA,
    ]

    def __init__(self, coordinator, entry, zona: int) -> None:
        super().__init__(coordinator, entry)
        self._zona = zona
        self._attr_name = f"Durata effettiva Zona {zona}"
        self._attr_unique_id = f"{entry.entry_id}_durata_effettiva_zona_{zona}"

    @property
    def native_value(self) -> int:
        key = self._DURATA_KEYS[self._zona - 1]
        base = self._number_value(key, DEFAULT_DURATA)
        fattore = calcola_fattore_riduzione(self.coordinator, self) / 100
        if fattore <= 0:
            return 0
        return max(1, round(base * fattore))


# ─────────────────────────────────────────────────────────────────────────────
# Funzione condivisa: calcolo fattore riduzione
# ─────────────────────────────────────────────────────────────────────────────

def calcola_fattore_riduzione(coordinator: IrrigazioneCoordinator, entity: _CoordSensor) -> int:
    """Ritorna 0-100: percentuale di irrigazione da applicare."""
    giorni = int(entity._number_value(KEY_GIORNI, DEFAULT_GIORNI))
    soglia_prevista = entity._number_value(KEY_SOGLIA_PREVISTA, DEFAULT_SOGLIA_PREVISTA)
    soglia_storica = entity._number_value(KEY_SOGLIA_STORICA, DEFAULT_SOGLIA_STORICA)

    pioggia_storica = coordinator.get_historical_total(giorni)
    pioggia_domani = coordinator.get_precip(IDX_TOMORROW)

    # Skip totale per pioggia prevista
    if entity._is_on(KEY_SKIP_PREVISTA) and pioggia_domani >= soglia_prevista:
        return 0

    # Skip totale per pioggia storica
    if entity._is_on(KEY_SKIP_RECENTE) and pioggia_storica >= soglia_storica:
        return 0

    # Riduzione proporzionale
    if entity._is_on(KEY_RIDUCI) and pioggia_storica > 0 and soglia_storica > 0:
        fattore = max(0.0, 1.0 - (pioggia_storica / soglia_storica))
        return int(fattore * 100)

    return 100
