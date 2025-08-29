import os
from tkinter import filedialog
import CTkMessagebox

def change_server_directory(app_instance):
    """Function to handle changing server directory and updating paths"""
    folder_selected = filedialog.askdirectory()
    
    if not folder_selected:
        CTkMessagebox.CTkMessagebox(
            title="No Folder Selected",
            message="You did not select a folder. Please try again.",
            sound=True,
            icon="warning"
        )
        return False

    if not os.path.exists(folder_selected):
        CTkMessagebox.CTkMessagebox(
            title="Folder Not Found",
            message=f"The selected folder '{folder_selected}' does not exist.",
            sound=True,
            icon="error"
        )
        return False

    # Support being called with either the App instance or the TabView
    app = getattr(app_instance, 'master', app_instance)

    server_path = os.path.join(folder_selected, 'server.jar')
    if os.path.exists(server_path):
        app.server_path = server_path
        app.folder_path = folder_selected
        
        # Check and create batch file if needed
        batch_path = os.path.join(folder_selected, "server.bat")
        if not os.path.exists(batch_path):
            server_jar_name = os.path.basename(server_path)
            with open(batch_path, 'w') as batch_file:
                batch_file.write("@echo off\n")
                # JVM options must precede -jar; add nogui for headless server
                batch_file.write(f"java --add-modules=jdk.incubator.vector -Xms2G -Xmx6G -jar {server_jar_name} nogui\n")
                batch_file.write("pause")
        
        CTkMessagebox.CTkMessagebox(
            title="Server Found",
            message=f"Folder '{folder_selected}' contains 'server.jar'.",
            sound=True
        )
        # Ensure main window is shown and Start button is enabled
        try:
            app.deiconify()
            if getattr(app, 'tab_view', None) is not None:
                app.tab_view.start_button.configure(state="normal")
        except Exception:
            pass
        return True
    else:
        CTkMessagebox.CTkMessagebox(
            title="No Server Found",
            message=f"Folder '{folder_selected}' does not contain 'server.jar'. Please select a valid Minecraft server folder.",
            sound=True,
            icon="warning"
        )
        return False