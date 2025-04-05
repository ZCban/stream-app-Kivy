# player.py
import subprocess
from kivy.utils import platform

if platform == 'android':
    from jnius import autoclass, cast
import os

class VideoStream:
    def __init__(self, url, previous_screen):
        self.url = url
        self.previous_screen = previous_screen

        if platform == 'android':
            self._open_vlc_android()
        elif platform == 'win':
            self._open_vlc_windows()
            #self._open_ffplay_windows()
        else:
            print("⚠️ Il sistema non supporta VLC esterno. URL:", self.url)

    def _open_vlc_android(self):
        try:
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')

            intent = Intent(Intent.ACTION_VIEW)
            intent.setDataAndType(Uri.parse(self.url), "video/*")
            intent.setPackage("org.videolan.vlc")  # Pacchetto ufficiale VLC

            currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
            currentActivity.startActivity(intent)

        except Exception as e:
            print("❌ Errore durante l'avvio di VLC su Android:", e)

    def _open_vlc_windows(self):
        try:
            vlc_path = "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe"  # Il percorso di VLC (verifica)
            if not os.path.exists(vlc_path):
                print("⚠️ VLC non trovato su Windows.")
                return

            # Costruisce il comando per eseguire VLC con l'URL .m3u8
            subprocess.Popen([vlc_path, self.url])
            print(f"🔊 VLC aperto su Windows per {self.url}")

        except Exception as e:
            print("❌ Errore durante l'avvio di VLC su Windows:", e)

    def _open_ffplay_windows(self):
        try:
            # Puoi modificare questo percorso se ffplay non è nel PATH
            subprocess.Popen(["ffplay","-autoexit", "-infbuf", self.url])
            print(f"▶️ ffplay avviato con: {self.url}")
        except Exception as e:
            print("❌ Errore durante l'avvio di ffplay:", e)
