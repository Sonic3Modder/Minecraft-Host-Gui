import os
import json
import threading
import customtkinter
import CTkScrollableDropdown
import CTkMessagebox
from tkinter import filedialog
import shutil
import psutil
import time
from libraries.directory_handler import change_server_directory
from libraries import mods_api
import pystray
from libraries.systemtray import SystemTray


class MyTabView(customtkinter.CTkTabview):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # create tabs
        self.add("Server Control")
        self.add("Settings")
        self.add("Browse")

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

        self.change_dir = customtkinter.CTkButton(
            master=self.tab('Settings'),
            text="Change Server Directory",
            command=lambda: change_server_directory(self)
        )
        self.change_dir.grid(row=0, column=0, padx=20, pady=10)

        # CurseForge API key field
        self.curseforge_label = customtkinter.CTkLabel(
            master=self.tab('Settings'),
            text="CurseForge API Key"
        )
        self.curseforge_label.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")
        self.curseforge_key_entry = customtkinter.CTkEntry(
            master=self.tab('Settings'),
            width=280
        )
        self.curseforge_key_entry.grid(row=2, column=0, padx=20, pady=5, sticky="w")
        self.save_key_btn = customtkinter.CTkButton(
            master=self.tab('Settings'),
            text="Save API Key",
            command=master.save_curseforge_key
        )
        self.save_key_btn.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        # Browse tab UI
        browse = self.tab("Browse")
        # Configure grid weights for a two-panel layout
        browse.grid_rowconfigure(2, weight=1)
        browse.grid_columnconfigure(1, weight=1)

        # Top search row spans across
        self.search_entry = customtkinter.CTkEntry(browse, placeholder_text="Search for mods/plugins...")
        self.search_entry.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="we")
        self.search_btn = customtkinter.CTkButton(browse, text="Search", command=master.on_search_projects, width=120)
        self.search_btn.grid(row=1, column=1, padx=10, pady=(0, 10), sticky="e")

        # Left side: provider/type, filters, results list
        self.sidebar = customtkinter.CTkFrame(browse)
        self.sidebar.grid(row=2, column=0, padx=(10, 6), pady=10, sticky="nsw")

        # Provider selector (radio buttons like a sidebar)
        self.provider_var = customtkinter.StringVar(value="Modrinth")
        self.provider_modrinth = customtkinter.CTkRadioButton(self.sidebar, text="Modrinth", variable=self.provider_var, value="Modrinth")
        self.provider_curseforge = customtkinter.CTkRadioButton(self.sidebar, text="CurseForge", variable=self.provider_var, value="CurseForge")
        self.provider_modrinth.grid(row=0, column=0, padx=10, pady=(10, 2), sticky="w")
        self.provider_curseforge.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")

        # Type segmented control
        self.type_segment = customtkinter.CTkSegmentedButton(self.sidebar, values=["mods", "plugins"]) 
        self.type_segment.set("mods")
        self.type_segment.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="we")

        # Filters
        self.version_label = customtkinter.CTkLabel(self.sidebar, text="Minecraft Version")
        self.version_label.grid(row=3, column=0, padx=10, pady=(0, 0), sticky="w")
        self.version_entry = customtkinter.CTkEntry(self.sidebar, width=160)
        self.version_entry.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="w")

        self.loader_label = customtkinter.CTkLabel(self.sidebar, text="Loader")
        self.loader_label.grid(row=5, column=0, padx=10, pady=(0, 0), sticky="w")
        self.loader_menu = customtkinter.CTkOptionMenu(
            self.sidebar,
            values=["-","forge","neoforge","fabric","quilt","bukkit","paper","spigot","purpur","folia","velocity","bungeecord","waterfall"]
        )
        self.loader_menu.set("-")
        self.loader_menu.grid(row=6, column=0, padx=10, pady=(0, 10), sticky="we")
        if _HAS_SCROLLABLE_DROPDOWN:
            try:
                self.loader_menu_dd = CTkScrollableDropdown(self.loader_menu, values=self.loader_menu.cget("values"))
            except Exception:
                self.loader_menu_dd = None

        # Sort selector
        self.sort_label = customtkinter.CTkLabel(self.sidebar, text="Sort by")
        self.sort_label.grid(row=7, column=0, padx=10, pady=(0, 0), sticky="w")
        self.sort_menu = customtkinter.CTkOptionMenu(self.sidebar, values=["Relevance", "Downloads", "Updated"])
        self.sort_menu.set("Relevance")
        self.sort_menu.grid(row=8, column=0, padx=10, pady=(0, 10), sticky="we")
        if _HAS_SCROLLABLE_DROPDOWN:
            try:
                self.sort_menu_dd = CTkScrollableDropdown(self.sort_menu, values=self.sort_menu.cget("values"))
            except Exception:
                self.sort_menu_dd = None

        # Results list
        self.results_frame = customtkinter.CTkScrollableFrame(self.sidebar, width=260, height=320)
        self.results_frame.grid(row=9, column=0, padx=10, pady=(0, 10), sticky="nswe")
        self.results_buttons = []

        # Right side: details panel
        self.detail_panel = customtkinter.CTkFrame(browse)
        self.detail_panel.grid(row=2, column=1, padx=(6, 10), pady=10, sticky="nsew")
        self.detail_panel.grid_columnconfigure(0, weight=1)
        self.detail_panel.grid_rowconfigure(2, weight=1)

        self.preview_icon = customtkinter.CTkLabel(self.detail_panel, text="", width=64, height=64)
        self.preview_icon.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        self.preview_desc = customtkinter.CTkTextbox(self.detail_panel, wrap="word")
        self.preview_desc.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.preview_desc.configure(state="disabled")

        # Versions + add button (bottom area of detail panel)
        self.bottom_bar = customtkinter.CTkFrame(self.detail_panel)
        self.bottom_bar.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="we")
        self.version_select = customtkinter.CTkOptionMenu(self.bottom_bar, values=["-"], width=300)
        self.version_select.set("-")
        self.version_select.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="w")
        # Upgrade to scrollable dropdown if available
        if _HAS_SCROLLABLE_DROPDOWN:
            try:
                self.version_select_dd = CTkScrollableDropdown(self.version_select, values=["-"])
            except Exception:
                self.version_select_dd = None
        self.add_btn = customtkinter.CTkButton(self.bottom_bar, text="Add to selected", command=master.on_install_selected, width=180)
        self.add_btn.grid(row=0, column=1, padx=0, pady=10, sticky="e")

        # Trigger initial search so the list is populated
        # Debounced initial search
        master._search_job = None
        master.after(200, master.on_search_projects)








class App(customtkinter.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Console")
        self.geometry("900x520")
        self.withdraw()  # hide main window
        
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.tab_view = MyTabView(master=self)
        self.tab_view.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
    
        self.server_process = None
        self.server_path = None
        self.folder_path = None
        
        # State for browse/install
        self._browse_state = {
            "selected_project": None,
            "selected_provider": "Modrinth",
            "selected_type": "mods",
            "curseforge_key": None,
            "version_map": {},
            "project_cache": {},
            "icon_cache": {}
        }

        # Load config for CurseForge key
        self._load_config()

        # Add system tray initialization
        self.system_tray = SystemTray(self)
        
        self.after(100, self.folder_dialog)
        # Start system tray icon (non-blocking)
        self.after(200, self.start_system_tray)

    # Config persistence
    def _config_path(self):
        try:
            base_dir = os.path.dirname(__file__)
        except Exception:
            base_dir = os.getcwd()
        return os.path.join(base_dir, "config.json")

    def _load_config(self):
        try:
            path = self._config_path()
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                key = data.get("curseforge_api_key")
                if key:
                    self._browse_state["curseforge_key"] = key
                    self.after(0, lambda: self.tab_view.curseforge_key_entry.insert(0, key))
        except Exception:
            pass

    def save_curseforge_key(self):
        key = self.tab_view.curseforge_key_entry.get().strip()
        self._browse_state["curseforge_key"] = key if key else None
        try:
            path = self._config_path()
            data = {}
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            data["curseforge_api_key"] = key
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            CTkMessagebox.CTkMessagebox(title="Saved", message="API key saved.")
        except Exception as e:
            CTkMessagebox.CTkMessagebox(title="Error", message=f"Failed to save key: {e}", icon="error")

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
                    batch_file.write(f"java --add-modules=jdk.incubator.vector -Xms2G -Xmx6G -jar {server_jar_name} nogui\n")
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

    def start_system_tray(self):
        """Start the system tray icon"""
        self.system_tray.start()  # This will run icon.run() in a separate thread

    # Browse/Install handlers
    def on_search_projects(self):
        # Debounce rapid calls
        try:
            if hasattr(self, "_search_job") and self._search_job is not None:
                self.after_cancel(self._search_job)
        except Exception:
            pass
        self._search_job = self.after(200, self._do_search_projects)

    def _do_search_projects(self):
        provider = self.tab_view.provider_var.get()
        sel_type = self.tab_view.type_segment.get()
        query = self.tab_view.search_entry.get().strip()
        mc_version = self.tab_view.version_entry.get().strip()
        sort = self.tab_view.sort_menu.get()
        loader = self.tab_view.loader_menu.get().strip()

        # Clear previous
        for btn in getattr(self.tab_view, 'results_buttons', []):
            btn.destroy()
        self.tab_view.results_buttons = []
        self._browse_state["selected_project"] = None
        self.tab_view.version_select.configure(values=["-"])
        self.tab_view.version_select.set("-")
        self._browse_state["version_map"] = {}

        def run():
            try:
                if provider == "Modrinth":
                    project_type = "mod" if sel_type == "mods" else "plugin"
                    index = "relevance"
                    if sort == "Downloads":
                        index = "downloads"
                    elif sort == "Updated":
                        index = "updated"
                    loaders = None
                    if loader and loader != "-":
                        loaders = [loader]
                    gversions = [mc_version] if mc_version else None
                    hits = mods_api.modrinth_search_projects(query, project_type, index=index, loaders=loaders, game_versions=gversions)
                    items = [(h.get("project_id"), h.get("title")) for h in hits]
                    payload = [(pid, name) for pid, name in items if pid and name]
                else:
                    key = self._browse_state.get("curseforge_key")
                    if not key:
                        return ("error", "CurseForge API key required. Save it in Settings.")
                    sort_field = None
                    if sort == "Downloads":
                        sort_field = 2  # Total Downloads
                    elif sort == "Updated":
                        sort_field = 3  # Last Updated
                    items = mods_api.curseforge_search_projects(query, sel_type, key, sort_field=sort_field)
                    payload = [ (it.get("id"), it.get("name")) for it in items ]

                return ("ok", payload)
            except Exception as e:
                return ("error", str(e))

        def done(result):
            status, data = result
            if status == "error":
                CTkMessagebox.CTkMessagebox(title="Search Error", message=data, icon="error")
                return
            for idx, (pid, name) in enumerate(data[:100]):
                btn = customtkinter.CTkButton(self.tab_view.results_frame, text=name, width=240,
                                              command=lambda p=pid, n=name: self.on_select_project(p, n))
                btn.grid(row=idx, column=0, padx=5, pady=3, sticky="w")
                self.tab_view.results_buttons.append(btn)

        def worker():
            result = run()
            self.after(0, lambda: done(result))

        threading.Thread(target=worker, daemon=True).start()

    def on_select_project(self, project_id, name):
        self._browse_state["selected_project"] = (project_id, name)
        provider = self.tab_view.provider_var.get()
        sel_type = self.tab_view.type_segment.get()
        mc_version = self.tab_view.version_entry.get().strip()
        loader = self.tab_view.loader_menu.get().strip()
        versions = [mc_version] if mc_version else None

        def run():
            try:
                if provider == "Modrinth":
                    # Fetch details (cache per project)
                    details = self._browse_state["project_cache"].get((provider, project_id)) if isinstance(self._browse_state.get("project_cache"), dict) else None
                    if not details:
                        details = mods_api.modrinth_get_project(project_id)
                        if isinstance(self._browse_state.get("project_cache"), dict):
                            self._browse_state["project_cache"][(provider, project_id)] = details
                    icon_url = details.get("icon_url")
                    desc = details.get("description") or details.get("slug") or name
                    # Build loader filter if provided
                    loaders = None
                    if loader and loader != "-":
                        loaders = [loader]
                    elif sel_type == "plugins":
                        loaders = ["paper", "bukkit", "spigot"]
                    vers = mods_api.modrinth_get_versions(project_id, loaders=loaders, game_versions=versions)
                    # Map display string to download URL
                    mapping = {}
                    options = []
                    for v in vers:
                        vname = v.get("version_number") or v.get("name") or "unknown"
                        files = v.get("files") or []
                        # Prefer primary file
                        if files:
                            primary = None
                            for f in files:
                                if f.get("primary"):
                                    primary = f
                                    break
                            if not primary:
                                primary = files[0]
                            url = primary.get("url") or primary.get("filename")
                            if url:
                                label = f"{vname}"
                                mapping[label] = url
                                options.append(label)
                    # Fallback: if filtering returned nothing, retry without filters
                    if not options and (loaders or versions):
                        vers = mods_api.modrinth_get_versions(project_id)
                        for v in vers:
                            vname = v.get("version_number") or v.get("name") or "unknown"
                            files = v.get("files") or []
                            if files:
                                primary = files[0]
                                url = primary.get("url") or primary.get("filename")
                                if url:
                                    mapping[vname] = url
                                    options.append(vname)
                    return ("ok", (options, mapping, icon_url, desc))
                else:
                    key = self._browse_state.get("curseforge_key")
                    proj = self._browse_state["project_cache"].get((provider, int(project_id))) if isinstance(self._browse_state.get("project_cache"), dict) else None
                    if not proj:
                        proj = mods_api.curseforge_get_project(int(project_id), key)
                        if isinstance(self._browse_state.get("project_cache"), dict):
                            self._browse_state["project_cache"][(provider, int(project_id))] = proj
                    logo = (proj.get("logo") or {}).get("url")
                    summary = proj.get("summary") or proj.get("name") or name
                    files = mods_api.curseforge_get_files(int(project_id), key)
                    mapping = {}
                    options = []
                    for f in files:
                        display = f.get("displayName") or f.get("fileName")
                        url = f.get("downloadUrl")
                        # Optional filter by mc version
                        if mc_version:
                            gvs = f.get("gameVersions") or []
                            if mc_version not in gvs:
                                continue
                        # Optional filter by loader (curseforge lists loaders inside gameVersions too)
                        if loader and loader != "-":
                            gvs = f.get("gameVersions") or []
                            if loader not in [x.lower() for x in gvs]:
                                continue
                        if display and url:
                            mapping[display] = url
                            options.append(display)
                    # Fallback if filters removed all options
                    if not options and (mc_version or (loader and loader != "-")):
                        mapping = {}
                        options = []
                        for f in files:
                            display = f.get("displayName") or f.get("fileName")
                            url = f.get("downloadUrl")
                            if display and url:
                                mapping[display] = url
                                options.append(display)
                    return ("ok", (options, mapping, logo, summary))
            except Exception as e:
                return ("error", str(e))

        def done(result):
            status, data = result
            if status == "error":
                CTkMessagebox.CTkMessagebox(title="Version Error", message=data, icon="error")
                return
            options, mapping, icon_url, desc = data
            if not options:
                options = ["-"]
            self._browse_state["version_map"] = mapping
            self.tab_view.version_select.configure(values=options)
            self.tab_view.version_select.set(options[0])
            if _HAS_SCROLLABLE_DROPDOWN and getattr(self.tab_view, 'version_select_dd', None) is not None:
                try:
                    self.tab_view.version_select_dd.configure(values=options)
                except Exception:
                    pass
            # Update description
            try:
                self.tab_view.preview_desc.configure(state="normal")
                self.tab_view.preview_desc.delete("1.0", "end")
                self.tab_view.preview_desc.insert("1.0", desc or "")
                self.tab_view.preview_desc.configure(state="disabled")
            except Exception:
                pass
            # Update icon (download bytes and display)
            try:
                if icon_url:
                    from PIL import Image, ImageTk
                    cache_key = icon_url
                    imgtk = self._browse_state["icon_cache"].get(cache_key) if isinstance(self._browse_state.get("icon_cache"), dict) else None
                    if not imgtk:
                        data = mods_api.fetch_bytes(icon_url)
                        import io
                        img = Image.open(io.BytesIO(data)).resize((64, 64))
                        imgtk = ImageTk.PhotoImage(img)
                        if isinstance(self._browse_state.get("icon_cache"), dict):
                            self._browse_state["icon_cache"][cache_key] = imgtk
                    self.tab_view.preview_icon.configure(image=imgtk)
                else:
                    self.tab_view.preview_icon.configure(image=None, text="")
            except Exception:
                self.tab_view.preview_icon.configure(image=None, text="")

        def worker():
            result = run()
            self.after(0, lambda: done(result))

        threading.Thread(target=worker, daemon=True).start()

    def on_install_selected(self):
        if not self.folder_path:
            CTkMessagebox.CTkMessagebox(title="Error", message="Select your server folder first.", icon="error")
            return
        selected = self._browse_state.get("selected_project")
        if not selected:
            CTkMessagebox.CTkMessagebox(title="Error", message="Select a project from search results.", icon="warning")
            return
        label = self.tab_view.version_select.get()
        url = self._browse_state.get("version_map", {}).get(label)
        if not url:
            CTkMessagebox.CTkMessagebox(title="Error", message="Select a version to install.", icon="warning")
            return
        sel_type = self.tab_view.type_menu.get()
        target_dir = os.path.join(self.folder_path, "mods" if sel_type == "mods" else "plugins")
        filename = os.path.basename(url.split("?")[0])
        dest = os.path.join(target_dir, filename)

        def run():
            try:
                mods_api.download_file(url, dest)
                return ("ok", dest)
            except Exception as e:
                return ("error", str(e))

        def done(result):
            status, data = result
            if status == "ok":
                CTkMessagebox.CTkMessagebox(title="Installed", message=f"Saved to {data}")
            else:
                CTkMessagebox.CTkMessagebox(title="Install Error", message=data, icon="error")

        def worker():
            result = run()
            self.after(0, lambda: done(result))

        threading.Thread(target=worker, daemon=True).start()

if __name__ == "__main__":
    app = App()
    app.mainloop()

