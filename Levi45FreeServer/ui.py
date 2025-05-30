from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.MenuList import MenuList
from Components.Button import Button
from Components.ProgressBar import ProgressBar
from .downloader import FreeServerDownloader
from .converter import FreeServerToOscamConverter
import threading

class Levi45FreeServerScreen(Screen):
    skin = """
    <screen position="center,center" size="700,550" title="Levi45 Free Server">
        <widget name="progress" position="10,10" size="680,20" />
        <widget name="status" position="10,40" size="680,30" font="Regular;22" />
        <widget name="server_count" position="10,80" size="680,25" font="Regular;20" foregroundColor="#00FF00" />
        <widget name="menu" position="10,120" size="680,380" scrollbarMode="showOnDemand" itemHeight="30" enableWrapAround="1" />
        <ePixmap name="red" position="10,510" size="160,40" pixmap="skin_default/buttons/red.png" zPosition="1" />
        <ePixmap name="green" position="190,510" size="160,40" pixmap="skin_default/buttons/green.png" zPosition="1" />
        <ePixmap name="yellow" position="370,510" size="160,40" pixmap="skin_default/buttons/yellow.png" zPosition="1" />
        <widget name="key_red" position="10,510" size="160,40" valign="center" halign="center" zPosition="2" font="Regular;20" transparent="1" foregroundColor="white" />
        <widget name="key_green" position="190,510" size="160,40" valign="center" halign="center" zPosition="2" font="Regular;20" transparent="1" foregroundColor="white" />
        <widget name="key_yellow" position="370,510" size="160,40" valign="center" halign="center" zPosition="2" font="Regular;20" transparent="1" foregroundColor="white" />
    </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.downloader = FreeServerDownloader()
        self.server_lines = []
        self.is_downloading = False
        
        # UI setup
        self["progress"] = ProgressBar()
        self["status"] = StaticText("Ready - Press GREEN to download")
        self["server_count"] = StaticText("")
        self["menu"] = MenuList([])
        self["key_red"] = Button("Exit")
        self["key_green"] = Button("Download")
        self["key_yellow"] = Button("Convert")
        
        self["actions"] = ActionMap(["ColorActions", "OkCancelActions"], {
            "red": self.exit_plugin,
            "green": self.start_download,
            "yellow": self.convert_servers,
            "cancel": self.exit_plugin,
        }, -1)
        
        self.onLayoutFinish.append(self.setInitialFocus)

    def setInitialFocus(self):
        try:
            self["key_green"].instance.setFocus(True)
        except:
            self.setFocus(self["key_green"])

    def exit_plugin(self):
        if self.is_downloading:
            self.downloader.stop_download()
            self["status"].setText("Download stopped")
        self.close()

    def start_download(self):
        if self.is_downloading:
            return
            
        self.is_downloading = True
        self.server_lines = []
        self["status"].setText("Downloading from GitHub...")
        self["server_count"].setText("")
        self["progress"].setRange((0, 100))
        self["progress"].setValue(0)
        self["menu"].setList(["Loading servers.txt..."])
        self["key_green"].setText("Working...")
        self["key_yellow"].setText("")

        def download_thread():
            try:
                servers = self.downloader.download_sync()
                self.server_lines = servers
                
                if servers:
                    display_list = []
                    for idx, server in enumerate(servers):
                        parts = server.split()
                        if len(parts) >= 5:
                            display_list.append(f"{idx+1:04d}. {parts[1]}:{parts[2]} (User:{parts[3]} Pass:{parts[4]})")
                    
                    self["menu"].setList(display_list)
                    self["status"].setText("Download complete")
                    self["server_count"].setText(f"Total: {len(servers)} server entries")
                    self["key_yellow"].setText("Convert")
                else:
                    self.show_error("No valid servers found")
                    
            except Exception as e:
                self.show_error(f"Error: {str(e)}")
            finally:
                self["progress"].setValue(100)
                self["key_green"].setText("Download")
                self.is_downloading = False

        threading.Thread(target=download_thread).start()

    def show_error(self, message):
        self["menu"].setList([
            "ERROR:",
            message,
            "",
            "Possible fixes:",
            "1. Check servers.txt format",
            "2. Verify internet connection",
            "3. Try again later"
        ])
        self["status"].setText("Operation failed")
        self["server_count"].setText("")

    def convert_servers(self):
        if not self.server_lines:
            self.show_error("No servers to convert")
            return
            
        try:
            converter = FreeServerToOscamConverter()
            config = converter.convert(self.server_lines)
            
            with open("/etc/tuxbox/config/oscam.server", "w") as f:
                f.write(config)
                
            self.session.open(
                MessageBox,
                f"Saved {len(self.server_lines)} server entries to oscam.server",
                MessageBox.TYPE_INFO
            )
        except Exception as e:
            self.show_error(f"Save failed: {str(e)}")