from kivy.metrics import sp
from kivy.clock import Clock
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.filemanager import MDFileManager
from kivymd.app import MDApp

import os
import shutil
from pytube import YouTube

class MainWindow(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.path = None
        self.dialog = None
        self.progress = 0
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            preview=True,
        )

    def file_manager_open(self):
        self.file_manager.show(os.path.abspath(os.getcwd()))  # output manager to the screen

    def select_path(self, path):
        self.path = path
        self.ids.download_path.text = path
        self.exit_manager()

    def exit_manager(self, *args):
        self.file_manager.close()

    def download_video(self):
        Clock.schedule_once(self.vid_download_background_process, 2)

    def download_audio(self):
        Clock.schedule_once(self.aud_download_background_process, 2)

    def vid_download_background_process(self, *args):
        if self.ids.video_url.text == "":
            self.ids.video_url.error = True
        elif not self.path or self.path == "":
            self.ids.download_path.error = True
        else:
            url = self.ids.video_url.text
            try:
                video_link = YouTube(url)
            except Exception as e:
                self.dialog = MDDialog(
                    title="Error!",
                    text=f"{e}",
                    buttons=[
                        MDIconButton(
                            icon="close-box",
                            theme_icon_color="Custom",
                            icon_size=sp(24),
                            icon_color=(1, 0, 0, 1)
                        )
                    ]
                )
                self.dialog.open()
            else:
                quality = video_link.streams.get_highest_resolution()
                video = quality.download()

                shutil.move(video, self.path)
                self.dialog = MDDialog(
                    title="Completed",
                    text="Download complete!",
                    buttons=[
                        MDIconButton(
                            icon="check",
                            icon_size=sp(24),
                            theme_icon_color="Custom",
                            icon_color=(0, 1, 0, 1),
                            on_release=self.close_dialog
                        )
                    ]
                )
                self.dialog.open()

    def aud_download_background_process(self, *args):
        if self.ids.video_url.text == "":
            self.ids.video_url.error = True
        elif not self.path or self.path == "":
            self.ids.download_path.error = True
        else:
            url = self.ids.video_url.text
            try:
                video_link = YouTube(url, on_progress_callback=self.progress_function)
            except Exception as e:
                self.dialog = MDDialog(
                    title="Error!",
                    text=f"{e}",
                    buttons=[
                        MDIconButton(
                            icon="close-box",
                            theme_icon_color="Custom",
                            icon_size=sp(24),
                            icon_color=(1, 0, 0, 1)
                        )
                    ]
                )
                self.dialog.open()
            else:
                quality = video_link.streams.get_audio_only()
                video = quality.download()

                base, ext = os.path.split(video)

                tmp = ext.split(" ")
                name = "".join(tmp)
                name, ext = name.split(".")
                mp3 = name + ".mp3"
                os.rename(video, mp3)

                shutil.move(mp3, self.path)
                self.dialog = MDDialog(
                    title="Completed",
                    text="Download complete!",
                    buttons=[
                        MDIconButton(
                            icon="check",
                            icon_size=sp(24),
                            theme_icon_color="Custom",
                            icon_color=(0, 1, 0, 1),
                            on_release=self.close_dialog
                        )
                    ]
                )
                self.dialog.open()

    def close_dialog(self, *args):
        self.dialog.dismiss(force=True)

class MainApp(MDApp):
    def __init__(self):
        super().__init__()
        self.title = "Video Downloader"

    def build(self):
        return MainWindow()

if __name__ == '__main__':
    MainApp().run()
