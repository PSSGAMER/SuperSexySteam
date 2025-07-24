# SuperSexySteam.py
#
# A graphical user interface (GUI) tool for managing Steam depot files
# (.lua and .manifest) with SQLite database backend. This script serves as the
# user-facing front-end with real-time game installation/uninstallation.
#
# Workflow:
# 1. On first launch, prompts the user to configure paths via modal dialogs.
#    These settings are saved permanently in 'config.ini'.
# 2. Presents a themed drag-and-drop interface. Users can drop a single .lua
#    file (named <AppID>.lua) along with any associated .manifest files.
# 3. The script organizes these files into a 'data/<AppID>/' directory structure,
#    overwriting any existing data for that AppID.
# 4. For new AppIDs: Immediately installs the game by running the complete workflow.
# 5. For existing AppIDs: First uninstalls the old version, then installs the new version.
# 6. All operations are tracked in a SQLite database for persistence and efficiency.
#
# Dependencies:
# - customtkinter: For the modern UI widgets.
# - tkinterdnd2: To enable drag-and-drop functionality.
# - Pillow (PIL): For dynamic image manipulation (header resizing and gradients).
# - sqlite3: For database operations (built into Python).

import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
import shutil
import re
import configparser
from PIL import Image, ImageDraw
import sys
import subprocess

# Import our custom modules
from greenluma_manager import configure_greenluma_injector
from database_manager import get_database_manager
from game_installer import GameInstaller


# =============================================================================
# --- THEME AND STYLING ---
# =============================================================================

class Theme:
    """
    A centralized class for storing all UI styling constants.
    This design makes it easy to modify the application's visual theme by
    editing values in a single location.
    """
    # Color Palette
    BG_DARK = "#212121"         # Main window background color
    BG_LIGHT = "#2b2b2b"        # Drop zone background color
    GOLD = "#ffbf00"            # Primary accent and button color
    DARK_GOLD = "#d4a000"       # Hover color for gold elements
    TEXT_PRIMARY = "#e0e0e0"    # Main text color
    TEXT_SECONDARY = "#aaaaaa"  # Lighter, secondary text color for placeholders

    # Status Feedback Colors
    STATUS_SUCCESS = "#76c7c0"  # Teal for success messages
    STATUS_ERROR = "#e57373"    # Soft red for error messages
    STATUS_WARNING = "#ffb74d"  # Amber for warning or update messages

    # Font Definitions
    FONT_PRIMARY = ("Segoe UI", 14)
    FONT_LARGE_BOLD = ("Segoe UI", 16, "bold")


# =============================================================================
# --- UTILITY FUNCTIONS ---
# =============================================================================

def create_gradient_image(width, height, color1, color2, vertical=True):
    """
    Generates a gradient image using Pillow and returns it as a CTkImage.
    This is used to create the dynamic, shiny border for the drop zone.

    Args:
        width (int): The width of the desired gradient image.
        height (int): The height of the desired gradient image.
        color1 (str): The starting color in hex format (e.g., "#ffbf00").
        color2 (str): The ending color in hex format (e.g., "#d4a000").
        vertical (bool): If True, the gradient is top-to-bottom. If False,
                         it is left-to-right.

    Returns:
        customtkinter.CTkImage or None: The generated image object ready to be
                                        used in a CTk widget, or None if
                                        width/height are invalid.
    """
    if width <= 0 or height <= 0:
        return None

    # Create a new transparent image to draw the gradient on.
    gradient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(gradient)

    # Convert hex colors to RGB integer tuples for mathematical operations.
    r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
    r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)

    # Iterate through each pixel row/column to draw the gradient.
    if vertical:
        for i in range(height):
            # Calculate the interpolated color for the current row.
            r = int(r1 + (i / height) * (r2 - r1))
            g = int(g1 + (i / height) * (g2 - g1))
            b = int(b1 + (i / height) * (b2 - b1))
            draw.line([(0, i), (width, i)], fill=(r, g, b))
    else:  # Horizontal
        for i in range(width):
            # Calculate the interpolated color for the current column.
            r = int(r1 + (i / width) * (r2 - r1))
            g = int(g1 + (i / width) * (g2 - g1))
            b = int(b1 + (i / width) * (b2 - b1))
            draw.line([(i, 0), (i, height)], fill=(r, g, b))

    return ctk.CTkImage(light_image=gradient, size=(width, height))


# =============================================================================
# --- SETUP DIALOG ---
# =============================================================================

class PathEntryDialog(ctk.CTkToplevel):
    """
    A reusable, modal dialog window for getting a path from the user.
    This is used exclusively for the first-time setup process. It features
    gray placeholder text that disappears when the user interacts with the entry box.
    """
    def __init__(self, parent, title: str, prompt_text: str, placeholder: str):
        """Initializes the dialog window and its widgets."""
        super().__init__(parent)
        self.transient(parent)  # Keep dialog on top of the parent window.
        self.title(title)
        self.geometry("500x180")
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.grab_set()  # Make the dialog modal (blocks interaction with parent).
        self.configure(fg_color=Theme.BG_DARK)

        self._placeholder = placeholder
        self._result = None  # This will store the final user input.

        # --- Widgets ---
        self.label = ctk.CTkLabel(self, text=prompt_text, font=Theme.FONT_PRIMARY, text_color=Theme.TEXT_PRIMARY)
        self.label.pack(padx=20, pady=(20, 10))

        self.entry = ctk.CTkEntry(self, width=450, fg_color=Theme.BG_LIGHT, border_color=Theme.GOLD, font=Theme.FONT_PRIMARY)
        self.entry.pack(padx=20, pady=5)

        self.confirm_button = ctk.CTkButton(self, text="Confirm", command=self._on_confirm, font=Theme.FONT_LARGE_BOLD,
                                             fg_color=Theme.GOLD, text_color=Theme.BG_DARK, hover_color=Theme.DARK_GOLD)
        self.confirm_button.pack(pady=(10, 20))

        # --- Event Bindings for Placeholder ---
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self._set_placeholder()

    def _set_placeholder(self):
        """Clears the entry and inserts the gray placeholder text."""
        self.entry.delete(0, "end")
        self.entry.insert(0, self._placeholder)
        self.entry.configure(text_color=Theme.TEXT_SECONDARY)

    def _on_focus_in(self, event):
        """Removes placeholder text when the user clicks in the entry box."""
        if self.entry.get() == self._placeholder:
            self.entry.delete(0, "end")
            self.entry.configure(text_color=Theme.TEXT_PRIMARY)

    def _on_focus_out(self, event):
        """Restores placeholder text if the user clicks away and the box is empty."""
        if not self.entry.get():
            self._set_placeholder()

    def _on_confirm(self):
        """Saves the user's input and closes the dialog."""
        current_text = self.entry.get()
        # If the box is empty or still has the placeholder, return an empty string
        # to signal that the default value should be used.
        if current_text == self._placeholder or not current_text:
            self._result = ""
        else:
            self._result = current_text
        self.grab_release()
        self.destroy()

    def _on_cancel(self):
        """Sets the result to None and closes the dialog if the user cancels."""
        self._result = None
        self.grab_release()
        self.destroy()

    def get_input(self):
        """
        Public method to show the dialog and retrieve the result.
        This method blocks the execution of the calling code until the dialog is closed.

        Returns:
            str or None: The user's input, an empty string for default, or
                         None if the dialog was cancelled by closing the window.
        """
        self.master.wait_window(self)
        return self._result


# =============================================================================
# --- MAIN APPLICATION ---
# =============================================================================

class App(TkinterDnD.Tk):
    """
    The main application class for SuperSexySteam.

    This class builds the GUI, handles all user interactions (drag-and-drop,
    button clicks), manages the SQLite database, and orchestrates
    real-time game installation and uninstallation operations.
    """
    def __init__(self, config: configparser.ConfigParser):
        """
        Initializes the main application window and all its components.

        Args:
            config (configparser.ConfigParser): The loaded application configuration.
        """
        super().__init__()
        # Renamed to `app_config` to avoid collision with the built-in `self.config()` method.
        self.app_config = config

        # Initialize database and game installer
        self.db = get_database_manager()
        self.game_installer = GameInstaller(config)

        # --- Window Configuration ---
        # The root window is a standard Tk object, so it uses 'background' for its color.
        self.configure(background=Theme.BG_DARK)
        self.title("SuperSexySteam")
        self.geometry("600x750")  # Made taller to accommodate database stats
        self.minsize(550, 700)
        
        # --- Window Icon ---
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
            if os.path.exists(icon_path):
                self.wm_iconbitmap(icon_path)
        except Exception as e:
            print(f"[WARNING] Failed to load window icon: {e}")

        # --- Header Image ---
        try:
            header_path = os.path.join(os.path.dirname(__file__), "header.png")
            header_pil_image = Image.open(header_path)

            # Resize the image programmatically to prevent a large image from breaking the layout.
            MAX_HEADER_WIDTH = 500
            original_width, original_height = header_pil_image.size
            if original_width > MAX_HEADER_WIDTH:
                aspect_ratio = original_height / original_width
                new_height = int(MAX_HEADER_WIDTH * aspect_ratio)
                header_pil_image = header_pil_image.resize((MAX_HEADER_WIDTH, new_height), Image.Resampling.LANCZOS)

            self.header_image = ctk.CTkImage(light_image=header_pil_image, size=header_pil_image.size)
            header_widget = ctk.CTkLabel(self, image=self.header_image, text="", bg_color="transparent")
        except FileNotFoundError:
            # Fallback to a text title if 'header.png' is not found.
            header_widget = ctk.CTkLabel(self, text="SuperSexySteam", font=("Impact", 48), text_color=Theme.GOLD, bg_color="transparent")
        header_widget.pack(pady=(20, 10))

        # --- Database Stats Panel ---
        self.stats_frame = ctk.CTkFrame(self, fg_color=Theme.BG_LIGHT, corner_radius=10)
        self.stats_frame.pack(padx=20, pady=(0, 10), fill="x")
        
        stats_title = ctk.CTkLabel(self.stats_frame, text="Database Statistics", font=Theme.FONT_LARGE_BOLD, text_color=Theme.GOLD)
        stats_title.pack(pady=(10, 5))
        
        self.stats_label = ctk.CTkLabel(self.stats_frame, text="Loading...", font=Theme.FONT_PRIMARY, text_color=Theme.TEXT_PRIMARY)
        self.stats_label.pack(pady=(0, 10))
        
        # Update stats initially
        self.update_database_stats()

        # --- Drop Zone ---
        # This outer frame's only purpose is to bind to the window resize event and hold the gradient.
        self.gradient_border_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.gradient_border_frame.pack(expand=True, fill="both", padx=20, pady=10)
        self.gradient_border_frame.bind("<Configure>", self._update_gradient_border)

        # This inner frame is the actual drop target and holds the UI elements.
        self.drop_frame = ctk.CTkFrame(self.gradient_border_frame, fg_color=Theme.BG_LIGHT, border_width=0, corner_radius=10)
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.on_drop)

        # Drop Zone Widgets
        plus_font = ctk.CTkFont(family="Impact", size=120)
        self.plus_label = ctk.CTkLabel(self.drop_frame, text="+", font=plus_font, text_color=Theme.TEXT_SECONDARY)
        self.plus_label.place(relx=0.5, rely=0.45, anchor="center")
        self.info_label = ctk.CTkLabel(self.drop_frame, text="Drag and drop Lua + Manifest files here", font=Theme.FONT_LARGE_BOLD, text_color=Theme.TEXT_PRIMARY)
        self.info_label.place(relx=0.5, rely=0.7, anchor="center")

        # --- Action Buttons Frame ---
        self.buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.buttons_frame.pack(pady=(10, 0), padx=20, fill="x")

        # --- Refresh Stats Button ---
        self.refresh_button = ctk.CTkButton(self.buttons_frame, text="Refresh Stats", font=Theme.FONT_PRIMARY, text_color=Theme.BG_DARK,
                                           fg_color=Theme.STATUS_SUCCESS, hover_color="#4caf50", border_width=0,
                                           corner_radius=8, command=self.update_database_stats, width=120)
        self.refresh_button.pack(side="left", padx=(0, 10))

        # --- Clear Database Button ---
        self.clear_db_button = ctk.CTkButton(self.buttons_frame, text="Clear Database", font=Theme.FONT_PRIMARY, text_color=Theme.TEXT_PRIMARY,
                                            fg_color=Theme.STATUS_WARNING, hover_color="#ff9800", border_width=0,
                                            corner_radius=8, command=self.on_clear_database_click, width=120)
        self.clear_db_button.pack(side="left", padx=(0, 10))

        # --- Clear Data Button (small, positioned in top-right) ---
        self.clear_button = ctk.CTkButton(self, text="Clear Data", font=("Segoe UI", 10), text_color=Theme.TEXT_PRIMARY,
                                          fg_color=Theme.STATUS_ERROR, hover_color="#c62828", border_width=0,
                                          corner_radius=5, command=self.on_clear_data_click, width=80, height=25)
        self.clear_button.place(relx=0.98, rely=0.02, anchor="ne")

        # --- Status Label ---
        self.status_label = ctk.CTkLabel(self, text="Ready for action. Drop files to install games instantly!", font=Theme.FONT_PRIMARY,
                                          text_color=Theme.TEXT_SECONDARY, bg_color="transparent")
        self.status_label.pack(side="bottom", fill="x", padx=20, pady=(0, 10))

    def _update_gradient_border(self, event):
        """
        Event handler called when the window is resized. It redraws the gradient
        background to fit the new size, ensuring a crisp look. It also ensures
        the drop_frame is layered correctly on top of the gradient.
        """
        w, h = event.width, event.height
        gradient = create_gradient_image(w, h, Theme.GOLD, Theme.DARK_GOLD, vertical=False)
        if gradient:
            # Create the gradient label only once, then just update its image.
            if not hasattr(self, 'gradient_label'):
                self.gradient_label = ctk.CTkLabel(self.gradient_border_frame, image=gradient, text="")
                self.gradient_label.place(x=0, y=0, relwidth=1.0, relheight=1.0)
            else:
                self.gradient_label.configure(image=gradient)

            # Place the inner drop_frame with a small negative padding to create a border effect.
            self.drop_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=1.0, relheight=1.0,
                                  bordermode="outside", x=-3, y=-3)
            # Lift the drop_frame to the top of the stacking order, making it visible and
            # interactive above the gradient label. This is a critical step.
            self.drop_frame.lift()

    def update_database_stats(self):
        """Update the database statistics display."""
        try:
            stats = self.db.get_database_stats()
            stats_text = f"Games: {stats['installed_appids']} installed | Depots: {stats['total_depots']} | With Keys: {stats['depots_with_keys']}"
            self.stats_label.configure(text=stats_text)
            print(f"[INFO] Database stats updated: {stats}")
        except Exception as e:
            self.stats_label.configure(text="Error loading database statistics")
            print(f"[ERROR] Failed to update database stats: {e}")

    def on_clear_database_click(self):
        """
        Clear all entries from the database and reset the application.
        """
        self.update_status("Clearing database...", "warning")
        
        try:
            # Get all installed AppIDs for cleanup
            installed_appids = self.db.get_all_installed_appids()
            
            if installed_appids:
                self.update_status(f"Uninstalling {len(installed_appids)} games...", "warning")
                
                # Uninstall all games
                for app_id in installed_appids:
                    try:
                        self.update_status(f"Uninstalling AppID {app_id}...", "info")
                        result = self.game_installer.uninstall_game(app_id)
                        if not result['success']:
                            print(f"[WARNING] Failed to fully uninstall AppID {app_id}: {result['errors']}")
                    except Exception as e:
                        print(f"[ERROR] Error uninstalling AppID {app_id}: {e}")
                
                self.update_status(f"Database cleared. {len(installed_appids)} games uninstalled.", "success")
            else:
                self.update_status("Database was already empty.", "info")
            
            # Update stats display
            self.update_database_stats()
            
        except Exception as e:
            self.update_status(f"Error clearing database: {e}", "error")
            print(f"[ERROR] Failed to clear database: {e}")

    def on_clear_data_click(self):
        """
        Handles the "Clear Data" button click.
        
        Deletes the config.ini and database files to reset the application
        to its initial state, then terminates the script.
        """
        self.update_status("Clearing all data and resetting application...", "warning")
        
        files_to_delete = ['config.ini', 'supersexyssteam.db']
        deleted_files = []
        
        for file_path in files_to_delete:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    deleted_files.append(file_path)
                    print(f"[INFO] Deleted {file_path}")
                except Exception as e:
                    print(f"[Error] Failed to delete {file_path}: {e}")
                    self.update_status(f"Error deleting {file_path}: {e}", "error")
                    return
        
        if deleted_files:
            print(f"[INFO] Successfully deleted: {', '.join(deleted_files)}")
        else:
            print("[INFO] No config files found to delete.")
        
        print("[INFO] Application data cleared. Terminating...")
        self.destroy()
        sys.exit(0)

    def update_status(self, message: str, level: str = "info"):
        """Provides colored feedback to the user via the status label at the bottom."""
        colors = {"info": Theme.TEXT_SECONDARY, "success": Theme.STATUS_SUCCESS,
                  "error": Theme.STATUS_ERROR, "warning": Theme.STATUS_WARNING}
        self.status_label.configure(text=message, text_color=colors.get(level, colors["info"]))
        print(f"[{level.upper()}] {message}")
        # Force GUI update to show status immediately
        self.update_idletasks()

    def on_drop(self, event):
        """
        The main logic handler for when files are dropped onto the drop zone.
        It validates input, organizes files, and immediately processes the game
        for installation or update.
        """
        self.update_status("Processing dropped files...")
        file_paths_str = re.findall(r'\{.*?\}|\S+', event.data)
        file_paths = [path.strip('{}') for path in file_paths_str]

        # Validate that exactly one .lua file was dropped.
        lua_files = [p for p in file_paths if p.lower().endswith('.lua')]
        if len(lua_files) != 1:
            msg = f"Error: {len(lua_files) if len(lua_files) > 1 else 'No'} .lua file{'s' if len(lua_files) > 1 else ''} dropped."
            self.update_status(f"{msg} Please drop exactly one.", "error")
            return

        # Extract AppID from the filename and validate it's a number.
        lua_path = lua_files[0]
        lua_filename = os.path.basename(lua_path)
        app_id = os.path.splitext(lua_filename)[0]
        if not app_id.isdigit():
            self.update_status(f"Invalid Lua filename: '{lua_filename}'. Name must be a numeric AppID.", "error")
            return

        # Prepare the destination directory.
        script_directory = os.path.dirname(os.path.abspath(__file__))
        destination_directory = os.path.join(script_directory, "data", app_id)

        # Check if this is an update or new installation
        is_update = self.db.is_appid_exists(app_id)
        
        if is_update:
            self.update_status(f"Updating existing AppID {app_id}...", "info")
            
            # First uninstall the existing game
            try:
                uninstall_result = self.game_installer.uninstall_game(app_id)
                if uninstall_result['success']:
                    print(f"[INFO] Successfully uninstalled existing AppID {app_id}")
                    stats = uninstall_result['stats']
                    self.update_status(f"Uninstalled AppID {app_id} ({stats['depots_removed']} depots removed)", "success")
                else:
                    self.update_status(f"Warning: Uninstallation had issues: {uninstall_result['errors']}", "warning")
                    print(f"[WARNING] Uninstall errors for AppID {app_id}: {uninstall_result['errors']}")
            except Exception as e:
                self.update_status(f"Error during uninstallation: {e}", "error")
                print(f"[ERROR] Failed to uninstall AppID {app_id}: {e}")
                return
        else:
            self.update_status(f"Installing new AppID {app_id}...", "info")

        # If a folder already exists, remove it to ensure a clean slate.
        if os.path.isdir(destination_directory):
            try:
                shutil.rmtree(destination_directory)
            except OSError as e:
                self.update_status(f"Error removing old folder: {e}", "error")
                return

        os.makedirs(destination_directory, exist_ok=True)

        # Copy all valid files to the destination.
        copied_files_count = 0
        for path in file_paths:
            if path.lower().endswith(('.lua', '.manifest')):
                try:
                    filename = os.path.basename(path)
                    shutil.copy2(path, os.path.join(destination_directory, filename))
                    copied_files_count += 1
                except Exception as e:
                    self.update_status(f"Error copying '{os.path.basename(path)}': {e}", "error")
                    shutil.rmtree(destination_directory, ignore_errors=True)  # Clean up on failure.
                    return

        # Now install the game using the new installer
        try:
            install_result = self.game_installer.install_game(app_id, destination_directory)
            
            if install_result['success']:
                action_verb = "Updated" if is_update else "Installed"
                stats = install_result['stats']
                success_msg = f"{action_verb} AppID {app_id} successfully! ({stats['depots_processed']} depots, {stats['manifests_copied']} manifests)"
                self.update_status(success_msg, "success")
                
                # Update database stats display
                self.update_database_stats()
                
                # Show any warnings
                if install_result['warnings']:
                    for warning in install_result['warnings']:
                        print(f"[WARNING] {warning}")
                
            else:
                # Installation failed, clean up
                self.update_status(f"Installation failed for AppID {app_id}: {install_result['errors']}", "error")
                for error in install_result['errors']:
                    print(f"[ERROR] {error}")
                
                # Clean up the data folder
                if os.path.exists(destination_directory):
                    shutil.rmtree(destination_directory, ignore_errors=True)
                
        except Exception as e:
            self.update_status(f"Unexpected error during installation: {e}", "error")
            print(f"[ERROR] Installation error for AppID {app_id}: {e}")
            
            # Clean up the data folder
            if os.path.exists(destination_directory):
                shutil.rmtree(destination_directory, ignore_errors=True)


# =============================================================================
# --- SCRIPT ENTRY POINT ---
# =============================================================================

if __name__ == "__main__":
    """
    The main execution block. It handles the initial configuration setup
    and launches the main application window.
    """
    config_file = 'config.ini'
    config = configparser.ConfigParser()

    # Check if the config file exists. If not, run the first-time setup.
    if not os.path.exists(config_file):
        setup_root = ctk.CTk()
        setup_root.withdraw()

        print("[INFO] config.ini not found. Starting first-time setup.")

        steam_dialog = PathEntryDialog(setup_root, "Steam Path Setup", "Please enter your Steam installation directory.", "Leave empty for C:\\Program Files (x86)\\Steam")
        steam_path = steam_dialog.get_input()
        if steam_path is None: sys.exit()
        if steam_path == "": steam_path = "C:\\Program Files (x86)\\Steam"

        gl_dialog = PathEntryDialog(setup_root, "GreenLuma Path Setup", "Please enter your GreenLuma directory.", "Leave empty for default (script's folder)")
        gl_path = gl_dialog.get_input()
        if gl_path is None: sys.exit()
        if gl_path == "":
            base_dir = os.path.dirname(os.path.abspath(__file__))
            gl_path = os.path.join(base_dir, "GreenLuma")
            os.makedirs(gl_path, exist_ok=True)

        config['Paths'] = {'steam_path': steam_path, 'greenluma_path': gl_path}
        
        # Add default debug setting (False = console hidden for end users)
        config['Debug'] = {'show_console': 'False'}
        
        with open(config_file, 'w') as f:
            config.write(f)
        
        # Configure the GreenLuma DLLInjector.ini with the paths
        configure_greenluma_injector(steam_path, gl_path)
        
        setup_root.destroy()

    # Load the config and launch the main application.
    config.read(config_file)
    
    # Handle console window visibility based on debug setting
    debug_mode = config.getboolean('Debug', 'show_console', fallback=False)
    if not debug_mode and sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except Exception:
            pass  # Silently ignore if hiding console fails
    
    app = App(config)
    app.mainloop()

# Docs are generated by AI and may be inaccurate