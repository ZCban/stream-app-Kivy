import threading
import requests
from flask import Flask, Response, request
from werkzeug.serving import make_server

from kivy.config import Config
Config.set('kivy', 'video', 'ffpyplayer')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.video import Video
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.clock import Clock


# === FLASK PROXY ===
app = Flask(__name__)
_source_url = None
_headers = {}

_flask_started = False
_flask_lock = threading.Lock()
_server = None

def set_proxy_data(url, headers):
    global _source_url, _headers
    _source_url = url
    _headers = headers
    print("\n🧾 HEADER INVIATI AL PROXY:")
    for k, v in headers.items():
        print(f"  {k}: {v}")


@app.route('/proxy.m3u8')
def serve_m3u8():
    if not _source_url:
        return Response("⛔ Stream non inizializzato", status=503)
    try:
        r = requests.get(_source_url, headers=_headers)
        content = r.text

        def rewrite_line(line):
            line = line.strip()
            if line.startswith("#"):  # non riscrivere metadata
                return line
            if line.startswith("http"):
                return f"/segment.ts?url={line}"
            elif line.endswith(".ts"):
                base = _source_url.rsplit("/", 1)[0]
                return f"/segment.ts?url={base}/{line}"
            else:
                return line

        new_lines = [rewrite_line(line) for line in content.splitlines()]
        new_content = "\n".join(new_lines)

        print("\n📺 CONTENUTO .m3u8 PROXY:")
        print(new_content)
        print("🔚 FINE\n")

        return Response(new_content, mimetype='application/vnd.apple.mpegurl')
    except Exception as e:
        return Response(f"Errore nel proxy: {e}", status=500)


@app.route('/segment.ts')
def serve_ts():
    if not _source_url:
        return Response("⛔ Stream non inizializzato", status=503)
    try:
        ts_url = request.args.get("url")
        if not ts_url:
            return Response("❌ URL mancante", status=400)

        print(f"🎥 Scarico segmento: {ts_url}")
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


# === PLAYER KIVY ===
class VideoStreamSimple(BoxLayout):
    def __init__(self, url, previous_screen="main", **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.video_url = url
        self.previous_screen = previous_screen
        self.is_fullscreen = False

        self.video = Video(
            source=self.video_url,
            state='play',
            volume=1.0,
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            play=True
        )
        self.add_widget(self.video)

        top_controls = BoxLayout(size_hint_y=None, height=40, spacing=5)

        btn_back = Button(text='🖙 Indietro', on_press=self.go_back)
        self.btn_play = Button(text='⏸ Pausa', on_press=self.toggle_play)
        btn_fullscreen = Button(text='⛶ Fullscreen', on_press=self.toggle_fullscreen)

        self.volume_slider = Slider(min=0, max=1, value=1.0, step=0.01)
        self.volume_slider.bind(value=self.on_volume_change)

        self.volume_label = Label(text="100%")
        self.volume_slider.bind(value=self.update_volume_label)

        top_controls.add_widget(btn_back)
        top_controls.add_widget(self.btn_play)
        top_controls.add_widget(btn_fullscreen)
        top_controls.add_widget(Label(text="🔊"))
        top_controls.add_widget(self.volume_slider)
        top_controls.add_widget(self.volume_label)

        self.add_widget(top_controls)
        Clock.schedule_interval(self.update_play_button, 0.5)

    def toggle_play(self, instance):
        if self.video.state == 'play':
            self.video.state = 'pause'
            self.btn_play.text = '▶️ Play'
        else:
            self.video.state = 'play'
            self.btn_play.text = '⏸ Pausa'

    def update_play_button(self, dt):
        if not self.video:
            return
        self.btn_play.text = '⏸ Pausa' if self.video.state == 'play' else '▶️ Play'

    def toggle_fullscreen(self, instance):
        self.is_fullscreen = not self.is_fullscreen
        Window.fullscreen = 'auto' if self.is_fullscreen else False
        print("🖥️ Fullscreen ON" if self.is_fullscreen else "🖥️ Fullscreen OFF")

    def on_volume_change(self, instance, value):
        if self.video:
            self.video.volume = value

    def update_volume_label(self, instance, value):
        self.volume_label.text = f"{int(value * 100)}%"

    def stop(self):
        if self.video:
            self.video.state = 'stop'
            self.video.unload()
            print("🛑 Video fermato")

    def go_back(self, instance):
        self.stop()
        stop_flask()
        Window.fullscreen = False
        app = App.get_running_app()
        app.root.current = self.previous_screen


# === APP KIVY PER TEST ===
class VideoApp(App):
    def __init__(self, url, headers, **kwargs):
        super().__init__(**kwargs)
        set_proxy_data(url, headers)
        start_flask_once()

    def build(self):
        return VideoStreamSimple(url="http://127.0.0.1:5000/proxy.m3u8")

# === ESEMPIO USO ===
if __name__ == "__main__":
     url = "https://hls.kangal.icu/hls/skynba/index.m3u8"
     headers = {
         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
         "Referer": "https://calciostreaming.lat/",
     }
     VideoApp(url, headers).run()



    def build(self):
        return VideoStreamSimple(url="http://127.0.0.1:5000/proxy.m3u8")
