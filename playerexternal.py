# player.py
import subprocess
import os
from kivy.utils import platform

if platform == 'android':
    from jnius import autoclass, cast


class VideoStream:
    def __init__(self, url, previous_screen,
                 use_streamlink=False,
                 use_ffplay=False,
                 headers=None,
                 ffplay_options=None):
        self.url = url
        self.previous_screen = previous_screen
        self.use_streamlink = use_streamlink
        self.use_ffplay = use_ffplay
        self.headers = headers or {}
        self.ffplay_options = ffplay_options or []

        if self.use_streamlink:
            self._open_with_streamlink()
        elif self.use_ffplay:
            self._open_ffplay_windows()
        elif platform == 'android':
            self._open_vlc_android()
        elif platform == 'win':
            self._open_vlc_windows()
        else:
            print("⚠️ Il sistema non supporta VLC esterno. URL:", self.url)

    def _open_vlc_android(self):
        try:
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')

            intent = Intent(Intent.ACTION_VIEW)
            intent.setDataAndType(Uri.parse(self.url), "video/*")
            intent.setPackage("org.videolan.vlc")

            currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
            currentActivity.startActivity(intent)

        except Exception as e:
            print("❌ Errore durante l'avvio di VLC su Android:", e)

    def _open_vlc_windows(self):
        try:
            vlc_path = "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe"
            if not os.path.exists(vlc_path):
                print("⚠️ VLC non trovato su Windows.")
                return

            subprocess.Popen([vlc_path, self.url])
            print(f"🔊 VLC aperto su Windows per {self.url}")

        except Exception as e:
            print("❌ Errore durante l'avvio di VLC su Windows:", e)

    def _open_ffplay_windows(self):
        try:
            command = ["ffplay"] + self.ffplay_options + ["-autoexit", "-infbuf"]

            if self.headers:
                # Crea una stringa header come richiesto da ffplay
                header_str = "".join(f"{k}: {v}\r\n" for k, v in self.headers.items())
                command += ["-headers", header_str]

            command.append(self.url)

            print(f"▶️ Avvio ffplay con: {' '.join(command)}")
            subprocess.Popen(command)
        except Exception as e:
            print("❌ Errore durante l'avvio di ffplay:", e)

    def _open_with_streamlink(self):
        try:
            command = ["streamlink"]

            for key, value in self.headers.items():
                command += ["--http-header", f"{key}={value}"]

            command += [self.url, "best"]

            print("🚀 Avvio stream con Streamlink + VLC:")
            print(" ".join(command))
            subprocess.Popen(command)
        except Exception as e:
            print("❌ Errore durante l'avvio di Streamlink:", e)

