# 💧 Sistema Irrigazione per Home Assistant

> Integrazione custom per Home Assistant che gestisce un impianto di irrigazione a 4 zone con adattamento automatico basato sulle previsioni meteo.

[![HA Version](https://img.shields.io/badge/Home%20Assistant-%3E%3D2023.1-blue?logo=homeassistant)](https://www.home-assistant.io/)
[![Meteo](https://img.shields.io/badge/Meteo-Open--Meteo-green)](https://open-meteo.com/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

---

## ✨ Funzionalità

| Funzione | Descrizione |
|---|---|
| 🌿 **4 zone indipendenti** | Ogni zona ha nome e durata personalizzabili |
| 🕒 **3 fasce orarie al giorno** | Avvia l'irrigazione fino a 3 volte al giorno |
| 📅 **Giorni della settimana** | Scegli esattamente quali giorni irrigare |
| 🌧️ **Meteo automatico** | Usa Open-Meteo (gratuito, nessuna API key richiesta) |
| ⏸️ **Skip per pioggia** | Salta l'irrigazione se ha piovuto o se è prevista pioggia |
| 📉 **Riduzione proporzionale** | Riduce la durata in proporzione alla pioggia recente |
| 🔌 **Hardware universale** | Funziona con qualsiasi relè integrato in HA |
| 🔒 **Sicurezza integrata** | Sequenza annullabile in qualsiasi momento |
| 📊 **Dashboard inclusa** | Pannello Lovelace organizzato con 3 viste |

---

## 🔌 Compatibilità hardware

Questa integrazione funziona con **qualsiasi modulo a 4 relè** già integrato in Home Assistant come entità `switch`:

- **ESPHome** (es. Sonoff 4CH, Shelly 4PM, custom ESP32/ESP8266)
- **Tasmota**
- **Zigbee / Z-Wave** (moduli relè compatibili)
- **Qualsiasi switch HA** (anche virtuale, per test)

> Non è richiesta nessuna configurazione firmware specifica. L'unico requisito è che i 4 relè siano visibili come entità `switch` in Home Assistant.

---

## 📦 Installazione

### Metodo 1 — Manuale

1. Scarica o clona questa repository
2. Copia la cartella `custom_components/irrigazione/` dentro `config/custom_components/` del tuo Home Assistant
3. Riavvia Home Assistant
4. Vai in **Impostazioni → Dispositivi e servizi → Aggiungi integrazione**
5. Cerca **"Sistema Irrigazione"** e segui il wizard

### Metodo 2 — Tramite HACS (Custom repository)

1. In HACS → Integrations → `⋮` → **Custom repositories**
2. Incolla: `https://github.com/belladieg/irrigazione-ha`
3. Categoria: **Integration** → **Add**
4. Cerca "Sistema Irrigazione" → **Installa** → **Riavvia HA**

---

## ⚙️ Configurazione iniziale

Il wizard richiede solo due informazioni:

### Step 1 — Nome del sistema
Dai un nome al sistema (es. "Irrigazione Giardino").

### Step 2 — Associazione zone
Seleziona i 4 switch che corrispondono ai relè del tuo dispositivo.

> 💡 Trovi gli switch disponibili in
> **Impostazioni → Dispositivi → [nome del tuo dispositivo]**

---

## 📋 Entità create automaticamente

Dopo l'installazione, il sistema crea **48 entità** organizzate con prefissi logici.
In Home Assistant le trovi ordinate alfabeticamente in questo modo:

```
Controllo - Avvia sequenza       ← pulsante avvio manuale
Controllo - Ferma tutto          ← pulsante stop immediato
Controllo - Sistema attivo       ← master switch on/off
Controllo - Stato                ← stato testuale del sistema

Fascia 1 - Attiva                ← abilita/disabilita fascia 1
Fascia 1 - Orario                ← orario di avvio fascia 1
Fascia 2 - Attiva
Fascia 2 - Orario
Fascia 3 - Attiva
Fascia 3 - Orario

Giorni - Domenica                ← giorni in cui irrigare
Giorni - Giovedì
Giorni - Lunedì
Giorni - Martedì
Giorni - Mercoledì
Giorni - Sabato
Giorni - Venerdì

Meteo - Fattore riduzione        ← % irrigazione attiva (0=skip, 100=normale)
Meteo - Giorni da analizzare     ← quanti giorni passati controllare
Meteo - Pioggia 2 giorni fa      ← dati storici Open-Meteo
Meteo - Pioggia 3 giorni fa
  ... (fino a 6 giorni fa)
Meteo - Pioggia ieri
Meteo - Pioggia oggi
Meteo - Pioggia prevista domani
Meteo - Pioggia storica totale   ← somma del periodo analizzato
Meteo - Probabilità pioggia domani
Meteo - Riduci se ha piovuto     ← riduzione proporzionale (invece di skip)
Meteo - Salta se pioggia prevista
Meteo - Salta se pioggia recente
Meteo - Soglia pioggia prevista  ← mm oltre i quali scatta lo skip
Meteo - Soglia pioggia storica

Zona 1 - Durata base             ← minuti impostati manualmente
Zona 1 - Durata effettiva        ← minuti reali dopo adattamento meteo
Zona 1 - Nome                    ← nome personalizzato (es. "Prato")
Zona 2 - Durata base
Zona 2 - Durata effettiva
Zona 2 - Nome
Zona 3 - Durata base
Zona 3 - Durata effettiva
Zona 3 - Nome
Zona 4 - Durata base
Zona 4 - Durata effettiva
Zona 4 - Nome

Zone - Attesa tra zone           ← secondi di pausa tra una zona e l'altra
```

---

## 🌦️ Come funziona il meteo

Usa **[Open-Meteo](https://open-meteo.com/)**: gratuito, open source, nessuna registrazione.

**Non occorre configurare nulla.** Usa automaticamente le coordinate di casa impostate in HA:
> Impostazioni → Sistema → Posizione → verifica latitudine e longitudine

Ogni ora vengono scaricati automaticamente:
- Precipitazioni degli **ultimi 7 giorni** nella tua posizione
- **Previsione pioggia** per il giorno successivo

### Logica di adattamento

```
Pioggia storica (ultimi N giorni) ──► confronta con soglia storica
                                              │
                         ┌────────────────────┼────────────────────┐
                         ▼                    ▼                    ▼
                    < soglia           soglia parziale         ≥ soglia
                Irrigazione al       Riduzione                Skip totale
                100% (normale)      proporzionale             (se abilitato)

Pioggia prevista domani ──► confronta con soglia previsione
                                     │
                      ┌──────────────┴──────────────┐
                      ▼                             ▼
                < soglia                       ≥ soglia
            Irrigazione normale             Skip totale
                                            (se abilitato)
```

**Esempio pratico:**
> Soglia storica = 15 mm · Pioggia ultimi 3 giorni = 9 mm
> Fattore = `1 − (9/15)` = **40% di riduzione**
> Zona con durata base 10 min → irrigherà per **6 minuti**

---

## 🛠️ Servizi disponibili

Utilizzabili da automazioni HA, script o dashboard:

```yaml
# Avvia la sequenza completa
service: irrigazione.avvia_sequenza

# Ferma tutto immediatamente
service: irrigazione.ferma_tutto

# Avvia una singola zona (utile per test o manutenzione)
service: irrigazione.avvia_zona
data:
  zona: 2       # numero zona 1-4
  durata: 5     # minuti (opzionale, default 10)
```

---

## 📱 Dashboard

Nella cartella `dashboard/` trovi `irrigazione_dashboard.yaml`: una dashboard Lovelace
pronta all'uso, organizzata in 3 viste:

| Vista | Contenuto |
|---|---|
| **Controllo** | Stato sistema, pulsanti avvio/stop, durate per zona |
| **Programma** | Giorni attivi, fasce orarie |
| **Meteo** | Dati pioggia, gauge fattore riduzione, soglie |

### Come importarla
1. Apri `dashboard/irrigazione_dashboard.yaml` su GitHub e copia il contenuto
2. In HA: **Impostazioni → Dashboard → +** → scegli "Vuota"
3. Apri la nuova dashboard → **matita** → **Editor RAW** → incolla il YAML

---

## 📄 Licenza

Distribuito sotto licenza MIT.
