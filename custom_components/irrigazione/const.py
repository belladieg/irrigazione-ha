"""Costanti per il sistema irrigazione."""
from homeassistant.const import Platform

DOMAIN = "irrigazione"

PLATFORMS = [
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.TIME,
    Platform.TEXT,
    Platform.BUTTON,
]

# --- Chiavi config entry ---
CONF_ZONA_1 = "zona_1_switch"
CONF_ZONA_2 = "zona_2_switch"
CONF_ZONA_3 = "zona_3_switch"
CONF_ZONA_4 = "zona_4_switch"

# --- Valori di default ---
DEFAULT_DURATA = 10        # minuti per zona
DEFAULT_ATTESA = 30        # secondi tra zone
DEFAULT_SOGLIA_PREVISTA = 3.0   # mm pioggia prevista per skip
DEFAULT_SOGLIA_STORICA = 15.0   # mm pioggia storica per skip
DEFAULT_GIORNI = 3         # giorni da analizzare
DEFAULT_SLOT_1 = "07:00"
DEFAULT_SLOT_2 = "19:00"
DEFAULT_SLOT_3 = "12:00"

# --- Chiavi entità (usate come unique_id suffix e storage key) ---

# Switch (boolean)
KEY_ABILITATA = "abilitata"
KEY_SLOT_1_ATTIVO = "slot_1_attivo"
KEY_SLOT_2_ATTIVO = "slot_2_attivo"
KEY_SLOT_3_ATTIVO = "slot_3_attivo"
KEY_LUN = "lun"
KEY_MAR = "mar"
KEY_MER = "mer"
KEY_GIO = "gio"
KEY_VEN = "ven"
KEY_SAB = "sab"
KEY_DOM = "dom"
KEY_SKIP_PREVISTA = "skip_pioggia_prevista"
KEY_SKIP_RECENTE = "skip_pioggia_recente"
KEY_RIDUCI = "riduci_se_piovuto"

# Number
KEY_ZONA_1_DURATA = "zona_1_durata"
KEY_ZONA_2_DURATA = "zona_2_durata"
KEY_ZONA_3_DURATA = "zona_3_durata"
KEY_ZONA_4_DURATA = "zona_4_durata"
KEY_ATTESA = "attesa_zone"
KEY_SOGLIA_PREVISTA = "soglia_prevista"
KEY_SOGLIA_STORICA = "soglia_storica"
KEY_GIORNI = "giorni"

# Time
KEY_ORA_SLOT_1 = "ora_slot_1"
KEY_ORA_SLOT_2 = "ora_slot_2"
KEY_ORA_SLOT_3 = "ora_slot_3"

# Text
KEY_NOME_ZONA_1 = "nome_zona_1"
KEY_NOME_ZONA_2 = "nome_zona_2"
KEY_NOME_ZONA_3 = "nome_zona_3"
KEY_NOME_ZONA_4 = "nome_zona_4"

# Coordinator
COORDINATOR = "coordinator"
ENTITIES = "entities"
SCHEDULER = "scheduler"

# Open-Meteo
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_PAST_DAYS = 7
OPEN_METEO_FORECAST_DAYS = 3

# Indici Open-Meteo (con past_days=7, oggi=7, domani=8)
IDX_TODAY = 7
IDX_TOMORROW = 8
