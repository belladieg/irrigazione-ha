# 💧 Sistema Irrigazione per Home Assistant

> Integrazione custom per Home Assistant che gestisce un impianto di irrigazione a 4 zone con adattamento automatico basato sulle previsioni meteo.

[![HA Version](https://img.shields.io/badge/Home%20Assistant-%3E%3D2023.1-blue?logo=homeassistant)](https://www.home-assistant.io/)
[![ESPHome](https://img.shields.io/badge/ESPHome-Sonoff%20RM4-orange?logo=esphome)](https://esphome.io/)
[![Meteo](https://img.shields.io/badge/Meteo-Open--Meteo-green)](https://open-meteo.com/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

---

## ✨ Funzionalità

| Funzione | Descrizione |
|---|---|
| 🌿 **4 zone indipendenti** | Ogni zona ha nome e durata personalizzabili |
| 🕒 **3 fasce orarie al giorno** | Puoi avviare l'irrigazione fino a 3 volte al giorno |
| 📅 **Giorni della settimana** | Scegli esattamente quali giorni irrigare |
| 🌧️ **Meteo automatico** | Usa Open-Meteo (gratuito, no API key) |
| ⏸️ **Skip per pioggia** | Salta l'irrigazione se ha piovuto o se è prevista pioggia |
| 📉 **Riduzione proporzionale** | Riduce la durata in base alla pioggia recente |
| 🔒 **Sicurezza integrata** | La sequenza può essere interrotta in qualsiasi momento |
| 📊 **Dashboard inclusa** | Pannello Lovelace organizzato con 3 viste |

---

## 🔧 Hardware richiesto

- **Sonoff RM4** (o qualsiasi ESP32/ESP8266 con 4 relè) flashato con **ESPHome**
- **Home Assistant** versione ≥ 2023.1
- Connessione internet (per i dati meteo Open-Meteo)

---

## 📦 Installazione

### Metodo 1 — Manuale (consigliato)

1. Scarica o clona questa repository
2. Copia la cartella `custom_components/irrigazione/` nella cartella `config/custom_components/` del tuo Home Assistant
3. Riavvia Home Assistant
4. Vai in **Impostazioni → Dispositivi e servizi → Aggiungi integrazione**
5. Cerca **"Sistema Irrigazione"** e segui il wizard

### Metodo 2 — Tramite HACS

1. In HACS → Integrations → `⋮` → **Custom repositories**
2. Incolla: `https://github.com/belladieg/irrigazione-ha`
3. Categoria: **Integration** → **Add**
4. Cerca "Sistema Irrigazione" → **Installa** → **Riavvia HA**

---

## ⚙️ Configurazione iniziale

Al primo avvio il wizard ti chiede due cose:

### Step 1 — Nome del sistema
Dai un nome al sistema (es. "Irrigazione Giardino").

### Step 2 — Associazione zone
Seleziona i 4 switch ESPHome che corrispondono ai relè del Sonoff RM4.

> 💡 Se il tuo ESPHome è già integrato in HA, trovi gli switch in
> **Impostazioni → Dispositivi → [nome del tuo ESPHome]**

Esempio di nomi switch ESPHome:
```
switch.sonoff_rm4_zona_1
switch.sonoff_rm4_zona_2
switch.sonoff_rm4_zona_3
switch.sonoff_rm4_zona_4
```

---

## 🌦️ Come funziona il meteo

L'integrazione usa **[Open-Meteo](https://open-meteo.com/)**, un servizio meteorologico gratuito e open source.

**Non serve nessuna API key.** Usa automaticamente le coordinate di casa impostate in HA:
> Impostazioni → Sistema → Posizione → verifica latitudine e longitudine

Ogni ora vengono scaricati:
- Precipitazioni degli **ultimi 7 giorni** nella tua posizione
- **Previsione pioggia** per il giorno successivo

### Logica di adattamento

```
Pioggia storica (ultimi N giorni) ──► confronta con soglia storica
                                           │
                        ┌──────────────────┼──────────────────┐
                        ▼                  ▼                  ▼
                   < soglia          = soglia           > soglia
               Irrigazione al     Riduzione          Skip totale
               100% (normale)    proporzionale       (se abilitato)

Pioggia prevista domani ──► confronta con soglia previsione
                                   │
                     ┌─────────────┴─────────────┐
                     ▼                           ▼
               < soglia                    ≥ soglia
             Irrigazione normale         Skip totale
                                         (se abilitato)
```

**Esempio pratico:**
- Soglia storica = 15 mm
- Pioggia ultimi 3 giorni = 9 mm
- Fattore riduzione = `1 - (9/15)` = **40% di riduzione**
- Zona con durata base 10 min → irrigherà per **6 minuti**

---

## 📋 Riferimento entità

Dopo l'installazione trovi queste entità nel dispositivo "Sistema Irrigazione":

### 🔀 Switch (interruttori)
| Entità | Descrizione |
|---|---|
| `switch.sistema_attivo` | Master switch — se OFF nulla parte |
| `switch.fascia_1_attiva` / `_2` / `_3` | Abilita/disabilita ogni fascia oraria |
| `switch.lunedi` … `switch.domenica` | Giorni in cui irrigare |
| `switch.salta_se_prevista_pioggia` | Skip se domani è prevista pioggia |
| `switch.salta_se_ha_piovuto_di_recente` | Skip se pioggia storica supera soglia |
| `switch.riduci_durata_se_ha_piovuto` | Riduzione proporzionale invece di skip |

### 🔢 Number (valori numerici)
| Entità | Default | Descrizione |
|---|---|---|
| `number.zona_1_durata_base` … `_4` | 10 min | Durata base per zona |
| `number.attesa_tra_zone` | 30 sec | Pausa tra una zona e la successiva |
| `number.soglia_pioggia_prevista` | 3 mm | Soglia per skip previsione |
| `number.soglia_pioggia_storica` | 15 mm | Soglia per skip/riduzione storica |
| `number.giorni_da_analizzare` | 3 giorni | Finestra temporale analisi pioggia |

### 🕐 Time (orari)
| Entità | Default | Descrizione |
|---|---|---|
| `time.orario_fascia_1` | 07:00 | Ora avvio fascia 1 |
| `time.orario_fascia_2` | 19:00 | Ora avvio fascia 2 |
| `time.orario_fascia_3` | 12:00 | Ora avvio fascia 3 |

### 📊 Sensor (sola lettura)
| Entità | Descrizione |
|---|---|
| `sensor.stato_irrigazione` | Stato testuale: Standby / Zona X in corso / Sospesa |
| `sensor.fattore_riduzione_irrigazione` | Percentuale irrigazione (0–100%) |
| `sensor.durata_effettiva_zona_1` … `_4` | Durata reale dopo adattamento meteo |
| `sensor.pioggia_storica_totale` | Pioggia cumulata nel periodo analizzato |
| `sensor.pioggia_prevista_domani` | mm previsti per domani |
| `sensor.probabilita_pioggia_domani` | Probabilità pioggia domani (%) |
| `sensor.pioggia_oggi` / `_ieri` / `_2gg_fa` … | Dati storici giorno per giorno |

### ✏️ Text (testi)
| Entità | Default | Descrizione |
|---|---|---|
| `text.nome_zona_1` … `_4` | "Zona 1" … "Zona 4" | Nome personalizzato per ogni zona |

### 🔘 Button (pulsanti)
| Entità | Descrizione |
|---|---|
| `button.avvia_irrigazione` | Avvia la sequenza completa immediatamente |
| `button.ferma_irrigazione` | Ferma tutto e spegne tutti i relè |

---

## 🛠️ Servizi disponibili

Puoi chiamare questi servizi da automazioni HA o da script:

```yaml
# Avvia la sequenza completa
service: irrigazione.avvia_sequenza

# Ferma tutto
service: irrigazione.ferma_tutto

# Avvia una singola zona (utile per test)
service: irrigazione.avvia_zona
data:
  zona: 2          # numero zona (1-4)
  durata: 5        # minuti (opzionale, default 10)
```

---

## 📱 Dashboard

Nella cartella `dashboard/` trovi il file `irrigazione_dashboard.yaml` con una dashboard Lovelace pronta all'uso, organizzata in 3 viste:

1. **Controllo** — stato, pulsanti avvio/stop, zone con durate
2. **Programma** — giorni attivi e fasce orarie
3. **Meteo** — dati pioggia, gauge fattore riduzione, soglie

### Come importarla
1. Apri `dashboard/irrigazione_dashboard.yaml` su GitHub
2. Copia tutto il contenuto
3. In HA: **Impostazioni → Dashboard → + → Vuota**
4. Apri la dashboard → **matita** → **Editor RAW** → incolla il YAML

---

## 🔌 ESPHome — Config di riferimento

Nella cartella `esphome/` trovi `sonoff_rm4_irrigazione.yaml`, una configurazione di partenza per il Sonoff RM4.

> ⚠️ I pin GPIO variano a seconda della versione del dispositivo.
> Verifica la pinout sul sito [devices.esphome.io](https://devices.esphome.io) cercando il tuo modello esatto.

---

## 📄 Licenza

Distribuito sotto licenza MIT. Vedi `LICENSE` per i dettagli.
