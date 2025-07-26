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
# 3. All business logic is handled by the app_logic module.
# 4. GUI only calls app_logic functions and displays the results.
#
# Dependencies:
# - customtkinter: For the modern UI widgets.
# - tkinterdnd2: To enable drag-and-drop functionality.
# - Pillow (PIL): For dynamic image manipulation (header resizing and gradients).
# - app_logic: The central brain module for all business operations.

import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD
from pathlib import Path
import re
from PIL import Image, ImageDraw
import sys

# Import our central brain module
from app_logic import SuperSexySteamLogic


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

    This class is focused only on GUI display and user interaction.
    All business logic is handled by the SuperSexySteamLogic class from app_logic.py.
    """
    def __init__(self, logic: SuperSexySteamLogic):
        """
        Initializes the main application window and all its components.

        Args:
            logic (SuperSexySteamLogic): The initialized logic controller
        """
        super().__init__()
        self.logic = logic

        # --- Window Configuration ---
        # The root window is a standard Tk object, so it uses 'background' for its color.
        self.configure(background=Theme.BG_DARK)
        self.title("SuperSexySteam")
        self.geometry("600x750")  # Made taller to accommodate database stats
        self.minsize(550, 700)
        
        # --- Window Icon ---
        try:
            icon_path = Path(__file__).parent / "icon.ico"
            if icon_path.exists():
                self.wm_iconbitmap(str(icon_path))
        except Exception as e:
            print(f"[WARNING] Failed to load window icon: {e}")

        # --- Header Image ---
        try:
            header_path = Path(__file__).parent / "header.png"
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

        # --- Run Steam Button (Large and Prominent) ---
        self.run_steam_button = ctk.CTkButton(self.buttons_frame, text="🚀 RUN STEAM", font=("Segoe UI", 18, "bold"), 
                                             text_color=Theme.BG_DARK, fg_color=Theme.GOLD, hover_color=Theme.DARK_GOLD, 
                                             border_width=0, corner_radius=12, command=self.on_run_steam_click, 
                                             width=200, height=50)
        self.run_steam_button.pack(side="top", pady=(0, 15))

        # --- Secondary Buttons Frame ---
        self.secondary_buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.secondary_buttons_frame.pack(pady=(0, 0), padx=20, fill="x")

        # --- Refresh Stats Button ---
        self.refresh_button = ctk.CTkButton(self.secondary_buttons_frame, text="Refresh Stats", font=Theme.FONT_PRIMARY, text_color=Theme.BG_DARK,
                                           fg_color=Theme.STATUS_SUCCESS, hover_color="#4caf50", border_width=0,
                                           corner_radius=8, command=self.update_database_stats, width=120)
        self.refresh_button.pack(side="left", padx=(0, 10))

        # --- Clear Data Button ---
        self.clear_data_button = ctk.CTkButton(self.secondary_buttons_frame, text="Clear Data", font=Theme.FONT_PRIMARY, text_color=Theme.TEXT_PRIMARY,
                                              fg_color=Theme.STATUS_ERROR, hover_color="#c62828", border_width=0,
                                              corner_radius=8, command=self.on_clear_data_click, width=120)
        self.clear_data_button.pack(side="left", padx=(0, 10))

        # --- Uninstall Button ---
        self.uninstall_button = ctk.CTkButton(self.secondary_buttons_frame, text="Uninstall AppID", font=Theme.FONT_PRIMARY, text_color=Theme.TEXT_PRIMARY,
                                             fg_color=Theme.STATUS_WARNING, hover_color="#ff9800", border_width=0,
                                             corner_radius=8, command=self.on_uninstall_click, width=120)
        self.uninstall_button.pack(side="left", padx=(0, 10))

        # --- Steam Search Button ---
        self.search_button = ctk.CTkButton(self.secondary_buttons_frame, text="🔍 Game Search", font=Theme.FONT_PRIMARY, text_color=Theme.TEXT_PRIMARY,
                                          fg_color="#2196f3", hover_color="#1976d2", border_width=0,
                                          corner_radius=8, command=self.on_search_click, width=120)
        self.search_button.pack(side="left", padx=(0, 10))

        # --- Installed Games Button ---
        self.installed_games_button = ctk.CTkButton(self.secondary_buttons_frame, text="📋 Installed Games", font=Theme.FONT_PRIMARY, text_color=Theme.TEXT_PRIMARY,
                                                   fg_color="#4caf50", hover_color="#388e3c", border_width=0,
                                                   command=self.on_installed_games_click, width=130)
        self.installed_games_button.pack(side="left", padx=(0, 10))

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
        """Update the database statistics display using app logic."""
        stats_result = self.logic.get_database_stats()
        if stats_result['success']:
            self.stats_label.configure(text=stats_result['formatted_text'])
        else:
            self.stats_label.configure(text=stats_result['formatted_text'])

    def update_status(self, message: str, level: str = "info"):
        """Provides colored feedback to the user via the status label at the bottom."""
        colors = {"info": Theme.TEXT_SECONDARY, "success": Theme.STATUS_SUCCESS,
                  "error": Theme.STATUS_ERROR, "warning": Theme.STATUS_WARNING}
        self.status_label.configure(text=message, text_color=colors.get(level, colors["info"]))
        # Force GUI update to show status immediately
        self.update_idletasks()

    # =============================================================================
    # --- EVENT HANDLERS ---
    # =============================================================================

    def on_drop(self, event):
        """
        Handle file drop events by delegating to app logic.
        """
        self.update_status("Processing dropped files...")
        
        # Parse dropped file paths
        file_paths_str = re.findall(r'\{.*?\}|\S+', event.data)
        file_paths = [path.strip('{}') for path in file_paths_str]
        
        # Delegate to app logic
        result = self.logic.process_game_installation(file_paths)
        
        if result['success']:
            action_verb = result['action_verb']
            app_id = result['app_id']
            stats = result['stats']
            success_msg = f"{action_verb} AppID {app_id} successfully! ({stats['depots_processed']} depots, {stats['manifests_copied']} manifests)"
            self.update_status(success_msg, "success")
            
            # Update database stats display
            self.update_database_stats()
            
            # Show any warnings
            if result['warnings']:
                for warning in result['warnings']:
                    print(f"[WARNING] {warning}")
        else:
            error_msg = result.get('error', 'Installation failed')
            if 'errors' in result and result['errors']:
                error_msg = '; '.join(result['errors'])
            
            self.update_status(f"Installation failed: {error_msg}", "error")

    def on_clear_data_click(self):
        """Handle clear data button click using app logic."""
        self.update_status("Starting comprehensive data cleanup...", "warning")
        
        result = self.logic.clear_all_application_data()
        
        if result['success']:
            self.update_status(f"Data cleanup completed! {result['summary']}", "success")
            
            if result['warnings']:
                for warning in result['warnings']:
                    print(f"[WARNING] {warning}")
            
            # Update stats display
            self.update_database_stats()
        else:
            self.update_status(f"Data cleanup failed: {result['error']}", "error")

    def on_uninstall_click(self):
        """Handle uninstall button click using app logic."""
        # Create input dialog
        dialog = ctk.CTkInputDialog(text="Enter AppID to uninstall:", title="Uninstall Game")
        app_id = dialog.get_input()
        
        if app_id is None or app_id.strip() == "":
            return  # User cancelled or entered empty string
        
        self.update_status(f"Uninstalling AppID {app_id.strip()}...", "warning")
        
        result = self.logic.uninstall_game(app_id)
        
        if result['success']:
            self.update_status(f"AppID {result['app_id']} uninstalled! {result['summary']}", "success")
            
            if result['warnings']:
                for warning in result['warnings']:
                    print(f"[WARNING] {warning}")
            
            # Update stats display
            self.update_database_stats()
        else:
            self.update_status(f"Uninstallation failed: {result['error']}", "error")

    def on_run_steam_click(self):
        """Handle run Steam button click using app logic."""
        self.update_status("Preparing to launch Steam...", "info")
        
        result = self.logic.launch_steam()
        
        if result['success']:
            # Show all messages
            for message in result['messages']:
                print(f"[INFO] {message}")
            
            # Show final success message
            final_message = result['messages'][-1] if result['messages'] else "Steam launched successfully! 🚀"
            self.update_status(final_message, "success")
            
            # Show warnings if any
            if result['warnings']:
                for warning in result['warnings']:
                    print(f"[WARNING] {warning}")
        else:
            # Show error
            if result['errors']:
                error_msg = '; '.join(result['errors'])
                self.update_status(f"Failed to launch Steam: {error_msg}", "error")
            else:
                self.update_status("Failed to launch Steam", "error")

    def on_search_click(self):
        """Handle game search button click."""
        self.open_search_window()

    def on_installed_games_click(self):
        """Handle installed games button click."""
        self.open_installed_games_window()

    # =============================================================================
    # --- SEARCH WINDOW ---
    # =============================================================================

    def open_search_window(self):
        """Open the Steam Game Search window."""
        # Create a new window for game search
        search_window = ctk.CTkToplevel(self)
        search_window.title("Steam Game Search")
        search_window.geometry("700x600")
        search_window.configure(fg_color=Theme.BG_DARK)
        
        # Make the window stay on top
        search_window.transient(self)
        search_window.grab_set()
        
        # Try to set icon
        try:
            icon_path = Path(__file__).parent / "icon.ico"
            if icon_path.exists():
                search_window.wm_iconbitmap(str(icon_path))
        except Exception:
            pass
        
        # Title
        title_label = ctk.CTkLabel(search_window, text="🔍 Steam Game Search", 
                                  font=("Segoe UI", 24, "bold"), text_color=Theme.GOLD)
        title_label.pack(pady=(20, 10))
        
        # Search frame
        search_frame = ctk.CTkFrame(search_window, fg_color=Theme.BG_LIGHT, corner_radius=10)
        search_frame.pack(padx=20, pady=10, fill="x")
        
        # Search label
        search_label = ctk.CTkLabel(search_frame, text="Enter game name:", 
                                   font=Theme.FONT_PRIMARY, text_color=Theme.TEXT_PRIMARY)
        search_label.pack(pady=(15, 5))
        
        # Search entry
        search_entry = ctk.CTkEntry(search_frame, placeholder_text="e.g., Counter-Strike 2, Portal, Half-Life...", 
                                   font=Theme.FONT_PRIMARY, width=400, height=35)
        search_entry.pack(pady=(0, 10))
        
        # Search button
        search_btn = ctk.CTkButton(search_frame, text="🔍 Search Games", 
                                  font=Theme.FONT_PRIMARY, text_color=Theme.BG_DARK,
                                  fg_color=Theme.GOLD, hover_color=Theme.DARK_GOLD,
                                  command=lambda: self.perform_search(search_entry.get(), results_frame, status_search))
        search_btn.pack(pady=(0, 15))
        
        # Status label for search
        status_search = ctk.CTkLabel(search_window, text="Enter a game name and click search", 
                                    font=Theme.FONT_PRIMARY, text_color=Theme.TEXT_SECONDARY)
        status_search.pack(pady=5)
        
        # Results frame with scrollbar
        results_container = ctk.CTkFrame(search_window, fg_color=Theme.BG_LIGHT, corner_radius=10)
        results_container.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Results title
        results_title = ctk.CTkLabel(results_container, text="Search Results", 
                                    font=Theme.FONT_LARGE_BOLD, text_color=Theme.GOLD)
        results_title.pack(pady=(10, 5))
        
        # Scrollable frame for results
        results_frame = ctk.CTkScrollableFrame(results_container, fg_color="transparent")
        results_frame.pack(padx=10, pady=(0, 10), fill="both", expand=True)
        
        # Bind Enter key to search
        search_entry.bind("<Return>", lambda e: self.perform_search(search_entry.get(), results_frame, status_search))
        
        # Focus on the search entry
        search_entry.focus()

    def perform_search(self, query, results_frame, status_label):
        """
        Perform the actual Steam game search and display results.
        
        Args:
            query (str): The search query entered by the user
            results_frame: The scrollable frame to display results in
            status_label: The status label to update with search progress
        """
        if not query or not query.strip():
            status_label.configure(text="Please enter a game name to search", text_color=Theme.STATUS_ERROR)
            return
        
        # Clear previous results
        for widget in results_frame.winfo_children():
            widget.destroy()
        
        # Update status
        status_label.configure(text=f"Searching for '{query}'...", text_color=Theme.TEXT_SECONDARY)
        results_frame.update_idletasks()
        
        # Perform search using app logic
        result = self.logic.search_steam_games(query, max_results=20)
        
        if not result['success']:
            status_label.configure(text=f"Error searching: {result['error']}", text_color=Theme.STATUS_ERROR)
            return
        
        games = result['games']
        
        if not games:
            status_label.configure(text=f"No games found for '{query}'", text_color=Theme.STATUS_WARNING)
            no_results_label = ctk.CTkLabel(results_frame, text="No games found. Try a different search term.", 
                                           font=Theme.FONT_PRIMARY, text_color=Theme.TEXT_SECONDARY)
            no_results_label.pack(pady=20)
            return
        
        # Update status with results count
        status_label.configure(text=f"Found {len(games)} games for '{query}'", text_color=Theme.STATUS_SUCCESS)
        
        # Display results
        for i, game in enumerate(games, 1):
            # Create a frame for each game result
            game_frame = ctk.CTkFrame(results_frame, fg_color=Theme.BG_DARK, corner_radius=8)
            game_frame.pack(fill="x", padx=5, pady=5)
            
            # Game info frame
            info_frame = ctk.CTkFrame(game_frame, fg_color="transparent")
            info_frame.pack(fill="x", padx=10, pady=10)
            
            # Game number and name
            name_label = ctk.CTkLabel(info_frame, text=f"{i}. {game['name']}", 
                                     font=("Segoe UI", 14, "bold"), text_color=Theme.TEXT_PRIMARY, anchor="w")
            name_label.pack(fill="x")
            
            # AppID and type
            details_text = f"AppID: {game['appid']} | Type: {game['type']}"
            details_label = ctk.CTkLabel(info_frame, text=details_text, 
                                       font=Theme.FONT_PRIMARY, text_color=Theme.TEXT_SECONDARY, anchor="w")
            details_label.pack(fill="x")
            
            # Copy AppID button
            copy_btn = ctk.CTkButton(info_frame, text=f"📋 Copy AppID ({game['appid']})", 
                                    font=("Segoe UI", 11), width=150, height=25,
                                    fg_color=Theme.STATUS_SUCCESS, hover_color="#4caf50",
                                    command=lambda aid=game['appid']: self.copy_appid_to_clipboard(aid, status_label))
            copy_btn.pack(pady=(5, 0), anchor="w")

    def copy_appid_to_clipboard(self, appid, status_label):
        """
        Copy the AppID to clipboard and show feedback.
        
        Args:
            appid: The AppID to copy
            status_label: Status label to show feedback
        """
        try:
            self.clipboard_clear()
            self.clipboard_append(str(appid))
            status_label.configure(text=f"AppID {appid} copied to clipboard!", text_color=Theme.STATUS_SUCCESS)
            print(f"[INFO] AppID {appid} copied to clipboard")
        except Exception as e:
            status_label.configure(text=f"Failed to copy AppID: {str(e)}", text_color=Theme.STATUS_ERROR)
            print(f"[ERROR] Failed to copy AppID {appid}: {e}")

    # =============================================================================
    # --- INSTALLED GAMES WINDOW ---
    # =============================================================================

    def open_installed_games_window(self):
        """
        Open the Installed Games window showing all installed games.
        """
        # Create a new window for installed games
        games_window = ctk.CTkToplevel(self)
        games_window.title("Installed Games")
        games_window.geometry("800x700")
        games_window.configure(fg_color=Theme.BG_DARK)
        
        # Make the window stay on top
        games_window.transient(self)
        games_window.grab_set()
        
        # Try to set icon
        try:
            icon_path = Path(__file__).parent / "icon.ico"
            if icon_path.exists():
                games_window.wm_iconbitmap(str(icon_path))
        except Exception:
            pass
        
        # Title
        title_label = ctk.CTkLabel(games_window, text="📋 Installed Games", 
                                  font=("Segoe UI", 24, "bold"), text_color=Theme.GOLD)
        title_label.pack(pady=(20, 10))
        
        # Status label for this window
        status_games = ctk.CTkLabel(games_window, text="Loading installed games...", 
                                   font=Theme.FONT_PRIMARY, text_color=Theme.TEXT_SECONDARY)
        status_games.pack(pady=5)
        
        # Refresh button
        refresh_frame = ctk.CTkFrame(games_window, fg_color="transparent")
        refresh_frame.pack(pady=10)
        
        refresh_btn = ctk.CTkButton(refresh_frame, text="🔄 Refresh List", 
                                   font=Theme.FONT_PRIMARY, text_color=Theme.BG_DARK,
                                   fg_color=Theme.GOLD, hover_color=Theme.DARK_GOLD,
                                   command=lambda: self.refresh_installed_games(games_frame, status_games))
        refresh_btn.pack()
        
        # Games list frame with scrollbar
        games_container = ctk.CTkFrame(games_window, fg_color=Theme.BG_LIGHT, corner_radius=10)
        games_container.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Scrollable frame for games
        games_frame = ctk.CTkScrollableFrame(games_container, fg_color="transparent")
        games_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Load the games initially
        self.refresh_installed_games(games_frame, status_games)

    def refresh_installed_games(self, games_frame, status_label):
        """
        Refresh the list of installed games in the window.
        
        Args:
            games_frame: The scrollable frame to display games in
            status_label: The status label to update with progress
        """
        # Clear previous games
        for widget in games_frame.winfo_children():
            widget.destroy()
        
        # Update status
        status_label.configure(text="Loading installed games...", text_color=Theme.TEXT_SECONDARY)
        games_frame.update_idletasks()
        
        # Get games using app logic
        result = self.logic.get_installed_games()
        
        if not result['success']:
            status_label.configure(text=f"Error loading games: {result['error']}", text_color=Theme.STATUS_ERROR)
            return
        
        games = result['games']
        
        if not games:
            status_label.configure(text="No games installed", text_color=Theme.STATUS_WARNING)
            no_games_label = ctk.CTkLabel(games_frame, text="No games found. Install some games first!", 
                                         font=Theme.FONT_PRIMARY, text_color=Theme.TEXT_SECONDARY)
            no_games_label.pack(pady=30)
            return
        
        # Update status with games count
        status_label.configure(text=f"Found {len(games)} installed games", text_color=Theme.STATUS_SUCCESS)
        
        # Display games
        for i, game in enumerate(games, 1):
            # Create a frame for each game
            game_frame = ctk.CTkFrame(games_frame, fg_color=Theme.BG_DARK, corner_radius=8)
            game_frame.pack(fill="x", padx=5, pady=5)
            
            # Game info frame
            info_frame = ctk.CTkFrame(game_frame, fg_color="transparent")
            info_frame.pack(fill="x", padx=15, pady=15)
            
            # Top row: Game number and name
            top_row = ctk.CTkFrame(info_frame, fg_color="transparent")
            top_row.pack(fill="x")
            
            name_label = ctk.CTkLabel(top_row, text=f"{i}. {game['game_name']}", 
                                     font=("Segoe UI", 16, "bold"), text_color=Theme.TEXT_PRIMARY, anchor="w")
            name_label.pack(side="left", fill="x", expand=True)
            
            # Bottom row: AppID and uninstall button
            bottom_row = ctk.CTkFrame(info_frame, fg_color="transparent")
            bottom_row.pack(fill="x", pady=(10, 0))
            
            appid_label = ctk.CTkLabel(bottom_row, text=f"AppID: {game['app_id']}", 
                                      font=Theme.FONT_PRIMARY, text_color=Theme.TEXT_SECONDARY, anchor="w")
            appid_label.pack(side="left")
            
            # Uninstall button
            uninstall_btn = ctk.CTkButton(bottom_row, text="🗑️ Uninstall", 
                                         font=("Segoe UI", 12), width=100, height=30,
                                         fg_color=Theme.STATUS_ERROR, hover_color="#d32f2f",
                                         command=lambda aid=game['app_id'], name=game['game_name']: 
                                         self.uninstall_game_from_list(aid, name, games_frame, status_label))
            uninstall_btn.pack(side="right", padx=(10, 0))

    def uninstall_game_from_list(self, app_id, game_name, games_frame, status_label):
        """
        Uninstall a specific game from the installed games list.
        
        Args:
            app_id (str): The AppID of the game to uninstall
            game_name (str): The name of the game
            games_frame: The games frame to refresh after uninstallation
            status_label: The status label to update with progress
        """
        # Show confirmation dialog
        from tkinter import messagebox
        
        result = messagebox.askyesno(
            "Confirm Uninstall", 
            f"Are you sure you want to uninstall '{game_name}' (AppID: {app_id})?\n\n"
            "This will remove all related files and data.",
            icon="warning"
        )
        
        if not result:
            return
        
        status_label.configure(text=f"Uninstalling {game_name}...", text_color=Theme.STATUS_WARNING)
        
        # Use app logic for uninstallation
        uninstall_result = self.logic.uninstall_game(app_id)
        
        if uninstall_result['success']:
            status_label.configure(text=f"Successfully uninstalled {game_name}", text_color=Theme.STATUS_SUCCESS)
            # Refresh the main app database stats
            self.update_database_stats()
            # Refresh the games list
            self.refresh_installed_games(games_frame, status_label)
        else:
            status_label.configure(text=f"Failed to uninstall {game_name}: {uninstall_result['error']}", text_color=Theme.STATUS_ERROR)


# =============================================================================
# --- SCRIPT ENTRY POINT ---
# =============================================================================

if __name__ == "__main__":
    """
    The main execution block. It handles the initial configuration setup
    and launches the main application window.
    """
    # Load or setup configuration using app logic
    config = SuperSexySteamLogic.load_configuration()
    if config is None:
        sys.exit("Setup cancelled or failed")
    
    # Initialize the logic controller
    logic = SuperSexySteamLogic(config)
    
    # Launch the GUI with the logic controller
    app = App(logic)
    app.mainloop()