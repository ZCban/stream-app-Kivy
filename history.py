import json
import os
import shutil
from tkinter import filedialog, Tk

HISTORY_FILE = "history.json"

# ✅ Funzione per caricare e leggere il file 
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# ✅ Funzione per salvare il file
def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

# ✅ Funzione per aggiungere quando guardi eppisodi
def add_to_history(series_title, episode_label):
    history = load_history()
    if series_title not in history:
        history[series_title] = []
    if episode_label not in history[series_title]:
        history[series_title].append(episode_label)
    save_history(history)

# ✅ Funzione per esportare la cronologia
def export_history():
    Tk().withdraw()  # Nasconde la finestra principale
    file_path = filedialog.asksaveasfilename(defaultextension=".json",
                                             filetypes=[("JSON files", "*.json")],
                                             title="Esporta cronologia")
    if file_path:
        shutil.copyfile(HISTORY_FILE, file_path)
        return True
    return False

# ✅ Funzione per importare una cronologia da file
def import_history():
    Tk().withdraw()
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")],
                                           title="Importa cronologia")
    if file_path:
        shutil.copyfile(file_path, HISTORY_FILE)
        return True
    return False

# ✅ Funzione per eliminare la cronologia visione
def clear_history():
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
