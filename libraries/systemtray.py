import pystray
from PIL import Image
import psutil
import os
import threading
import time

class SystemTray:
    def __init__(self, app_instance):
        self.app = app_instance
        self.icon = None
        self.current_stats = "CPU: --% | RAM: -- MB"
        self.running = False
        self.create_system_tray()

    def create_system_tray(self):
        try:
            # Get icon path
            icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "icon.png")
            if not os.path.exists(icon_path):
                img = Image.new('RGB', (64, 64), color='green')
                img.save(icon_path)
            
            image = Image.open(icon_path)
            
            # Create menu with proper callback function
            def get_stats_text(item):
                return self.current_stats
            
            # Create menu items
            self.icon = pystray.Icon(
                "Minecraft Server",
                image,
                menu=pystray.Menu(
                    pystray.MenuItem(get_stats_text, lambda: None),
                    pystray.MenuItem("Show Window", self.show_window),
                    pystray.MenuItem("Start/Stop Server", self.toggle_server),
                    pystray.MenuItem("Quit", self.quit_app)
                )
            )
        except Exception as e:
            print(f"Error creating system tray: {e}")
            raise

    def update_stats(self):
        """Update server stats"""
        while self.running:
            try:
                if self.app.server_process and self.app.server_process.is_running():
                    cpu = self.app.server_process.cpu_percent(interval=1)
                    memory = self.app.server_process.memory_info().rss / 1024 / 1024
                    self.current_stats = f"CPU: {cpu}% | RAM: {memory:.1f} MB"
                else:
                    self.current_stats = "Server Not Running"
            except psutil.NoSuchProcess:
                self.current_stats = "Server Process Not Found"
            except psutil.AccessDenied:
                self.current_stats = "Access Denied to Process"
            except Exception as e:
                self.current_stats = "Stats Error"
                print(f"Error updating stats: {str(e)}")
            
            if self.icon:
                try:
                    self.icon.update_menu()
                except Exception as e:
                    print(f"Error updating menu: {str(e)}")
            
            time.sleep(2)

    def start(self):
        """Start the system tray icon and stats updater in background thread"""
        if self.icon and not self.running:
            self.running = True

            # Start stats update thread
            stats_thread = threading.Thread(target=self.update_stats, name="stats-updater", daemon=True)
            stats_thread.start()

            # Run tray icon in dedicated thread so it doesn't block the GUI
            def run_icon():
                try:
                    self.icon.run()
                finally:
                    self.running = False

            icon_thread = threading.Thread(target=run_icon, name="tray-icon", daemon=True)
            icon_thread.start()

    def show_window(self, icon, item):
        self.app.deiconify()
        self.app.focus_force()

    def toggle_server(self, icon, item):
        self.app.start_server()

    def quit_app(self, icon, item):
        self.running = False
        if self.app.server_process:
            self.app.server_process.kill()
        icon.stop()
        self.app.quit()