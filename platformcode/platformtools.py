# -*- coding: utf-8 -*-
# platformtools semplificato per uso fuori da Kodi

def dialog_ok(heading, message):
    print(f"[{heading}] {message}")

def dialog_notification(heading, message, icon=3, time=5000, sound=True):
    print(f"🔔 {heading}: {message}")

def dialog_yesno(heading, message, nolabel="No", yeslabel="Yes", autoclose=0, customlabel=None):
    print(f"[{heading}] {message}")
    risposta = input(f"{yeslabel}/{nolabel}? ").strip().lower()
    return risposta in ['yes', 'y', 'sì', 'si']

def dialog_input(default="", heading="", hidden=False):
    if hidden:
        import getpass
        return getpass.getpass(f"{heading}: ")
    else:
        return input(f"{heading} (default: {default}): ") or default

def dialog_select(heading, options, preselect=0, useDetails=False):
    print(f"{heading}")
    for i, opt in enumerate(options):
        print(f"{i + 1}. {opt}")
    try:
        scelta = int(input("Seleziona un'opzione: ")) - 1
        return scelta if 0 <= scelta < len(options) else -1
    except:
        return -1

def logger_debug(msg):
    print(f"[DEBUG] {msg}")

def logger_info(msg):
    print(f"[INFO] {msg}")

def logger_error(msg):
    print(f"[ERROR] {msg}")
