#!/usr/bin/env python3
"""
Antigravity Shortcuts Manager
Inspect, create, edit, and delete i3 keyboard shortcuts with Rofi & CLI interfaces.
"""

import sys
import os
import re
import subprocess
import shutil

I3_CONFIG = os.path.expanduser("~/.config/i3/config")
CUSTOM_CONF = os.path.expanduser("~/.config/i3/custom_shortcuts.conf")
ROFI_THEME = os.path.expanduser("~/.config/rofi/shortcuts.rasi")

CORE_DESCRIPTIONS = {
    "$mod+Return": "Terminale (Alacritty)",
    "$mod+Shift+Return": "File Manager (Ranger)",
    "$mod+Shift+m": "Monitor di Sistema (Btop)",
    "$mod+Shift+g": "Monitor GPU (nvitop / nvtop)",
    "$mod+Shift+w": "Menu Wi-Fi (Rofi)",
    "$mod+Shift+t": "Menu Bluetooth & Personalizzazione (Rofi)",
    "$mod+Shift+a": "Mixer Audio Modal (Alsamixer)",
    "$mod+Shift+b": "Selettore Sfondo & Tema Dinamico (Rofi)",
    "$mod+d": "Launcher Applicazioni (Rofi drun)",
    "$mod+q": "Chiudi finestra attiva",
    "$mod+Shift+q": "Forza chiusura finestra",
    "$mod+f": "Attiva/Disattiva Schermo Intero",
    "$mod+Shift+space": "Attiva/Disattiva Modalità Flottante",
    "$mod+space": "Alterna Focus (Tiling / Flottante)",
    "$mod+b": "Dividi orizzontalmente (Split H)",
    "$mod+v": "Dividi verticalmente (Split V)",
    "$mod+s": "Layout a Pila (Stacking)",
    "$mod+w": "Layout a Schede (Tabbed)",
    "$mod+e": "Alterna layout orizzontale/verticale",
    "$mod+a": "Focus al contenitore genitore",
    "$mod+Shift+c": "Ricarica configurazione i3 in memoria",
    "$mod+Shift+r": "Riavvia i3 sul posto",
    "$mod+Shift+e": "Menu Spegnimento / Blocco (Rofi)",
    "$mod+Escape": "Menu Spegnimento / Blocco (Rofi)",
    "$mod+h": "Focus a sinistra (Vim H)",
    "$mod+j": "Focus in basso (Vim J)",
    "$mod+k": "Focus in alto (Vim K)",
    "$mod+l": "Focus a destra (Vim L)",
    "$mod+Left": "Focus a sinistra (Freccia Sinistra)",
    "$mod+Down": "Focus in basso (Freccia Giù)",
    "$mod+Up": "Focus in alto (Freccia Su)",
    "$mod+Right": "Focus a destra (Freccia Destra)",
    "$mod+Shift+h": "Sposta finestra a sinistra (Vim H)",
    "$mod+Shift+j": "Sposta finestra in basso (Vim J)",
    "$mod+Shift+k": "Sposta finestra in alto (Vim K)",
    "$mod+Shift+l": "Sposta finestra a destra (Vim L)",
    "$mod+Shift+Left": "Sposta finestra a sinistra (Freccia)",
    "$mod+Shift+Down": "Sposta finestra in basso (Freccia)",
    "$mod+Shift+Up": "Sposta finestra in alto (Freccia)",
    "$mod+Shift+Right": "Sposta finestra a destra (Freccia)",
    "$mod+1": "Passa al Desktop 1",
    "$mod+2": "Passa al Desktop 2",
    "$mod+3": "Passa al Desktop 3",
    "$mod+4": "Passa al Desktop 4",
    "$mod+5": "Passa al Desktop 5",
    "$mod+6": "Passa al Desktop 6",
    "$mod+7": "Passa al Desktop 7",
    "$mod+8": "Passa al Desktop 8",
    "$mod+9": "Passa al Desktop 9",
    "$mod+0": "Passa al Desktop 10",
    "$mod+Shift+1": "Sposta finestra sul Desktop 1",
    "$mod+Shift+2": "Sposta finestra sul Desktop 2",
    "$mod+Shift+3": "Sposta finestra sul Desktop 3",
    "$mod+Shift+4": "Sposta finestra sul Desktop 4",
    "$mod+Shift+5": "Sposta finestra sul Desktop 5",
    "$mod+Shift+6": "Sposta finestra sul Desktop 6",
    "$mod+Shift+7": "Sposta finestra sul Desktop 7",
    "$mod+Shift+8": "Sposta finestra sul Desktop 8",
    "$mod+Shift+9": "Sposta finestra sul Desktop 9",
    "$mod+Shift+0": "Sposta finestra sul Desktop 10",
    "$mod+r": "Modalità Ridimensionamento Finestra",
    "XF86AudioRaiseVolume": "Volume +5% (bloccato max 100%)",
    "XF86AudioLowerVolume": "Volume -5%",
    "XF86AudioMute": "Muto Audio On/Off",
    "XF86AudioMicMute": "Muto Microfono On/Off",
    "XF86AudioPlay": "Riproduci / Pausa Multimediale",
    "XF86AudioNext": "Traccia Successiva",
    "XF86AudioPrev": "Traccia Precedente",
    "XF86MonBrightnessUp": "Luminosità Schermo +10%",
    "XF86MonBrightnessDown": "Luminosità Schermo -10%",
    "Print": "Screenshot area selezionata negli appunti",
    "F13": "Screenshot rapido negli appunti",
    "XF86Tools": "Screenshot rapido negli appunti",
    "$mod+Shift+s": "Screenshot area selezionata negli appunti",
    "Shift+Print": "Screenshot schermo intero negli appunti",
    "$mod+F1": "Gestione Scorciatoie (Questo menu)",
    "$mod+slash": "Gestione Scorciatoie (Questo menu)",
}

def notify(summary, body="", urgency="normal"):
    if shutil.which("dunstify"):
        subprocess.run(["dunstify", "-a", "Shortcuts", "-r", "7788", "-u", urgency, summary, body], check=False)
    elif shutil.which("notify-send"):
        subprocess.run(["notify-send", "-u", urgency, summary, body], check=False)

def ensure_custom_conf():
    if not os.path.exists(CUSTOM_CONF):
        os.makedirs(os.path.dirname(CUSTOM_CONF), exist_ok=True)
        with open(CUSTOM_CONF, "w") as f:
            f.write("# ==============================================================================\n")
            f.write("# Custom User Shortcuts (Managed by Shortcuts Manager)\n")
            f.write("# Syntax: bindsym <KeyCombo> exec [--no-startup-id] <Command>\n")
            f.write("# ==============================================================================\n\n")

    # Ensure include exists in ~/.config/i3/config
    if os.path.exists(I3_CONFIG):
        with open(I3_CONFIG, "r") as f:
            content = f.read()
        if "custom_shortcuts.conf" not in content:
            with open(I3_CONFIG, "a") as f:
                f.write("\n# ==============================================================================\n")
                f.write("# Custom User Shortcuts\n")
                f.write("# ==============================================================================\n")
                f.write("include ~/.config/i3/custom_shortcuts.conf\n")

def run_rofi(prompt, items=None, filter_text=None, message=None):
    cmd = ["rofi", "-dmenu", "-i", "-p", prompt, "-theme", ROFI_THEME]
    if filter_text:
        cmd.extend(["-filter", filter_text])
    if message:
        cmd.extend(["-mesg", message])

    input_data = "\n".join(items) if items else ""
    res = subprocess.run(cmd, input=input_data, stdout=subprocess.PIPE, text=True, check=False)
    if res.returncode == 0:
        return res.stdout.strip()
    return None

def normalize_key(key_str):
    k = key_str.strip()
    # Normalize Super, Win, Mod, mod -> $mod
    k = re.sub(r'^(super|win|mod)\b', '$mod', k, flags=re.IGNORECASE)
    k = re.sub(r'\+(super|win|mod)\b', '+$mod', k, flags=re.IGNORECASE)
    # Capitalize modifiers
    k = re.sub(r'\bshift\b', 'Shift', k, flags=re.IGNORECASE)
    k = re.sub(r'\bctrl\b|\bcontrol\b', 'Control', k, flags=re.IGNORECASE)
    k = re.sub(r'\balt\b|\bmod1\b', 'Mod1', k, flags=re.IGNORECASE)
    k = re.sub(r'\breturn\b|\benter\b', 'Return', k, flags=re.IGNORECASE)
    k = re.sub(r'\bspace\b', 'space', k, flags=re.IGNORECASE)
    k = re.sub(r'\besc\b|\bescape\b', 'Escape', k, flags=re.IGNORECASE)
    return k

def parse_custom_shortcuts():
    ensure_custom_conf()
    shortcuts = []
    current_desc = None

    if os.path.exists(CUSTOM_CONF):
        with open(CUSTOM_CONF, "r") as f:
            for line in f:
                line_str = line.strip()
                if not line_str:
                    continue
                if line_str.startswith("#"):
                    m_desc = re.match(r'^#\s*(?:Name|Desc|Description):\s*(.+)$', line_str, re.IGNORECASE)
                    if m_desc:
                        current_desc = m_desc.group(1).strip()
                    continue

                m_bind = re.match(r'^bindsym\s+(?:--release\s+)?([^\s]+)\s+exec\s+(?:--no-startup-id\s+)?(.+)$', line_str)
                if m_bind:
                    key = m_bind.group(1).strip()
                    cmd = m_bind.group(2).strip()
                    desc = current_desc or cmd
                    shortcuts.append({"key": key, "cmd": cmd, "desc": desc, "raw": line_str})
                    current_desc = None
                else:
                    current_desc = None
    return shortcuts

def parse_all_shortcuts():
    ensure_custom_conf()
    all_list = []

    # 1. Custom shortcuts
    for c in parse_custom_shortcuts():
        all_list.append({
            "key": c["key"],
            "cmd": c["cmd"],
            "desc": c["desc"],
            "is_custom": True
        })

    # 2. Core shortcuts from i3 config
    custom_keys = {c["key"] for c in all_list}
    if os.path.exists(I3_CONFIG):
        with open(I3_CONFIG, "r") as f:
            for line in f:
                line_str = line.strip()
                if line_str.startswith("#") or not line_str.startswith("bindsym"):
                    continue
                m = re.match(r'^bindsym\s+(?:--release\s+)?([^\s]+)\s+(.+)$', line_str)
                if m:
                    key = m.group(1).strip()
                    action = m.group(2).strip()
                    if key not in custom_keys:
                        desc = CORE_DESCRIPTIONS.get(key, action)
                        all_list.append({
                            "key": key,
                            "cmd": action,
                            "desc": desc,
                            "is_custom": False
                        })
                        custom_keys.add(key)
    return all_list

def save_custom_shortcuts(shortcuts):
    ensure_custom_conf()
    backup_path = CUSTOM_CONF + ".bak"
    if os.path.exists(CUSTOM_CONF):
        shutil.copy(CUSTOM_CONF, backup_path)

    with open(CUSTOM_CONF, "w") as f:
        f.write("# ==============================================================================\n")
        f.write("# Custom User Shortcuts (Managed by Shortcuts Manager)\n")
        f.write("# Syntax: bindsym <KeyCombo> exec [--no-startup-id] <Command>\n")
        f.write("# ==============================================================================\n\n")
        for s in shortcuts:
            f.write(f"# Description: {s['desc']}\n")
            f.write(f"bindsym {s['key']} exec --no-startup-id {s['cmd']}\n\n")

    # Verify i3 configuration syntax
    res = subprocess.run(["i3", "-C"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        # Revert
        if os.path.exists(backup_path):
            shutil.copy(backup_path, CUSTOM_CONF)
        err_msg = res.stderr.strip() or "Sintassi configurazione i3 non valida"
        notify("Errore Salvataggio Shortcut", err_msg, urgency="critical")
        return False, err_msg

    # Reload i3
    subprocess.run(["i3-msg", "reload"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(backup_path):
        os.remove(backup_path)
    return True, "OK"

def action_add(key=None, cmd=None, desc=None, is_gui=True):
    if is_gui:
        if not key:
            key_in = run_rofi("󰌌 Tasti scorciatoia :~$", message="Es. Mod+t, Mod+Shift+c, Control+Alt+t ($mod = Windows)")
            if not key_in:
                return
            key = normalize_key(key_in)

        # Check existing
        all_s = parse_all_shortcuts()
        existing = next((s for s in all_s if s["key"].lower() == key.lower()), None)
        if existing:
            warn = f"La combinazione '{key}' è già in uso per:\n'{existing['desc']}'\n\nVuoi sovrascriverla?"
            ans = run_rofi("󰅚 Conflitto :~$", ["󰄬 Sì, sovrascrivi", "󰅖 No, annulla"], message=warn)
            if not ans or "Sì" not in ans:
                return

        if not cmd:
            cmd = run_rofi("󰅂 Comando da eseguire :~$", message="Es. firefox, alacritty -e htop, code, pavucontrol")
            if not cmd:
                return

        if not desc:
            desc = run_rofi("󰅃 Descrizione / Nome :~$", message=f"Descrizione per '{cmd}' (invio per default)")
            if not desc:
                desc = cmd
    else:
        if not key or not cmd:
            print("Errore: devi specificare combinazione tasti e comando.")
            return False
        key = normalize_key(key)
        if not desc:
            desc = cmd

    shortcuts = parse_custom_shortcuts()
    # Remove existing if duplicate
    shortcuts = [s for s in shortcuts if s["key"].lower() != key.lower()]
    shortcuts.append({"key": key, "cmd": cmd, "desc": desc})

    success, msg = save_custom_shortcuts(shortcuts)
    if success:
        notify("󰄬 Shortcut Aggiunta", f"{key} 󰅂 {desc}\nEsegue: {cmd}")
        return True
    else:
        if not is_gui:
            print(f"Errore: {msg}")
        return False

def action_delete(target_key=None, is_gui=True):
    shortcuts = parse_custom_shortcuts()
    if not shortcuts:
        if is_gui:
            run_rofi("󰅖 Nessuna shortcut :~$", ["Nessuna scorciatoia personalizzata trovata."], message="Aggiungine una con l'opzione 'Aggiungi nuova scorciatoia'.")
        else:
            print("Nessuna scorciatoia personalizzata trovata.")
        return

    if is_gui:
        items = []
        for s in shortcuts:
            items.append(f"{s['key']:<22} 󰅂  {s['desc']}")
        choice = run_rofi("󰅖 Elimina shortcut :~$", items, message="Seleziona la scorciatoia da rimuovere:")
        if not choice:
            return
        selected_key = choice.split("󰅂")[0].strip()
    else:
        selected_key = normalize_key(target_key) if target_key else None

    if not selected_key:
        print("Errore: specificare la scorciatoia da rimuovere.")
        return

    filtered = [s for s in shortcuts if s["key"].lower() != selected_key.lower()]
    if len(filtered) == len(shortcuts):
        msg = f"Scorciatoia '{selected_key}' non trovata tra quelle personalizzate."
        if is_gui:
            notify("Attenzione", msg, urgency="normal")
        else:
            print(msg)
        return

    success, msg = save_custom_shortcuts(filtered)
    if success:
        notify("󰄬 Shortcut Eliminata", f"Rimossa la scorciatoia: {selected_key}")
    else:
        if not is_gui:
            print(f"Errore: {msg}")

def action_edit(is_gui=True):
    shortcuts = parse_custom_shortcuts()
    if not shortcuts:
        if is_gui:
            run_rofi("󰏫 Nessuna shortcut :~$", ["Nessuna scorciatoia personalizzata configurata."], message="Usa 'Aggiungi' per crearne una.")
        else:
            print("Nessuna scorciatoia personalizzata trovata.")
        return

    items = [f"{s['key']:<22} 󰅂  {s['desc']} ({s['cmd']})" for s in shortcuts]
    choice = run_rofi("󰏫 Modifica shortcut :~$", items, message="Seleziona la scorciatoia da modificare:")
    if not choice:
        return

    key = choice.split("󰅂")[0].strip()
    item = next((s for s in shortcuts if s["key"].lower() == key.lower()), None)
    if not item:
        return

    ops = [
        f"󰌌 Modifica combinazione tasti [{item['key']}]",
        f"󰅂 Modifica comando [{item['cmd']}]",
        f"󰅃 Modifica descrizione [{item['desc']}]",
        f"󰅖 Elimina questa scorciatoia"
    ]
    sub_choice = run_rofi(f"󰏫 {item['key']} :~$", ops)
    if not sub_choice:
        return

    if "Modifica combinazione tasti" in sub_choice:
        new_key = run_rofi("󰌌 Nuovi tasti :~$", filter_text=item["key"])
        if new_key:
            item["key"] = normalize_key(new_key)
    elif "Modifica comando" in sub_choice:
        new_cmd = run_rofi("󰅂 Nuovo comando :~$", filter_text=item["cmd"])
        if new_cmd:
            item["cmd"] = new_cmd
    elif "Modifica descrizione" in sub_choice:
        new_desc = run_rofi("󰅃 Nuova descrizione :~$", filter_text=item["desc"])
        if new_desc:
            item["desc"] = new_desc
    elif "Elimina" in sub_choice:
        shortcuts = [s for s in shortcuts if s["key"].lower() != item["key"].lower()]
        save_custom_shortcuts(shortcuts)
        notify("󰄬 Shortcut Rimossa", f"Eliminata: {item['key']}")
        return

    save_custom_shortcuts(shortcuts)
    notify("󰄬 Shortcut Aggiornata", f"{item['key']} 󰅂 {item['desc']}")

def action_list(is_gui=True):
    shortcuts = parse_all_shortcuts()
    if is_gui:
        items = []
        for s in shortcuts:
            tag = " 󰐕" if s.get("is_custom") else ""
            items.append(f"{s['key']:<24}{tag} 󰅂  {s['desc']}")
        choice = run_rofi("󰌌 Lista scorciatoie :~$", items, message="Cerca qualsiasi comando o tasto. Invio su un'app per avviarla:")
        if choice:
            key = choice.split("󰅂")[0].replace("󰐕", "").strip()
            item = next((s for s in shortcuts if s["key"] == key), None)
            if item and item.get("cmd", "").startswith("exec "):
                run_cmd = item["cmd"].replace("exec ", "").replace("--no-startup-id ", "").strip()
                subprocess.Popen(run_cmd, shell=True)
    else:
        print("=" * 80)
        print(f"{'TASTI SCORCIATOIA':<28} {'TIPO':<10} {'AZIONE / DESCRIZIONE'}")
        print("=" * 80)
        for s in shortcuts:
            tipo = "Custom" if s.get("is_custom") else "Core"
            print(f"{s['key']:<28} {tipo:<10} {s['desc']}")
        print("=" * 80)

def main_gui():
    ensure_custom_conf()
    while True:
        menu_items = [
            "󰌌  Visualizza tutte le scorciatoie (Cerca...)",
            "󰐕  Aggiungi nuova scorciatoia",
            "󰏫  Modifica scorciatoia personalizzata",
            "󰅖  Elimina scorciatoia personalizzata",
            "󰑐  Ricarica configurazione i3",
            "󰈆  Esci"
        ]
        choice = run_rofi("󰌌 Shortcuts Manager :~$", menu_items, message="Gestore Scorciatoie da Tastiera i3wm")
        if not choice or "Esci" in choice:
            break

        if "Visualizza tutte" in choice:
            action_list(is_gui=True)
        elif "Aggiungi nuova" in choice:
            action_add(is_gui=True)
        elif "Modifica scorciatoia" in choice:
            action_edit(is_gui=True)
        elif "Elimina scorciatoia" in choice:
            action_delete(is_gui=True)
        elif "Ricarica configurazione" in choice:
            subprocess.run(["i3-msg", "reload"], check=False)
            notify("󰑐 i3 Ricaricato", "Tutte le scorciatoie sono state ricaricate in memoria")

def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd in ("list", "-l", "--list"):
            action_list(is_gui=False)
        elif cmd in ("add", "-a", "--add"):
            key = sys.argv[2] if len(sys.argv) > 2 else None
            command = sys.argv[3] if len(sys.argv) > 3 else None
            desc = sys.argv[4] if len(sys.argv) > 4 else None
            action_add(key, command, desc, is_gui=False)
        elif cmd in ("delete", "remove", "rm", "-d"):
            key = sys.argv[2] if len(sys.argv) > 2 else None
            action_delete(key, is_gui=False)
        elif cmd in ("reload", "-r"):
            subprocess.run(["i3-msg", "reload"], check=False)
            print("Configurazione i3 ricaricata con successo.")
        elif cmd in ("gui", "menu", "--gui"):
            main_gui()
        elif cmd in ("help", "-h", "--help"):
            print("Uso: shortcuts-manager [COMANDO]")
            print("\nComandi:")
            print("  list                       Elenca tutte le scorciatoie (core e personalizzate)")
            print("  add <tasti> <cmd> [desc]   Aggiunge una nuova scorciatoia da tastiera")
            print("  delete <tasti>             Rimuove una scorciatoia personalizzata")
            print("  reload                     Ricarica i3 in tempo reale")
            print("  gui                        Apre l'interfaccia interattiva Rofi (default)")
        else:
            print(f"Comando non riconosciuto: {cmd}. Usa 'shortcuts-manager help'.")
    else:
        # Default: if stdin is a tty and DISPLAY is set, open GUI, else show CLI help
        if os.environ.get("DISPLAY"):
            main_gui()
        else:
            action_list(is_gui=False)

if __name__ == "__main__":
    main()
