import os
import customtkinter
import CTkMessagebox
from tkinter import filedialog
import shutil
import psutil
import time

class MyTabView(customtkinter.CTkTabview):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # create tabs
        self.add("Server Control")
        self.add("Settings")

        # add widgets on Server Control tab
        self.start_button = customtkinter.CTkButton(
            master=self.tab("Server Control"),
            text="Start Server",
            command=master.start_server,
            state="disabled"  # Initially disabled
        )
        self.start_button.grid(row=0, column=0, padx=20, pady=10)

        self.status_label = customtkinter.CTkLabel(
            master=self.tab("Server Control"),
            text="Server Status: Not Running"
        )
        self.status_label.grid(row=1, column=0, padx=20, pady=10)

class App(customtkinter.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Console")
        self.geometry("430x300")
        self.withdraw()  # hide main window
        
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.tab_view = MyTabView(master=self)
        self.tab_view.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
    
        self.server_process = None
        self.server_path = None
        self.folder_path = None
        
        self.after(100, self.folder_dialog)

    def start_server(self):
        """Start the Minecraft server using batch file"""
        if not self.server_path:
            CTkMessagebox.CTkMessagebox(
                title="Error",
                message="No server.jar selected",
                icon="error"
            )
            return

        try:
            server_dir = os.path.dirname(self.server_path)
            server_jar_name = os.path.basename(self.server_path)
            batch_path = os.path.join(server_dir, "server.bat")

            # Check if batch file exists, if not create it
            if not os.path.exists(batch_path):
                with open(batch_path, 'w') as batch_file:
                    batch_file.write("@echo off\n")
                    batch_file.write(f"java -Xms2G -Xmx6G -jar {server_jar_name} --add-modules=jdk.incubator.vector\n")
                    batch_file.write("pause")

            if self.server_process is None:  # Only start if not already running
                os.chdir(server_dir)
                self.server_process = psutil.Popen(
                    ["cmd", "/c", "server.bat"],
                    cwd=server_dir
                )
                self.tab_view.start_button.configure(text="Stop Server")
                self.track_server_process()
            else:  # Stop the server if it's running
                self.server_process.kill()
                self.server_process = None
                self.tab_view.start_button.configure(text="Start Server")
                self.tab_view.status_label.configure(text="Server Status: Stopped")
        except Exception as e:
            CTkMessagebox.CTkMessagebox(
                title="Error",
                message=f"Failed to start/stop server: {str(e)}",
                icon="error"
            )

    def track_server_process(self):
        """Monitor server.jar process"""
        if self.server_process:
            try:
                if self.server_process.is_running():
                    memory = self.server_process.memory_info().rss / 1024 / 1024
                    self.tab_view.status_label.configure(
                        text=f"Server Status: Running\nMemory Usage: {memory:.1f} MB"
                    )
                    self.after(5000, self.track_server_process)
                    return
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # If we get here, server process wasn't found
        self.tab_view.status_label.configure(text="Server Status: Not Running")
        self.tab_view.start_button.configure(text="Start Server")
        self.server_process = None
        self.after(5000, self.track_server_process)

    def folder_dialog(self):
        folder_selected = filedialog.askdirectory()
        if not folder_selected:
            CTkMessagebox.CTkMessagebox(
                title="No Folder Selected",
                message="You did not select a folder. Please try again.",
                sound=True,
                icon="warning"
            )
            self.after(100, self.folder_dialog)
            return

        if not os.path.exists(folder_selected):
            CTkMessagebox.CTkMessagebox(
                title="Folder Not Found",
                message=f"The selected folder '{folder_selected}' does not exist.",
                sound=True,
                icon="error"
            )
            self.after(100, self.folder_dialog)
            return

        server_path = os.path.join(folder_selected, 'server.jar')
        if os.path.exists(server_path):
            self.server_path = server_path
            self.folder_path = folder_selected
            
            # Check and create batch file if needed
            batch_path = os.path.join(folder_selected, "server.bat")
            if not os.path.exists(batch_path):
                server_jar_name = os.path.basename(server_path)
                with open(batch_path, 'w') as batch_file:
                    batch_file.write("@echo off\n")
                    batch_file.write(f"java -Xms2G -Xmx6G -jar {server_jar_name} --add-modules=jdk.incubator.vector\n")
                    batch_file.write("pause")
            
            CTkMessagebox.CTkMessagebox(
                title="Server Found",
                message=f"Folder '{folder_selected}' contains 'server.jar'.",
                sound=True
            )
            self.deiconify()
            # Enable start button when server is found
            self.tab_view.start_button.configure(state="normal")
        else:
            CTkMessagebox.CTkMessagebox(
                title="No Server Found",
                message=f"Folder '{folder_selected}' does not contain 'server.jar'. Please select a valid Minecraft server folder.",
                sound=True,
                icon="warning"
            )
            self.after(100, self.folder_dialog)

if __name__ == "__main__":
    app = App()
    app.mainloop()

