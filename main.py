import platform
import ssl
import subprocess
import os
import shutil
import http.client

from pytube import YouTube, Search
from functools import partial

from kivy.metrics import sp
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import StringProperty, ObjectProperty, ListProperty
from kivy.uix.recycleview import RecycleView

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.behaviors import FakeRectangularElevationBehavior
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.filemanager import MDFileManager
from kivymd.app import MDApp


# width = 288.96 * 2
# height = 618.24 * 2
#
# Window.size = (width, height)
# Window.left = 0
# Window.top = 0

""" Allowing App to access external storage path """

from android.storage import primary_external_storage_path
primary_ext_storage = primary_external_storage_path()

from android.permissions import request_permissions, Permission
request_permissions([Permission.WRITE_EXTERNAL_STORAGE])

"""================================================"""

class CustomCard(MDCard, FakeRectangularElevationBehavior):
    pass

class DetailCard(CustomCard):
    """ Implement: YouTubeObject, AsyncImage, Title, Author, Views, Publish Date """
    obj = ObjectProperty()
    image_url = StringProperty()
    title = StringProperty()
    author = StringProperty()
    views = StringProperty()
    publish_date = StringProperty()

class VideoCard(CustomCard):
    """ Implement: YouTubeObject, AsyncImage, Title, Author, Views, Publish Date, Download Button """
    obj = ObjectProperty()
    image_url = StringProperty()
    title = StringProperty()
    author = StringProperty()
    views = StringProperty()
    publish_date = StringProperty()

class RV(RecycleView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cycles = ListProperty()

    def add_data(self, *largs):
        try:
            cycle = self.cycles.pop(0)
        except IndexError:  # No more cycle
            return
        self.add(obj=cycle)

        Clock.schedule_once(self.add_data, 1.5)
        # self.data = [
        #     {
        #         "obj": data,
        #         "image_url": f"{data.thumbnail_url}",
        #         "title": f"{data.title}",
        #         "author": f"{data.author}",
        #         "views": f"{data.views:,}",
        #         "publish_date": f"{data.publish_date.strftime('%Y-%m-%d')}"
        #     }
        #     for data in list_data
        # ]

    def on_add(self, list_data):
        self.cycles = list_data
        self.data = []

        self.add_data()

    def add(self, obj):
        data = {
            "obj": obj,
            "image_url": f"{obj.thumbnail_url}",
            "title": f"{obj.title}",
            "author": f"{obj.author}",
            "views": f"{obj.views:,}",
            "publish_date": f"{obj.publish_date.strftime('%Y-%m-%d')}"
        }
        self.data.append(data)

class MainWindow(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.path = None
        self.dialog = MDDialog()
        self.progress = MDDialog(
            title="Downloading....!",
        )
        self.process_dialog = MDDialog(
            title="Searching...!",
            text="Please wait..."
        )
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            preview=True,
        )

        Clock.schedule_once(lambda x: self.check_network(), 1)

        """ Allow OpenSSL """

        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            # Legacy Python that doesn't verify HTTPS certificates by default
            pass
        else:
            # Handle target environment that doesn't support HTTPS verification
            ssl._create_default_https_context = _create_unverified_https_context

        """================"""

    def check_network(self):
        self.close_dialog()
        conn = http.client.HTTPSConnection("8.8.8.8", timeout=5)
        try:
            conn.request("HEAD", "/")
        except:
            self.dialog = MDDialog(
                title="Error!",
                text="No Internet!",
                buttons=[
                    MDRaisedButton(
                        text="Retry",
                        on_release=lambda x: Clock.schedule_once(lambda a: self.check_network(), 1)
                    )
                ]
            )
            self.dialog.open()
        else:
            self.close_dialog()
            return True

    def open_process(self):
        self.process_dialog.open()

    def close_process(self, *args):
        self.process_dialog.dismiss(force=True)

    def search_videos(self, title):
        self.open_process()
        try:
            Clock.schedule_once(partial(self.search_process, title), 2)
        except Exception as e:
            self.close_process()
            self.dialog = MDDialog(
                title="Oh No!",
                text=f"{e}",
                buttons=[
                    MDRaisedButton(
                        text="Close",
                        on_release=self.close_dialog
                    )
                ]
            )
            self.dialog.open()

    def search_process(self, title, *largs):
        try:
            search_obj = Search(title)
        except Exception as e:
            self.dialog = MDDialog(
                title="Oh No!",
                text=f"{e}",
                buttons=[
                    MDRaisedButton(
                        text="Close",
                        on_release=self.close_dialog
                    )
                ]
            )
            self.dialog.open()
        else:
            self.close_process()
            result = search_obj.results
            self.ids.rv.on_add(list_data=result)

    def add_detail(self, obj):
        self.ids.detail_card.obj = obj
        self.ids.detail_card.image_url = f"{obj.thumbnail_url}"
        self.ids.detail_card.title = f"{obj.title}"
        self.ids.detail_card.author = f"{obj.author}"
        self.ids.detail_card.views = f"{obj.views:,}"
        self.ids.detail_card.publish_date = f"{obj.publish_date.strftime('%Y-%m-%d')}"

    def file_manager_open(self):
        # self.file_manager.show('/')  # output manager to the screen
        self.file_manager.show(primary_ext_storage)

    def select_path(self, path):
        self.path = path
        self.ids.download_path.text = path
        self.exit_manager()

    def exit_manager(self, *args):
        self.file_manager.close()

    def download_video(self, obj):
        if self.check_network():
            self.progress.open()
            Clock.schedule_once(partial(self.vid_download_background_process, obj), 2)
        else:
            self.check_network()

    def download_audio(self, obj):
        if self.check_network():
            self.progress.open()
            Clock.schedule_once(partial(self.aud_download_background_process, obj), 2)
        else:
            self.check_network()

    def vid_download_background_process(self, obj, *largs):
        if self.ids.download_path.text == "":
            self.close_process_dialog()
            self.ids.download_path.error = True
            self.dialog = MDDialog(
                title="Missing Requirement!",
                text="Missing Download Path",
                buttons=[
                    MDRaisedButton(
                        text="Close",
                        on_release=self.close_dialog
                    )
                ]
            )
            self.dialog.open()
        else:
            try:
                quality = obj.streams.get_highest_resolution()
                video = quality.download()

                base, ext = os.path.split(video)

                name = ext
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
                # file_name = os.path.split(name)
                # source = file_name[1]
                self.close_process_dialog()
                self.dialog = MDDialog(
                    title="Completed",
                    text="Download complete!",
                    buttons=[
                        # MDRaisedButton(
                        #     text="Open",
                        #     on_release=lambda x: self.open_file(source)
                        # ),
                        # MDRaisedButton(
                        #     text="Show in folder",
                        #     on_release=lambda x: self.open_file_location()
                        # ),
                        MDRaisedButton(
                            text="Close",
                            on_release=self.close_dialog
                        )
                    ]
                )
                self.dialog.open()

    def aud_download_background_process(self, obj, *largs):
        if self.ids.download_path.text == "":
            self.close_process_dialog()
            self.ids.download_path.error = True
            self.dialog = MDDialog(
                title="Missing Requirement!",
                text="Missing Download Path",
                buttons=[
                    MDRaisedButton(
                        text="Close",
                        on_release=self.close_dialog
                    )
                ]
            )
            self.dialog.open()
        else:
            try:
                quality = obj.streams.get_audio_only()
                video = quality.download()

                base, ext = os.path.split(video)

                tmp = ext
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
                # file_name = os.path.split(mp3)
                # source = file_name[1]
                self.close_process_dialog()
                self.dialog = MDDialog(
                    title="Completed",
                    text="Download complete!",
                    buttons=[
                        # MDRaisedButton(
                        #     text="Open",
                        #     on_release=lambda x: self.open_file(source)
                        # ),
                        # MDRaisedButton(
                        #     text="Show in Folder!",
                        #     on_release=lambda x: self.open_file_location()
                        # ),
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
        self.dialog = None

    def close_dialog(self, *args):
        self.dialog.dismiss(force=True)

    def build(self):
        self.theme_cls.primary_palette = "Indigo"
        return MainWindow()

    def search(self, title):
        if self.root.check_network():
            try:
                # Clock.schedule_once(partial(self.root.search_videos, title, 2))
                self.root.search_videos(title=title)
            except Exception as e:
                self.dialog = MDDialog(
                    title="Error!",
                    text=f"{e}",
                    buttons=[
                        MDRaisedButton(
                            text="Close",
                            on_release=self.close_dialog
                        )
                    ]
                )
                self.dialog.open()
            else:
                self.goto_search()
        else:
            self.root.check_network()

    def goto_main(self):
        if self.root.ids.scrn_mngr.current == "second_page":
            self.root.ids.scrn_mngr.transition.direction = "right"
            self.root.ids.scrn_mngr.current = "first_page"
            self.root.ids.toolbar.right_action_items = [
                ['arrow-right-bold', lambda x: self.goto_search()]
            ]
            self.root.ids.toolbar.left_action_items = []

    def goto_search(self):
        if self.root.ids.scrn_mngr.current == "first_page":
            self.root.ids.scrn_mngr.transition.direction = "left"
            self.root.ids.scrn_mngr.current = "second_page"
            self.root.ids.toolbar.left_action_items = [
                ['arrow-left-bold', lambda x: self.goto_main()]
            ]
            self.root.ids.toolbar.right_action_items = []
        else:
            self.root.ids.scrn_mngr.transition.direction = "right"
            self.root.ids.scrn_mngr.current = "second_page"
            self.root.ids.toolbar.left_action_items = [
                ['arrow-left-bold', lambda x: self.goto_main()]
            ]

    def goto_download(self, obj):
        try:
            self.root.add_detail(obj=obj)
        except Exception as e:
            print(e)
        else:
            self.root.ids.scrn_mngr.transition.direction = "left"
            self.root.ids.scrn_mngr.current = "third_page"
            self.root.ids.toolbar.left_action_items = [
                ['arrow-left-bold', lambda x: self.goto_search()]
            ]

if __name__ == '__main__':
    MainApp().run()
