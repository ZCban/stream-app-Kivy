import threading
import requests
from flask import Flask, Response
from werkzeug.serving import make_server

from kivy.config import Config
Config.set('kivy', 'video', 'ffpyplayer')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.video import Video
from kivy.core.window import Window
from kivy.uix.button import Button

# === FLASK PROXY ===
app = Flask(__name__)
_source_url = None
_headers = {}

# Controllo singleton per il server Flask
_flask_started = False
_flask_lock = threading.Lock()
_server = None  # Oggetto server WSGI per lo shutdown

def set_proxy_data(url, headers):
    global _source_url, _headers
    _source_url = url
    _headers = headers

@app.route('/proxy.m3u8')
def serve_m3u8():
    if not _source_url:
        return Response("⛔ Stream non inizializzato", status=503)
    try:
        r = requests.get(_source_url, headers=_headers)
        return Response(r.text, mimetype='application/vnd.apple.mpegurl')
    except Exception as e:
        return Response(f"Errore nel proxy: {e}", status=500)

@app.route('/<path:segment>')
def serve_ts(segment):
    if not _source_url:
        return Response("⛔ Stream non inizializzato", status=503)
    try:
        base_url = _source_url.rsplit('/', 1)[0]
        ts_url = f"{base_url}/{segment}"
        r = requests.get(ts_url, headers=_headers, stream=True)
        return Response(r.iter_content(chunk_size=4096), content_type=r.headers.get('Content-Type'))
    except Exception as e:
        return Response(f"Errore nel TS proxy: {e}", status=500)

def start_flask():
    global _server
    print("🚀 Avvio server Flask su http://127.0.0.1:5000")
    _server = make_server("127.0.0.1", 5000, app)
    _server.serve_forever()

def start_flask_once():
    global _flask_started
    with _flask_lock:
        if not _flask_started:
            _flask_started = True
            threading.Thread(target=start_flask, daemon=True).start()

def stop_flask():
    global _server, _flask_started
    if _server:
        print("🛑 Arresto server Flask")
        _server.shutdown()
        _server = None
        _flask_started = False

# === KIVY VIDEO PLAYER (usa il proxy) ===
class VideoStreamSimple(BoxLayout):
    def __init__(self, url, previous_screen="main", **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.video_url = url
        self.previous_screen = previous_screen

        self.video = Video(
            source=self.video_url,
            state='play',
            volume=1.0,
            options={'allow_stretch': True},
            play=True,
            size_hint=(1, 1)
        )
        self.add_widget(self.video)

        # Controlli
        top_controls = BoxLayout(size_hint_y=None, height=40, spacing=5)
        btn_back = Button(text='🖙 Indietro', on_press=self.go_back)
        btn_play = Button(text='⏯', on_press=self.toggle_play)
        btn_fullscreen = Button(text='⛶', on_press=self.toggle_fullscreen)
        top_controls.add_widget(btn_back)
        top_controls.add_widget(btn_play)
        top_controls.add_widget(btn_fullscreen)
        self.add_widget(top_controls)

    def toggle_play(self, instance):
        self.video.state = 'pause' if self.video.state == 'play' else 'play'

    def toggle_fullscreen(self, instance):
        Window.fullscreen = not Window.fullscreen

    def stop(self):
        if self.video:
            self.video.state = 'stop'
            self.video.unload()
            print("🛑 Video fermato (Kivy Video)")

    def go_back(self, instance):
        self.stop()
        stop_flask()  # Ferma il server Flask quando si torna indietro
        app = App.get_running_app()
        app.root.current = self.previous_screen

# === KIVY APP (facoltativa se standalone) ===
class VideoApp(App):
    def __init__(self, url, referer, **kwargs):
        super().__init__(**kwargs)
        self.url = url
        self.referer = referer

    def build(self):
        return VideoStreamSimple(url="http://127.0.0.1:5000/proxy.m3u8")
        
# === MAIN  test===
#if __name__ == '__main__':
#    PAGINA_STREAM = "https://calcio.codes/live/everton-vs-arsenal"
#    risultati = estrai_link_m3u8_da_url(PAGINA_STREAM)

#     if not risultati:
#         print("❌ Nessuno stream trovato.")
#         exit(1)

#     SOURCE_URL = risultati[0]["url"]
#     REFERER = risultati[0]["referer"]
#     proxied_headers = get_headers_for_ffmpeg(SOURCE_URL, REFERER)#

#     print(f"🎬 Trovato:\n  ➤ Stream: {SOURCE_URL}\n  ➤ Referer: {REFERER}")

#     threading.Thread(target=start_flask, daemon=True).start()
#     VideoApp(SOURCE_URL, REFERER).run()

