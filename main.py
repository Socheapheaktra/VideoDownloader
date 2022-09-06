import platform
import subprocess

from kivy.metrics import sp
from kivy.clock import Clock
from kivymd.toast import toast
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton, MDRaisedButton
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
        self.progress = MDDialog(
            title="Downloading....!",
        )
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
        self.progress.open()
        Clock.schedule_once(self.vid_download_background_process, 2)

    def download_audio(self):
        self.progress.open()
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
                self.close_process_dialog()
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
                try:
                    quality = video_link.streams.get_highest_resolution()
                    video = quality.download()

                    base, ext = os.path.split(video)

                    name = ext.replace(" ", "")
                    os.rename(video, name)

                    if os.path.isdir(self.path + '/' + name):
                        shutil.rmtree(self.path + '/' + name)

                    elif os.path.isfile(self.path + '/' + name):
                        os.remove(self.path + '/' + name)

                    shutil.move(name, self.path)
                except Exception as e:
                    self.close_process_dialog()
                    self.dialog = MDDialog(
                        title="Error!",
                        text=f"{e}",
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
                else:
                    file_name = os.path.split(name)
                    source = file_name[1]
                    self.close_process_dialog()
                    self.dialog = MDDialog(
                        title="Completed",
                        text="Download complete!",
                        buttons=[
                            MDRaisedButton(
                                text="Open",
                                on_release=lambda x: self.open_file(source)
                            ),
                            MDRaisedButton(
                                text="Show in folder",
                                on_release=lambda x: self.open_file_location()
                            ),
                            MDRaisedButton(
                                text="Close",
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
                video_link = YouTube(url)
            except Exception as e:
                self.close_process_dialog()
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
                try:
                    quality = video_link.streams.get_audio_only()
                    video = quality.download()

                    base, ext = os.path.split(video)

                    tmp = ext.replace(" ", "")
                    name, ext = tmp.split(".")
                    mp3 = name + ".mp3"
                    os.rename(video, mp3)

                    if os.path.isdir(self.path + '/' + mp3):
                        shutil.rmtree(self.path + '/' + mp3)

                    elif os.path.isfile(self.path + '/' + mp3):
                        os.remove(self.path + '/' + mp3)

                    shutil.move(mp3, self.path)
                except Exception as e:
                    self.close_process_dialog()
                    self.dialog = MDDialog(
                        title="Error!",
                        text=f"{e}",
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
                else:
                    file_name = os.path.split(mp3)
                    source = file_name[1]
                    self.close_process_dialog()
                    self.dialog = MDDialog(
                        title="Completed",
                        text="Download complete!",
                        buttons=[
                            MDRaisedButton(
                                text="Open",
                                on_release=lambda x: self.open_file(source)
                            ),
                            MDRaisedButton(
                                text="Show in Folder!",
                                on_release=lambda x: self.open_file_location()
                            ),
                            MDRaisedButton(
                                text="Close",
                                on_release=self.close_dialog
                            )
                        ]
                    )
                    self.dialog.open()

    def open_file(self, source):
        self.close_dialog()
        if platform.system() == "Windows":
            os.startfile(f"{self.path}/{source}")
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", f"{self.path}/{source}"])
        else:
            subprocess.Popen(["xdg-open", f"{self.path}/{source}"])

    def open_file_location(self):
        self.close_dialog()
        if platform.system() == "Windows":
            os.startfile(self.path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", self.path])
        else:
            subprocess.Popen(["xdg-open", self.path])

    def close_dialog(self, *args):
        self.dialog.dismiss(force=True)

    def close_process_dialog(self, *args):
        self.progress.dismiss(force=True)

class MainApp(MDApp):
    def __init__(self):
        super().__init__()
        self.title = "Video Downloader"

    def build(self):
        self.theme_cls.primary_palette = "Indigo"
        return MainWindow()

if __name__ == '__main__':
    MainApp().run()
