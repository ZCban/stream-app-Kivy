import time
import threading
import gc
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.window import Window
from ffpyplayer.player import MediaPlayer
from kivy.app import App

def format_time(seconds):
    if seconds is None or seconds < 0:
        return "--:--:--"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02}:{m:02}:{s:02}"

class VideoStreaminternal(BoxLayout):
    def __init__(self, url, previous_screen="main", **kwargs):
        super().__init__(orientation='vertical', **kwargs)

        self.previous_screen = previous_screen
        self.stream_url = url

        self.image = Image(fit_mode="contain", size_hint=(1, 1))
        self.add_widget(self.image)

        self.player = MediaPlayer(self.stream_url)#, ff_opts={'sync': 'video'}
        self.is_playing = True
        self.paused_time = 0
        self.is_fullscreen = False
        self.volume = 1.0
        self.is_muted = False
        self.video_quality_index = 0
        self.stretch_mode = True
        self._manual_seek = None
        self._force_refresh = False

        self._done = False
        self._frame_lock = threading.RLock()
        self.next_frame = None
        self.texture = None
        self.size = (0, 0)
        self._trigger = Clock.create_trigger(self.redraw)

        self._thread = threading.Thread(target=self._next_frame, daemon=True)
        self._thread.start()

        Window.bind(on_key_down=self.on_key_down)

        # --- Controls Layout ---
        controls = BoxLayout(size_hint_y=None, height=30)
        controls.add_widget(Button(text='🖙 Indietro', on_press=self.go_back))
        self.play_btn = Button(text='⏸️ Pausa', on_press=self.toggle_play)
        controls.add_widget(Button(text='⏪ -15s', on_press=self.rewind))
        controls.add_widget(self.play_btn)
        controls.add_widget(Button(text='⏭ +15s', on_press=self.forward))
        controls.add_widget(Button(text='🗁 Modalità', on_press=self.toggle_stretch_mode))
        controls.add_widget(Button(text='⛶ Fullscreen', on_press=self.toggle_fullscreen))
        self.add_widget(controls)

        bottom_controls = BoxLayout(size_hint_y=None, height=40, spacing=10, padding=[10, 0, 10, 0])
        bottom_controls.add_widget(Label(text="Vol", size_hint_x=None, width=30))

        self.volume_slider = Slider(min=0, max=1, value=self.volume, size_hint_x=0.2)
        self.volume_slider.bind(value=self.set_volume)
        bottom_controls.add_widget(self.volume_slider)

        self.mute_btn = Button(text="🔇", size_hint_x=None, width=40)
        self.mute_btn.bind(on_press=self.toggle_mute)
        bottom_controls.add_widget(self.mute_btn)

        self.quality_btn = Button(text="--", size_hint_x=None, width=90)
        self.quality_btn.bind(on_press=self.toggle_video_quality)
        bottom_controls.add_widget(self.quality_btn)

        self.seek_slider = Slider(min=0, max=1, value=0, size_hint_x=0.5)
        self.seek_slider.bind(on_touch_move=self.on_seek_touch_move)
        self.seek_slider.bind(on_touch_up=self.on_seek_touch_up)
        bottom_controls.add_widget(self.seek_slider)

        self.label_time = Label(text="🕒 Caricamento...", size_hint_x=None, width=150)
        bottom_controls.add_widget(self.label_time)

        self.add_widget(bottom_controls)


    def _next_frame(self):
        while not self._done:
            #if not self.is_playing:
            #    time.sleep(1 / 30.0)
            #    continue

            force = self._force_refresh
            #frame, val = self.player.get_frame(force_refresh=force)
            if force:
                self._force_refresh = False
            frame, val = self.player.get_frame(force_refresh=force)
            if val == 'eof':
                time.sleep(1 / 48.0)
            elif val == 'paused':
                time.sleep(1 / 48.0)
            else:
                if frame:
                    img, pts = frame
                    time.sleep(val)
                    with self._frame_lock:
                        self.next_frame = frame
                        self.paused_time = pts
                        self._trigger()
                else:
                    val= val if val else (1/48)
                    time.sleep(val)
                    #time.sleep(0.01)

                    


    def redraw(self, *args):
        # Se il player è stato chiuso, non continuare
        if not self.player:
            return

        with self._frame_lock:
            if not self.next_frame:
                return
            img, pts = self.next_frame

            if img.get_size() != self.size or self.texture is None:
                self.texture = Texture.create(size=img.get_size(), colorfmt='rgb')
                self.texture.flip_vertical()
                self.size = img.get_size()

            self.texture.blit_buffer(img.to_bytearray()[0], colorfmt='rgb', bufferfmt='ubyte')
            self.image.texture = None
            self.image.texture = self.texture
            self.next_frame = None
            gc.collect()

        current_time = self._manual_seek if self._manual_seek is not None else self.paused_time
        metadata = self.player.get_metadata()
        duration = metadata.get('duration')
        resolution = metadata.get('src_vid_size', None)
        frame_rate = metadata.get('frame_rate')

        if duration and duration > 0:
            self.label_time.text = f"{format_time(current_time)} / {format_time(duration)}"
            self.seek_slider.max = duration
            self.seek_slider.value = current_time
        else:
            self.label_time.text = "🔴 LIVE"

        if resolution:
            if frame_rate and isinstance(frame_rate, tuple) and frame_rate[1] != 0:
                fps = int(frame_rate[0] / frame_rate[1])
                fps_display = f"/{fps}"
            else:
                fps_display = ""
            self.quality_btn.text = f"{resolution[0]}x{resolution[1]}{fps_display}"

    def toggle_play(self, instance):
        self.is_playing = not self.is_playing
        self.play_btn.text = '▶️ Play' if not self.is_playing else '⏸️ Pausa'
        try:
            self.player.toggle_pause()
        except Exception as e:
            print("Errore toggle_pause:", e)

    def toggle_fullscreen(self, instance):
        self.is_fullscreen = not self.is_fullscreen
        Window.fullscreen = 'auto' if self.is_fullscreen else False
        if self.is_fullscreen:
            self.image.fit_mode = "fill"  # oppure "stretch"

    def rewind(self, instance):
        self.player.seek(-15.0)
        self._force_refresh = True


    def forward(self, instance):
        self.player.seek(15.0)
        self._force_refresh = True


    def on_seek_touch_move(self, instance, touch):
        if instance.collide_point(*touch.pos):
            relative_x = touch.pos[0] - instance.pos[0]
            percentage = relative_x / instance.width
            target_time = percentage * instance.max
            self._manual_seek = target_time
            self.seek_slider.value = target_time
            return True
        return False

    def on_seek_touch_up(self, instance, touch):
        if instance.collide_point(*touch.pos) and self._manual_seek is not None:
            self.player.seek(self._manual_seek, relative=False)
            self.paused_time = self._manual_seek
            self._force_refresh = True
            self._manual_seek = None
            return True
        return False

    def set_volume(self, instance, value):
        self.volume = value
        try:
            if not self.is_muted:
                self.player.set_volume(self.volume)
        except Exception as e:
            print("Errore volume:", e)

    def toggle_mute(self, instance):
        self.is_muted = not self.is_muted
        if self.is_muted:
            self.player.set_volume(0)
            self.mute_btn.text = "🔊"
        else:
            self.player.set_volume(self.volume)
            self.mute_btn.text = "🔇"

    def toggle_video_quality(self, instance):
        try:
            self.player.request_channel('video', 'cycle')
            self.video_quality_index += 1
            self._force_refresh = True
            print("📀 Qualità cambiata")
        except Exception as e:
            print("Errore cambio qualità video:", e)

    def toggle_stretch_mode(self, instance):
        if self.image.fit_mode == "contain":
            #self.image.fit_mode = "scale-down"
            self.image.fit_mode = "fill"
            instance.text = "🗁 Adatta"
        else:
            self.image.fit_mode = "contain"
            instance.text = "🗁 Originale"

    def on_key_down(self, window, key, scancode, codepoint, modifiers):
        try:
            if key == 32:
                self.toggle_play(None)
            elif key == 276:
                self.rewind(None)
            elif key == 275:
                self.forward(None)
            elif key == ord('f') or key == ord('F'):
                self.toggle_fullscreen(None)
            elif key == 273:
                self.volume_slider.value = min(self.volume_slider.value + 0.1, 1.0)
            elif key == 274:
                self.volume_slider.value = max(self.volume_slider.value - 0.1, 0.0)
        except Exception as e:
            print("Errore controllo tastiera:", e)

    def stop(self):
        self._done = True  # ferma il thread
        try:
            if self.player:
                self.player.close_player()
                self.player = None  # Forza rilascio
            Window.unbind(on_key_down=self.on_key_down)
            print("🛑 Video fermato e risorse rilasciate.")
        except Exception as e:
            print("❌ Errore durante lo stop del video:", e)

    def go_back(self, instance):
        self.stop()  # chiude il video
        # Accedi al root App e cambia schermata
        from kivy.app import App
        app = App.get_running_app()
        app.root.current = self.previous_screen


# Test rapido
def play_m3u8(url):
    from kivy.uix.screenmanager import ScreenManager, Screen
    class ManualTestScreen(Screen):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            stream = VideoStreaminternal(url=url, previous_screen="manual")
            self.add_widget(stream)

    class ManualTestApp(App):
        def build(self):
            sm = ScreenManager()
            sm.add_widget(ManualTestScreen(name="manual"))
            return sm

    ManualTestApp().run()


#if __name__ == "__main__":
#    test_url = "https://hfs295.serversicuro.cc/hls/dnzpf7gy5xg4a3gyvaqh533qtmsbk4z34tcb7ljoa,jyqtftow2zu65ijmclq,orqtftow2zwcgbwgibq,.urlset/master.m3u8"
#    play_m3u8(test_url)

