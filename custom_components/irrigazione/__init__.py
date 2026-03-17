"""Sistema Irrigazione - custom integration per Home Assistant."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers.event import async_track_time_change

from .const import (
    DOMAIN,
    PLATFORMS,
    COORDINATOR,
    ENTITIES,
    SCHEDULER,
    CONF_ZONA_1, CONF_ZONA_2, CONF_ZONA_3, CONF_ZONA_4,
    KEY_ABILITATA,
    KEY_SLOT_1_ATTIVO, KEY_SLOT_2_ATTIVO, KEY_SLOT_3_ATTIVO,
    KEY_ORA_SLOT_1, KEY_ORA_SLOT_2, KEY_ORA_SLOT_3,
    KEY_LUN, KEY_MAR, KEY_MER, KEY_GIO, KEY_VEN, KEY_SAB, KEY_DOM,
    KEY_ZONA_1_DURATA, KEY_ZONA_2_DURATA, KEY_ZONA_3_DURATA, KEY_ZONA_4_DURATA,
    KEY_ATTESA,
    DEFAULT_DURATA, DEFAULT_ATTESA,
)
from .coordinator import IrrigazioneCoordinator

_LOGGER = logging.getLogger(__name__)

WEEKDAY_KEYS = [KEY_LUN, KEY_MAR, KEY_MER, KEY_GIO, KEY_VEN, KEY_SAB, KEY_DOM]
DURATION_KEYS = [KEY_ZONA_1_DURATA, KEY_ZONA_2_DURATA, KEY_ZONA_3_DURATA, KEY_ZONA_4_DURATA]
SLOT_ACTIVE_KEYS = [KEY_SLOT_1_ATTIVO, KEY_SLOT_2_ATTIVO, KEY_SLOT_3_ATTIVO]
SLOT_TIME_KEYS = [KEY_ORA_SLOT_1, KEY_ORA_SLOT_2, KEY_ORA_SLOT_3]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Inizializza l'integrazione."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    # Coordinator meteo
    coordinator = IrrigazioneCoordinator(hass)
    hass.data[DOMAIN][entry.entry_id][COORDINATOR] = coordinator
    await coordinator.async_config_entry_first_refresh()

    # Setup piattaforme (crea tutte le entità)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Scheduler (avviato dopo le entità)
    scheduler = IrrigazioneScheduler(hass, entry)
    hass.data[DOMAIN][entry.entry_id][SCHEDULER] = scheduler
    await scheduler.async_setup()

    # Services
    _register_services(hass)

    # Cleanup su HA stop
    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, scheduler.async_shutdown)
    )

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Ricarica l'integrazione quando cambiano le opzioni."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Rimuovi l'integrazione."""
    scheduler = hass.data[DOMAIN][entry.entry_id].get(SCHEDULER)
    if scheduler:
        await scheduler.async_shutdown(None)

    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unloaded


def _register_services(hass: HomeAssistant) -> None:
    """Registra i servizi dell'integrazione (idempotente)."""
    if hass.services.has_service(DOMAIN, "avvia_sequenza"):
        return

    async def _svc_avvia_sequenza(call: ServiceCall) -> None:
        for entry_id, data in hass.data[DOMAIN].items():
            scheduler = data.get(SCHEDULER)
            if scheduler:
                await scheduler.async_start_sequence(manual=True)

    async def _svc_ferma_tutto(call: ServiceCall) -> None:
        for entry_id, data in hass.data[DOMAIN].items():
            scheduler = data.get(SCHEDULER)
            if scheduler:
                await scheduler.async_stop()

    async def _svc_avvia_zona(call: ServiceCall) -> None:
        zona = int(call.data.get("zona", 1))
        durata = int(call.data.get("durata", DEFAULT_DURATA))
        for entry_id, data in hass.data[DOMAIN].items():
            scheduler = data.get(SCHEDULER)
            if scheduler:
                await scheduler.async_start_zone(zona, durata)

    hass.services.async_register(DOMAIN, "avvia_sequenza", _svc_avvia_sequenza)
    hass.services.async_register(DOMAIN, "ferma_tutto", _svc_ferma_tutto)
    hass.services.async_register(DOMAIN, "avvia_zona", _svc_avvia_zona)


# ─────────────────────────────────────────────────────────────────────────────
# Scheduler
# ─────────────────────────────────────────────────────────────────────────────

class IrrigazioneScheduler:
    """Gestisce lo scheduling e la sequenza di irrigazione."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._entry_id = entry.entry_id
        self._task: asyncio.Task | None = None
        self._cancel_ticker: list = []

    async def async_setup(self) -> None:
        """Registra il ticker al secondo 0 di ogni minuto."""
        cancel = async_track_time_change(
            self.hass, self._on_tick, second=0
        )
        self._cancel_ticker.append(cancel)
        _LOGGER.debug("Irrigazione scheduler avviato")

    @callback
    def _on_tick(self, now: datetime) -> None:
        """Chiamato ogni minuto. Controlla se è ora di irrigare."""
        asyncio.ensure_future(self._async_check(now))

    async def _async_check(self, now: datetime) -> None:
        """Controlla condizioni e avvia sequenza se necessario."""
        if self._task and not self._task.done():
            return  # sequenza già in corso

        if not self._is_on(KEY_ABILITATA):
            return

        # Controlla giorno della settimana
        wd = now.weekday()
        if not self._is_on(WEEKDAY_KEYS[wd]):
            return

        # Controlla slot orari
        current_hm = (now.hour, now.minute)
        for slot_idx, (active_key, time_key) in enumerate(
            zip(SLOT_ACTIVE_KEYS, SLOT_TIME_KEYS), start=1
        ):
            if not self._is_on(active_key):
                continue
            slot_time = self._get_slot_time(time_key)
            if slot_time and (slot_time.hour, slot_time.minute) == current_hm:
                _LOGGER.info("Irrigazione: avvio slot %d (%02d:%02d)", slot_idx, *current_hm)
                await self.async_start_sequence(manual=False)
                return

    async def async_start_sequence(self, manual: bool = False) -> None:
        """Avvia la sequenza completa (4 zone)."""
        if self._task and not self._task.done():
            _LOGGER.warning("Irrigazione già in corso, ignoro avvio")
            return

        if not self._is_on(KEY_ABILITATA) and not manual:
            return

        from .sensor import calcola_fattore_riduzione
        coordinator = self.hass.data[DOMAIN][self._entry_id].get(COORDINATOR)
        fattore = 100

        if coordinator:
            # Crea un proxy minimale per calcola_fattore_riduzione
            class _Proxy:
                def __init__(self, hass, entry_id):
                    self.hass = hass
                    self._entry_id = entry_id

                def _number_value(self, key, default=0.0):
                    e = self.hass.data[DOMAIN][self._entry_id].get(ENTITIES, {}).get(key)
                    if e is not None and e.native_value is not None:
                        return float(e.native_value)
                    return default

                def _is_on(self, key):
                    e = self.hass.data[DOMAIN][self._entry_id].get(ENTITIES, {}).get(key)
                    return bool(e and e.is_on)

            fattore = calcola_fattore_riduzione(coordinator, _Proxy(self.hass, self._entry_id))

        if fattore == 0 and not manual:
            _LOGGER.info("Irrigazione: saltata per pioggia (fattore=0)")
            self.hass.components.persistent_notification.async_create(
                "Irrigazione saltata: pioggia prevista o recente troppo elevata.",
                title="Irrigazione sospesa",
                notification_id="irr_skip",
            )
            return

        conf = {**self._entry.data, **self._entry.options}
        zone_entities = [
            conf.get(CONF_ZONA_1, ""),
            conf.get(CONF_ZONA_2, ""),
            conf.get(CONF_ZONA_3, ""),
            conf.get(CONF_ZONA_4, ""),
        ]
        durate_base = [
            self._get_number(KEY_ZONA_1_DURATA, DEFAULT_DURATA),
            self._get_number(KEY_ZONA_2_DURATA, DEFAULT_DURATA),
            self._get_number(KEY_ZONA_3_DURATA, DEFAULT_DURATA),
            self._get_number(KEY_ZONA_4_DURATA, DEFAULT_DURATA),
        ]
        attesa = self._get_number(KEY_ATTESA, DEFAULT_ATTESA)

        if fattore < 100 and not manual:
            msg = f"Irrigazione ridotta al {fattore}%."
            self.hass.components.persistent_notification.async_create(
                msg, title="Irrigazione ridotta", notification_id="irr_ridotta"
            )

        self._task = asyncio.ensure_future(
            self._run_sequence(zone_entities, durate_base, fattore, attesa)
        )

    async def _run_sequence(
        self,
        zone_entities: list[str],
        durate_base: list[float],
        fattore: int,
        attesa_sec: float,
    ) -> None:
        """Esegue la sequenza: accende ogni zona per la durata calcolata."""
        try:
            for i, (entity_id, durata) in enumerate(zip(zone_entities, durate_base), start=1):
                if not entity_id:
                    _LOGGER.debug("Zona %d: entity_id vuoto, salto", i)
                    continue

                durata_effettiva = max(1, round(durata * fattore / 100))
                _LOGGER.info("Zona %d: accensione per %d min (%s)", i, durata_effettiva, entity_id)

                await self.hass.services.async_call(
                    "switch", "turn_on", {"entity_id": entity_id}, blocking=True
                )
                await asyncio.sleep(durata_effettiva * 60)
                await self.hass.services.async_call(
                    "switch", "turn_off", {"entity_id": entity_id}, blocking=True
                )

                if i < len(zone_entities) and attesa_sec > 0:
                    _LOGGER.debug("Attesa tra zone: %d sec", attesa_sec)
                    await asyncio.sleep(attesa_sec)

            _LOGGER.info("Sequenza irrigazione completata")

        except asyncio.CancelledError:
            _LOGGER.info("Sequenza irrigazione annullata")
            # Spegni tutte le zone in sicurezza
            for entity_id in zone_entities:
                if entity_id:
                    try:
                        await self.hass.services.async_call(
                            "switch", "turn_off", {"entity_id": entity_id}, blocking=True
                        )
                    except Exception:
                        pass
            raise

    async def async_start_zone(self, zona: int, durata_min: int) -> None:
        """Avvia una singola zona (per test manuali)."""
        conf = {**self._entry.data, **self._entry.options}
        keys = [CONF_ZONA_1, CONF_ZONA_2, CONF_ZONA_3, CONF_ZONA_4]
        if not 1 <= zona <= 4:
            return
        entity_id = conf.get(keys[zona - 1], "")
        if not entity_id:
            return

        async def _run():
            await self.hass.services.async_call(
                "switch", "turn_on", {"entity_id": entity_id}, blocking=True
            )
            await asyncio.sleep(durata_min * 60)
            await self.hass.services.async_call(
                "switch", "turn_off", {"entity_id": entity_id}, blocking=True
            )

        self._task = asyncio.ensure_future(_run())

    async def async_stop(self) -> None:
        """Ferma la sequenza e spegne tutti i relè."""
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        conf = {**self._entry.data, **self._entry.options}
        for key in [CONF_ZONA_1, CONF_ZONA_2, CONF_ZONA_3, CONF_ZONA_4]:
            entity_id = conf.get(key, "")
            if entity_id:
                try:
                    await self.hass.services.async_call(
                        "switch", "turn_off", {"entity_id": entity_id}, blocking=True
                    )
                except Exception:
                    pass

        _LOGGER.info("Irrigazione fermata")

    async def async_shutdown(self, _event=None) -> None:
        """Cleanup al riavvio di HA."""
        for cancel in self._cancel_ticker:
            cancel()
        self._cancel_ticker.clear()
        await self.async_stop()

    # ── helpers ──────────────────────────────────────────────────────────────

    def _is_on(self, key: str) -> bool:
        e = self.hass.data[DOMAIN][self._entry_id].get(ENTITIES, {}).get(key)
        return bool(e and e.is_on)

    def _get_number(self, key: str, default: float) -> float:
        e = self.hass.data[DOMAIN][self._entry_id].get(ENTITIES, {}).get(key)
        if e is not None and e.native_value is not None:
            return float(e.native_value)
        return default

    def _get_slot_time(self, key: str):
        e = self.hass.data[DOMAIN][self._entry_id].get(ENTITIES, {}).get(key)
        if e is not None:
            return e.native_value  # datetime.time
        return None
