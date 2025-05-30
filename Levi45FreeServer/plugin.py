from Plugins.Plugin import PluginDescriptor
from .ui import Levi45FreeServerScreen
from .updater import PluginUpdater
import threading

__version__ = "1.1"  # Update with each release

def main(session, **kwargs):
    # Initialize updater and start background check
    updater = PluginUpdater(session)
    threading.Thread(target=updater.start_auto_check).start()
    
    # Open main screen
    session.open(Levi45FreeServerScreen)

def Plugins(**kwargs):
    return PluginDescriptor(
        name=f"Levi45 Free Server v{__version__}",
        description="Auto-updating CCcam server manager",
        where=PluginDescriptor.WHERE_PLUGINMENU,
        fnc=main,
        icon="plugin.png"
    )
