import os
import requests
import shutil
import hashlib
from datetime import datetime, timedelta
from Tools.Directories import fileExists
from enigma import eTimer
import threading

GIT_REPO = "https://raw.githubusercontent.com/levi-45/free-cccam/main/Levi45FreeServer/"
PLUGIN_PATH = "/usr/lib/enigma2/python/Plugins/Extensions/Levi45FreeServer/"
UPDATE_CHECK_INTERVAL = 86400  # 24 hours in seconds

class PluginUpdater:
    def __init__(self, session):
        self.session = session
        self.last_check = None
        self.update_available = False
        self.latest_version = ""
        self.changelog = ""
        self.check_timer = eTimer()
        self.check_timer.timeout.get().append(self.background_check)

    def background_check(self):
        """Background update check without user interaction"""
        if self.check_for_update():
            from Screens.MessageBox import MessageBox
            self.session.openWithCallback(
                self.update_confirmed,
                MessageBox,
                f"New version {self.latest_version} available!\n\n{self.changelog}\n\nUpdate now?",
                MessageBox.TYPE_YESNO,
                timeout=30
            )

    def check_for_update(self):
        """Check for updates with enhanced validation"""
        try:
            # Skip if checked recently
            if self.last_check and (datetime.now() - self.last_check).seconds < UPDATE_CHECK_INTERVAL:
                return False

            # Get version info with timeout
            version_info = requests.get(
                f"{GIT_REPO}version.txt",
                timeout=15,
                headers={'Cache-Control': 'no-cache'}
            ).text.strip().splitlines()

            if len(version_info) >= 2:
                self.latest_version = version_info[0]
                self.changelog = version_info[1] if len(version_info) > 1 else "Bug fixes and improvements"
                
                if self.latest_version != __version__:
                    # Verify file integrity before marking as available
                    if self.verify_update_files():
                        self.update_available = True
                        self.last_check = datetime.now()
                        return True
            return False
        except Exception as e:
            print(f"[Levi45Updater] Check error: {str(e)}")
            return False

    def verify_update_files(self):
        """Verify all update files before proceeding"""
        required_files = ["plugin.py", "ui.py", "downloader.py", "converter.py"]
        try:
            for filename in required_files:
                response = requests.head(f"{GIT_REPO}{filename}", timeout=10)
                if response.status_code != 200:
                    return False
            return True
        except:
            return False

    def update_confirmed(self, answer):
        """Handle user update confirmation"""
        if answer:
            from Screens.Standby import TryQuitMainloop
            from Screens.MessageBox import MessageBox
            
            if self.update_plugin():
                self.session.openWithCallback(
                    self.restart_receiver,
                    MessageBox,
                    "Update successful! Receiver needs to restart.\nRestart now?",
                    MessageBox.TYPE_YESNO
                )
            else:
                self.session.open(
                    MessageBox,
                    "Update failed! Please try manually.",
                    MessageBox.TYPE_ERROR
                )

    def restart_receiver(self, answer):
        """Restart receiver if user confirms"""
        if answer:
            from Screens.Standby import TryQuitMainloop
            self.session.open(TryQuitMainloop, 3)

    def update_plugin(self):
        """Safe update procedure with rollback capability"""
        backup_success = False
        try:
            # Create backup with version suffix
            backup_dir = f"{PLUGIN_PATH}backup_v{__version__}"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

            # Backup current files
            files_to_update = ["plugin.py", "ui.py", "downloader.py", "converter.py", "updater.py"]
            for filename in files_to_update:
                src = f"{PLUGIN_PATH}{filename}"
                if fileExists(src):
                    shutil.copy2(src, backup_dir)
            
            backup_success = True

            # Download new files with verification
            for filename in files_to_update:
                response = requests.get(f"{GIT_REPO}{filename}", timeout=15)
                if response.status_code == 200:
                    with open(f"{PLUGIN_PATH}{filename}", "w") as f:
                        f.write(response.text)
                else:
                    raise Exception(f"Failed to download {filename}")

            # Verify critical files were updated
            if not all(fileExists(f"{PLUGIN_PATH}{f}") for f in files_to_update):
                raise Exception("Missing files after update")

            # Clean compiled python files
            for f in os.listdir(PLUGIN_PATH):
                if f.endswith(('.pyo', '.pyc')):
                    os.remove(f"{PLUGIN_PATH}{f}")

            return True

        except Exception as e:
            print(f"[Levi45Updater] Update error: {str(e)}")
            # Rollback if backup was successful
            if backup_success:
                self.restore_backup(backup_dir)
            return False

    def restore_backup(self, backup_dir):
        """Restore files from backup"""
        try:
            for filename in os.listdir(backup_dir):
                shutil.copy2(f"{backup_dir}/{filename}", PLUGIN_PATH)
            return True
        except:
            return False

    def start_auto_check(self):
        """Start background update checker"""
        self.check_timer.start(5000)  # Initial check after 5 seconds
