# main.py
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import AsyncImage
from kivy.clock import Clock
from kivy.core.window import Window
import threading


from config_utils import load_config, save_config
from history import load_history, save_history, clear_history, export_history, import_history , add_to_history
from playerexternal import VideoStream
from playerinternal import VideoStreaminternal
from playerLIVE import start_flask, set_proxy_data, VideoStreamSimple


# Importa i canali plugin
from channels_registry import CHANNELS


# =============================
# Temi
# =============================
THEMES = {
    "light": (1, 1, 1, 1),
    "dark": (0.1, 0.1, 0.1, 1)
}

config = load_config()
current_theme = config.get("theme", "dark")
highlight_color = config.get("highlight_color", [1, 1, 0, 1])


def apply_theme(theme_name):
    global current_theme
    current_theme = theme_name
    Window.clearcolor = THEMES[theme_name]
    config["theme"] = theme_name
    save_config(config)

apply_theme(current_theme)

# =============================
# Schermata di selezione canale
# =============================
class ChannelSelectorScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        settings_btn = Button(text="⚙️ Impostazioni", size_hint_y=None, height=40)
        settings_btn.bind(on_press=self.open_settings)
        layout.add_widget(settings_btn)

        layout.add_widget(Label(text="Scegli un canale", size_hint_y=None, height=50))

        for plugin in CHANNELS:
            btn = Button(text=plugin.get_name(), size_hint_y=None, height=50)
            btn.bind(on_press=lambda btn, p=plugin: self.select_channel(p))
            layout.add_widget(btn)

        self.add_widget(layout)

    def select_channel(self, plugin):
        main = self.manager.get_screen("main")
        main.set_channel(plugin)
        self.manager.current = "main"

    def open_settings(self, instance):
        self.manager.current = "settings"

# =============================
# MainScreen #home page provvider plugin
# =============================
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import AsyncImage
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
import threading
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout



from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout

# ... mantieni tutti gli altri import già presenti ...

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.plugin = None
        self.categories = {}
        self.current_category = None
        self.current_page = 1

        self.layout = BoxLayout(orientation='vertical')

        # Barra categorie
        self.category_bar = BoxLayout(size_hint=(1, 0.1))
        self.layout.add_widget(self.category_bar)

        # Contenuto serie
        self.scroll = ScrollView(size_hint=(1, 0.8))
        self.grid = GridLayout(cols=3, spacing=10, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid)
        self.layout.add_widget(self.scroll)

        # Barra inferiore
        self.pagination = BoxLayout(size_hint=(1, 0.1), padding=5, spacing=10)

        back_btn = Button(text="🔙 Canali", size_hint=(None, 1), width=100)
        back_btn.bind(on_press=self.go_to_channel_selector)

        search_btn = Button(text="🔍 Cerca", size_hint=(None, 1), width=100)
        search_btn.bind(on_press=self.open_search_popup)

        self.prev_btn = Button(text="<", size_hint=(None, 1), width=50)
        self.prev_btn.bind(on_press=self.prev_page)

        self.page_label = Label(text="Pagina 1", size_hint=(None, 1), width=100)

        self.next_btn = Button(text=">", size_hint=(None, 1), width=50)
        self.next_btn.bind(on_press=self.next_page)

        self.pagination.add_widget(back_btn)
        self.pagination.add_widget(search_btn)
        self.pagination.add_widget(self.prev_btn)
        self.pagination.add_widget(self.page_label)
        self.pagination.add_widget(self.next_btn)

        self.layout.add_widget(self.pagination)
        self.add_widget(self.layout)

    def open_search_popup(self, instance):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        text_input = TextInput(hint_text="Scrivi il titolo da cercare...", multiline=False, size_hint_y=None, height=40)
        search_btn = Button(text="Cerca", size_hint_y=None, height=40)

        popup = Popup(
            title="🔍 Cerca una titolo",
            content=layout,
            size_hint=(0.8, 0.4)
        )

        layout.add_widget(text_input)
        layout.add_widget(search_btn)

        def do_search(instance):
            query = text_input.text.strip()
            popup.dismiss()
            if not query:
                return
            if hasattr(self.plugin, "search_series"):
                def fetch():
                    try:
                        results = self.plugin.search_series(query)
                        Clock.schedule_once(lambda dt: self.display_series(results))
                    except Exception as e:
                        print(f"Errore nella ricerca: {e}")
                threading.Thread(target=fetch).start()
            else:
                print("⚠️ Questo plugin non supporta la ricerca.")

        search_btn.bind(on_press=do_search)
        popup.open()

    def set_channel(self, plugin):
        self.plugin = plugin
        self.categories = plugin.get_categories()
        self.current_category = list(self.categories.values())[0]
        self.current_page = 1
        self.build_category_bar()
        self.load_series()

    def build_category_bar(self):
        self.category_bar.clear_widgets()
        for name, url in self.categories.items():
            btn = Button(text=name)
            btn.bind(on_press=lambda btn, u=url: self.change_category(u))
            self.category_bar.add_widget(btn)

    def change_category(self, url):
        self.current_category = url
        self.current_page = 1
        self.load_series()

    def prev_page(self, instance):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_series()

    def next_page(self, instance):
        self.current_page += 1
        self.load_series()

    def load_series(self):
        def fetch():
            try:
                data = self.plugin.get_series_list(self.current_category, self.current_page)
                Clock.schedule_once(lambda dt: self.display_series(data))
            except Exception as e:
                print(f"Errore nel caricamento delle serie: {e}")

        threading.Thread(target=fetch).start()

    def display_series(self, series_list):
        self.page_label.text = f"Pagina {self.current_page}"
        self.grid.clear_widgets()

        for serie in series_list:
            box = BoxLayout(orientation='vertical', size_hint_y=None, height=220)
            image = AsyncImage(source=serie['poster'], size_hint=(1, None), height=180)
            title = Label(text=serie['title'], size_hint_y=None, height=30)
            btn = Button(text="Apri", size_hint_y=None, height=30)
            btn.bind(on_press=lambda b, s=serie: self.open_serie(s))
            box.add_widget(image)
            box.add_widget(title)
            box.add_widget(btn)
            self.grid.add_widget(box)

    def open_serie(self, serie):
        def fetch():
            try:
                episodes = self.plugin.get_episodes(serie['url'])

                def switch_screen(dt):
                    ep_screen = self.manager.get_screen("episodes")
                    ep_screen.set_plugin(self.plugin)
                    ep_screen.load_episodes(serie, episodes)
                    self.manager.current = "episodes"

                Clock.schedule_once(switch_screen)
            except Exception as e:
                print(f"Errore nel caricamento episodi: {e}")

        threading.Thread(target=fetch).start()

    def go_to_channel_selector(self, instance):
        self.manager.current = "channel_selector"






# =============================
# HistoryScreen
# =============================
class HistoryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')
        self.scroll = ScrollView()
        self.grid = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid)

        self.back_btn = Button(text="🔙 Torna indietro", size_hint_y=None, height=40)
        self.back_btn.bind(on_press=self.go_back)

        self.layout.add_widget(self.back_btn)
        self.layout.add_widget(self.scroll)
        self.add_widget(self.layout)

    def load_history(self):
        self.grid.clear_widgets()
        history = load_history()
        # Imposta il colore del testo in base al tema
        text_color = (1, 1, 1, 1) if current_theme == "dark" else (0, 0, 0, 1)

        for series_title, episodes in history.items():
            series_label = Label(text=f"[b]{series_title}[/b]", markup=True, size_hint_y=None, height=40,color=text_color)
            self.grid.add_widget(series_label)
            for ep in episodes:
                ep_label = Label(text=f"• {ep}", size_hint_y=None, height=30,color=text_color)
                self.grid.add_widget(ep_label)

    def go_back(self, instance):
        self.manager.current = "settings"

# =============================
# SettingsScreen
# =============================
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from history import load_history, save_history, clear_history
import json
import os

class SettingsScreen(Screen):
    HIGHLIGHT_COLORS = [
        ([0, 1, 0, 1], "🟩 Verde"),
        ([1, 0, 0, 1], "🟥 Rosso"),
        ([1, 1, 0, 1], "🟨 Giallo"),
        ([0, 0.5, 1, 1], "🟦 Azzurro"),
        ([1, 0.5, 0, 1], "🟧 Arancione"),
        ([0.5, 0.2, 0.8, 1], "🌸 viola"),
        ([0.8, 1, 0.6, 1], "💚 Verde Lime")
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')

        btn_history = Button(text="📺 Cronologia episodi visti", size_hint_y=None, height=50)
        btn_history.bind(on_press=self.open_history)

        self.theme_btn = Button(text="", size_hint_y=None, height=50)
        self.theme_btn.bind(on_press=self.toggle_theme)

        self.highlight_btn = Button(text="", size_hint_y=None, height=50)
        self.highlight_btn.bind(on_press=self.toggle_highlight_color)

        btn_export = Button(text="📤 Esporta cronologia", size_hint_y=None, height=50)
        btn_export.bind(on_press=self.export_history)

        btn_import = Button(text="📥 Importa cronologia", size_hint_y=None, height=50)
        btn_import.bind(on_press=self.import_history)

        btn_clear = Button(text="🗑️ Cancella cronologia", size_hint_y=None, height=50)
        btn_clear.bind(on_press=self.confirm_clear_history)

        back_btn = Button(text="🔙 Indietro", size_hint_y=None, height=50)
        back_btn.bind(on_press=self.go_back)

        self.layout.add_widget(btn_history)
        self.layout.add_widget(self.theme_btn)
        self.layout.add_widget(self.highlight_btn)
        self.layout.add_widget(btn_export)
        self.layout.add_widget(btn_import)
        self.layout.add_widget(btn_clear)
        self.layout.add_widget(back_btn)
        self.add_widget(self.layout)

        self.update_theme_label()
        self.update_highlight_label()

    def open_history(self, instance):
        history_screen = self.manager.get_screen("history")
        history_screen.load_history()
        self.manager.current = "history"

    def go_back(self, instance):
        self.manager.current = "channel_selector"

    def toggle_theme(self, instance):
        new_theme = "light" if current_theme == "dark" else "dark"
        apply_theme(new_theme)
        self.update_theme_label()

    def update_theme_label(self):
        icon = "🌞" if current_theme == "light" else "🌙"
        name = "Chiaro" if current_theme == "light" else "Scuro"
        self.theme_btn.text = f"{icon} Tema: {name}"

    def toggle_highlight_color(self, instance):
        global highlight_color
        current_index = next((i for i, (c, _) in enumerate(self.HIGHLIGHT_COLORS) if c == highlight_color), 0)
        new_index = (current_index + 1) % len(self.HIGHLIGHT_COLORS)
        highlight_color = self.HIGHLIGHT_COLORS[new_index][0]
        config["highlight_color"] = highlight_color
        save_config(config)
        self.update_highlight_label()

    def update_highlight_label(self):
        current = next((label for color, label in self.HIGHLIGHT_COLORS if color == highlight_color), "🟨 Giallo")
        self.highlight_btn.text = f"Colore episodi visti {current}"

    def export_history(self, instance):
        history = load_history()
        with open("history_export.json", "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
        self.show_popup("✅ Cronologia esportata in history_export.json")

    def import_history(self, instance):
        def load_file(_, selection, *args):
            if selection:
                try:
                    with open(selection[0], "r", encoding="utf-8") as f:
                        history = json.load(f)
                        save_history(history)
                    popup.dismiss()
                    self.show_popup("✅ Cronologia importata con successo.")
                except Exception as e:
                    self.show_popup(f"❌ Errore importazione: {e}")

        file_chooser = FileChooserIconView()
        file_chooser.bind(on_submit=load_file)

        popup = Popup(title="Importa cronologia",
                      content=file_chooser,
                      size_hint=(0.9, 0.9))
        popup.open()

    def confirm_clear_history(self, instance):
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text="Sei sicuro di voler cancellare tutta la cronologia?"))

        btns = BoxLayout(size_hint_y=None, height=50)
        yes_btn = Button(text="✅ Sì")
        no_btn = Button(text="❌ No")

        btns.add_widget(yes_btn)
        btns.add_widget(no_btn)
        content.add_widget(btns)

        popup = Popup(title="Conferma", content=content, size_hint=(None, None), size=(400, 200))

        def do_clear(*args):
            clear_history()
            popup.dismiss()
            self.show_popup("✅ Cronologia cancellata.")

        yes_btn.bind(on_press=do_clear)
        no_btn.bind(on_press=popup.dismiss)
        popup.open()

    def show_popup(self, msg):
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=msg))
        ok_btn = Button(text="OK", size_hint_y=None, height=40)
        content.add_widget(ok_btn)

        popup = Popup(title="Info", content=content, size_hint=(None, None), size=(400, 200))
        ok_btn.bind(on_press=popup.dismiss)
        popup.open()


# =============================
# EpisodeScreen
# =============================
class EpisodeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.plugin = None
        self.layout = BoxLayout(orientation='vertical')
        self.image = AsyncImage(size_hint=(1, None), height=300)
        self.title = Label(size_hint_y=None, height=40)
        self.scroll = ScrollView()
        self.grid = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid)
        self.back_btn = Button(text="🔙 Indietro", size_hint_y=None, height=40)
        self.back_btn.bind(on_press=self.go_back)

        self.layout.add_widget(self.back_btn)
        self.layout.add_widget(self.image)
        self.layout.add_widget(self.title)
        self.layout.add_widget(self.scroll)
        self.add_widget(self.layout)

    def set_plugin(self, plugin):
        self.plugin = plugin

    def load_episodes(self, serie, episodes):
        self.image.source = serie['poster']
        self.title.text = serie['title']
        self.grid.clear_widgets()

        seen = load_history().get(serie['title'], [])

        for ep in episodes:
            is_seen = ep['label'] in seen
            btn = Button(
                text=ep['label'],
                size_hint_y=None,
                height=40,
                background_color=highlight_color if is_seen else (1, 1, 1, 1),
                color=(0, 0, 0, 1) if is_seen else (1, 1, 1, 1)
            )
            btn.bind(on_press=lambda b, l=ep['link'], lbl=ep['label']: self.play_episode(l, lbl))
            self.grid.add_widget(btn)

    def go_back(self, instance):
        self.manager.current = "main"

    def play_episode(self, link, label):
        def fetch():
            m3u8 = self.plugin.resolve_stream_url(link)
            add_to_history(self.title.text, label)

            #for external play no kivy
            def switch_to_player(dt):
                #PlayerScreen.play(m3u8)
                VideoStream(url=m3u8, previous_screen=self.name)

            #for integreted player inside kivy
            def switch_to_player1(dt):
                player = self.manager.get_screen("player")
                player.previous_screen = self.name
                player.play(m3u8)
                self.manager.current = "player"

            Clock.schedule_once(switch_to_player)

        threading.Thread(target=fetch).start()

# =============================
# PlayerScreen
# =============================
class PlayerScreen1(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.previous_screen = "main"
        self.layout = BoxLayout(orientation='vertical')
        self.stream_widget = None
        self.add_widget(self.layout)

    def play(self, m3u8_url):
        if self.stream_widget:
            self.layout.remove_widget(self.stream_widget)
        self.stream_widget = VideoStreaminternal(url=m3u8_url, previous_screen=self.previous_screen)
        self.layout.add_widget(self.stream_widget)




# IMPORTA anche SOURCE_URL come stringa globale
SOURCE_URL = None  # se non importato direttamente da playerlive.py

class PlayerScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.previous_screen = "main"
        self.layout = BoxLayout(orientation='vertical')
        self.stream_widget = None
        self.add_widget(self.layout)

    def play(self, m3u8_data):
        global SOURCE_URL  # Rende modificabile la variabile globale

        # Rimuovi vecchio player se c'è
        if self.stream_widget:
            self.layout.remove_widget(self.stream_widget)
            self.stream_widget = None

        # --- Caso con proxy Flask ---
        if isinstance(m3u8_data, tuple):
            url, headers = m3u8_data

            # ✅ Passa i dati al proxy con la funzione corretta
            set_proxy_data(url, headers)

            # 2. Avvia il server Flask
            threading.Thread(target=start_flask, daemon=True).start()


            # 4. Usa il player che punta al proxy
            self.stream_widget = VideoStreamSimple(url="http://127.0.0.1:5000/proxy.m3u8", previous_screen=self.previous_screen)

        # --- Caso m3u8 diretto ---
        else:
            self.stream_widget = VideoStreaminternal(url=m3u8_data, previous_screen=self.previous_screen)

        # Aggiungi il player alla schermata
        self.layout.add_widget(self.stream_widget)


# =============================
# StreamingApp
# =============================
class StreamingApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(ChannelSelectorScreen(name="channel_selector"))
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(EpisodeScreen(name="episodes"))
        sm.add_widget(PlayerScreen(name="player"))
        sm.add_widget(SettingsScreen(name="settings"))
        sm.add_widget(HistoryScreen(name="history"))
        sm.current = "channel_selector"
        return sm

if __name__ == '__main__':
    StreamingApp().run()
