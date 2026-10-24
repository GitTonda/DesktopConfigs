# ⌨️ Scorciatoie da Tastiera (Keybindings Cheat-Sheet)

Guida completa a tutte le combinazioni di tasti configurate nell'ambiente desktop Catppuccin Mocha (**i3wm** + **Polybar** + **Rofi**).

Il tasto modificatore principale è **`Super`** (noto anche come tasto **Windows** o **`Mod`**).

---

## 🚀 1. Applicazioni Principali & Applet di Sistema

| Scorciatoia | Azione | Note / Finestra |
|---|---|---|
| **`Super + Return`** | **Terminale** | Apre Alacritty (stile terminale trasparente Mocha) |
| **`Super + Shift + Return`** | **File Manager** | Apre Ranger (gestore file a 3 colonne) |
| **`Super + D`** | **Launcher Applicazioni** | Menu di avvio Rofi (`rofi -show drun`) |
| **`Super + Shift + M`** | **Monitor di Sistema** | Apre `btop` in finestra flottante centrata |
| **`Super + Shift + G`** | **Dashboard GPU** | Apre la dashboard prestazionale Rofi (telemetria, VRAM, app attive e power mode) |
| **`Super + Shift + W`** | **Gestore Wi-Fi** | Applet Rofi per scansionare reti e connettersi |
| **`Super + Shift + T`** | **Gestore Bluetooth** | Menu Rofi per accendere, scansionare e accoppiare dispositivi |
| **`Super + Shift + A`** | **Mixer Audio** | Apre `alsamixer` modale in finestra flottante |
| **`Super + Shift + B`** | **Selettore Sfondi** | Galleria visiva + lista Rofi con sincronizzazione accenti tema |
| **`Super + F1`** o **`Super + /`** | **Gestore Scorciatoie** | **Programma interattivo per vedere, creare e modificare le scorciatoie** |
| **`Super + Escape`** o **`Super + Shift + E`** | **Menu Spegnimento** | Schermata Rofi: Sospensione, Riavvio, Spegnimento, Logout |

---

## 🖼️ 2. Gestione Finestre & Tiling

| Scorciatoia | Azione |
|---|---|
| **`Super + Q`** | **Chiude la finestra attiva** in modo pulito |
| **`Super + Shift + Q`** | Forza la chiusura immediata della finestra |
| **`Super + F`** | Attiva / Disattiva la modalità a **schermo intero** |
| **`Super + Shift + Spazio`** | Alterna modalità **Tiling / Flottante** per la finestra attiva |
| **`Super + Spazio`** | Sposta il focus tra finestre flottanti e finestre a griglia |
| **`Super + B`** | Imposta la divisione del prossimo contenitore in **orizzontale** (Split H) |
| **`Super + V`** | Imposta la divisione del prossimo contenitore in **verticale** (Split V) |
| **`Super + S`** | Layout a **Pila** (Stacking - finestre sovrapposte con titolo) |
| **`Super + W`** | Layout a **Schede** (Tabbed - schede stile browser in alto) |
| **`Super + E`** | Alterna layout diviso orizzontale / verticale |
| **`Super + A`** | Seleziona il contenitore genitore (Focus parent) |
| **`Super + R`** | Entra nella **modalità ridimensionamento** (`Frecce` per ridimensionare, `Esc` per uscire) |
| **`Super + Shift + C`** | Ricarica la configurazione di i3 in memoria |
| **`Super + Shift + R`** | Riavvia i3 sul posto (mantiene aperte tutte le applicazioni) |

---

## 🎯 3. Navigazione & Spostamento (Frecce o Tasti Vim)

### Spostare il Focus:
* **`Super + H / J / K / L`** oppure **`Super + Frecce`**: Sinistra / Giù / Su / Destra.

### Spostare la Finestra nella Griglia:
* **`Super + Shift + H / J / K / L`** oppure **`Super + Shift + Frecce`**: Sposta la finestra a Sinistra / Giù / Su / Destra.

---

## 🗂️ 4. Gestione Desktop Virtuali (Workspace 1 - 10)

| Scorciatoia | Azione |
|---|---|
| **`Super + 1`** ... **`Super + 0`** | Passa istantaneamente al Desktop **1** fino a **10** |
| **`Super + Shift + 1`** ... **`Super + Shift + 0`** | Sposta la finestra attiva nel Desktop selezionato |

---

## 🔊 5. Tasti Multimediali, Audio, Schermo & Screenshot

| Tasto Hardware / Scorciatoia | Azione |
|---|---|
| **`XF86AudioRaiseVolume`** | Alza il volume del 5% (**con blocco hardware di sicurezza a max 100%**) |
| **`XF86AudioLowerVolume`** | Abbassa il volume del 5% |
| **`XF86AudioMute`** | Attiva / Disattiva il muto per gli altoparlanti |
| **`XF86AudioMicMute`** | Attiva / Disattiva il muto per il microfono |
| **`XF86AudioPlay`** | Riproduci / Pausa (Spotify, browser, playerctl, mpv) |
| **`XF86AudioNext`** | Traccia successiva |
| **`XF86AudioPrev`** | Traccia precedente |
| **`XF86MonBrightnessUp`** | Aumenta luminosità display del 10% (supporta laptop e monitor esterni) |
| **`XF86MonBrightnessDown`** | Diminuisce luminosità display del 10% |
| **`Print`** o **`F13`** o **`Super + Shift + S`** | **Screenshot ad area ritagliata** (copia diretta negli appunti PNG con notifica) |
| **`Shift + Print`** | **Screenshot a schermo intero** (copia diretta negli appunti) |

---

## 🖱️ 6. Interazioni con il Mouse sulla Barra Superiore (Polybar)

| Modulo Barra | Click Sinistro | Click Destro | Click Centrale / Scroll |
|---|---|---|---|
| **Data / Orologio (`󰃭`)** | Calendario del Mese | Calendario del Mese | - |
| **Volume Audio (`󰕾` / `󰝟`)** | Muto On/Off | Mixer Audio Modale (`alsamixer`) | Scroll: Volume +5% / -5% |
| **GPU (`󰢮`)** | Apre dashboard **Rofi** | **Cicla modalità di vista** (`%` / `Temp` / `VRAM`) | Notifica OSD dettagliata specifiche GPU |
| **CPU (`󰍛`) & RAM (`󰘚`)** | Apre monitor `btop` | Apre monitor `btop` | - |
| **Bluetooth (`󰂯`)** | Menu Rofi Bluetooth | Accendi / Spegni Bluetooth | Click Centrale: Personalizza Widget |
| **Wi-Fi (`󰤨`)** | Menu Rofi Wi-Fi | Impostazioni di Rete (`nmtui`) | - |
| **Ethernet (`󰈀`)** | Connessioni di Rete (`nmtui`) | Connessioni di Rete (`nmtui`) | - |
| **Pulsante Spegnimento (`󰐥`)** | Menu Spegnimento | Menu Spegnimento | - |

---

## 🛠️ 7. Come Creare e Modificare le Proprie Scorciatoie

Il sistema include uno strumento dedicato (**Shortcuts Manager**) integrato sia in interfaccia grafica Rofi che tramite riga di comando.

### Metodo A: Interfaccia Grafica Rapida (Consigliato)
1. Premi **`Super + F1`** (oppure **`Super + /`**).
2. Seleziona **`󰐕  Aggiungi nuova scorciatoia`**.
3. Inserisci la combinazione di tasti (es. `Mod+t` oppure `Mod+Shift+o`).
4. Inserisci il comando da lanciare (es. `firefox`, `telegram-desktop`, `alacritty -e htop`).
5. Assegna un nome (es. `Browser Web`).
6. Lo strumento convalida automaticamente la sintassi con `i3 -C` e ricarica i3 in tempo reale!

Puoi anche selezionare **`󰏫  Modifica scorciatoia`** o **`󰅖  Elimina scorciatoia`** per modificare o rimuovere quelle esistenti.

### Metodo B: Da Riga di Comando (Terminale)
Puoi gestire le scorciatoie direttamente dal terminale con il comando `shortcuts-manager`:

```bash
# Mostra la lista di tutte le scorciatoie
shortcuts-manager list

# Aggiunge una scorciatoia (Tasti, Comando, Descrizione)
shortcuts-manager add "Mod+t" "telegram-desktop" "Telegram"

# Rimuove una scorciatoia personalizzata
shortcuts-manager delete "Mod+t"

# Ricarica i3
shortcuts-manager reload
```

### Metodo C: Modifica Manuale del File
Tutte le scorciatoie create dall'utente vengono salvate in modo isolato e sicuro in:
```text
~/.config/i3/custom_shortcuts.conf
```
Puoi aprire questo file con qualsiasi editor (es. `nano ~/.config/i3/custom_shortcuts.conf`), aggiungere le tue righe con la sintassi:
```ini
# Description: Il mio programma
bindsym $mod+Shift+x exec mio_comando
```
e poi premere **`Super + Shift + C`** per ricaricare la configurazione al volo.
