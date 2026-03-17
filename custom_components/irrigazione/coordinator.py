"""DataUpdateCoordinator per i dati meteo Open-Meteo."""
from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    OPEN_METEO_URL,
    OPEN_METEO_PAST_DAYS,
    OPEN_METEO_FORECAST_DAYS,
)

_LOGGER = logging.getLogger(__name__)


class IrrigazioneCoordinator(DataUpdateCoordinator[dict]):
    """Scarica i dati meteo da Open-Meteo ogni ora."""

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_meteo",
            update_interval=timedelta(hours=1),
        )

    async def _async_update_data(self) -> dict:
        """Fetch dati da Open-Meteo usando le coordinate di zone.home."""
        lat = self.hass.config.latitude
        lon = self.hass.config.longitude

        if not lat or not lon:
            raise UpdateFailed("Coordinate home non configurate in HA")

        url = (
            f"{OPEN_METEO_URL}"
            f"?latitude={lat:.4f}"
            f"&longitude={lon:.4f}"
            f"&daily=precipitation_sum,precipitation_probability_max"
            f"&timezone=auto"
            f"&forecast_days={OPEN_METEO_FORECAST_DAYS}"
            f"&past_days={OPEN_METEO_PAST_DAYS}"
        )

        session = async_get_clientsession(self.hass)
        try:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Errore fetch Open-Meteo: {err}") from err

        daily = data.get("daily", {})
        _LOGGER.debug(
            "Open-Meteo: %d giorni di dati ricevuti",
            len(daily.get("time", [])),
        )
        return daily

    def get_precip(self, index: int) -> float:
        """Precipitazione per un indice specifico (mm). Ritorna 0 se non disponibile."""
        if not self.data:
            return 0.0
        precip = self.data.get("precipitation_sum", [])
        if index < len(precip) and precip[index] is not None:
            return float(precip[index])
        return 0.0

    def get_precip_probability(self, index: int) -> int:
        """Probabilità pioggia (%) per un indice specifico."""
        if not self.data:
            return 0
        prob = self.data.get("precipitation_probability_max", [])
        if index < len(prob) and prob[index] is not None:
            return int(prob[index])
        return 0

    def get_historical_total(self, days: int) -> float:
        """Somma precipitazioni degli ultimi N giorni (incluso oggi)."""
        # Con past_days=7: indice 7=oggi, 6=ieri, 5=2gg fa, ...
        # Per N giorni: somma da (7-N+1) a 7 inclusi, con minimo indice 0
        start = max(0, 8 - days)
        return sum(self.get_precip(i) for i in range(start, 8))
