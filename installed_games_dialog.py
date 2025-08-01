# installed_games_dialog.py
#
# Modern installed games dialog for SuperSexySteam using PySide6

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QWidget, QFrame, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QIcon
from pathlib import Path

from SuperSexySteam_PySide6 import Theme, AnimatedButton, GradientFrame


class LoadGamesWorker(QThread):
    """Worker thread for loading installed games"""
    
    games_loaded = Signal(dict)
    
    def __init__(self, logic):
        super().__init__()
        self.logic = logic
        
    def run(self):
        """Load installed games"""
        result = self.logic.get_installed_games()
        self.games_loaded.emit(result)


class UninstallWorker(QThread):
    """Worker thread for uninstalling games"""
    
    uninstall_completed = Signal(dict)
    
    def __init__(self, logic, app_id):
        super().__init__()
        self.logic = logic
        self.app_id = app_id
        
    def run(self):
        """Uninstall game"""
        result = self.logic.uninstall_game(self.app_id)
        self.uninstall_completed.emit(result)


class InstalledGameWidget(GradientFrame):
    """Widget to display a single installed game"""
    
    uninstall_requested = Signal(str, str)  # app_id, game_name
    
    def __init__(self, game_data, parent=None):
        super().__init__(parent, [Theme.SURFACE_DARK, Theme.TERTIARY_DARK])
        self.game_data = game_data
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(12)
        
        # Top row: Game name
        name_label = QLabel(self.game_data['game_name'])
        name_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_PRIMARY};
                font-size: 18px;
                font-weight: bold;
            }}
        """)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
        # Bottom row: AppID and uninstall button
        bottom_layout = QHBoxLayout()
        
        # AppID
        appid_label = QLabel(f"AppID: {self.game_data['app_id']}")
        appid_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_SECONDARY};
                font-size: 14px;
            }}
        """)
        bottom_layout.addWidget(appid_label)
        
        bottom_layout.addStretch()
        
        # Uninstall button
        uninstall_button = AnimatedButton("Uninstall")
        uninstall_button.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.ACCENT_RED};
                color: {Theme.TEXT_PRIMARY};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background: #f44336;
            }}
            QPushButton:pressed {{
                background: #d32f2f;
            }}
        """)
        uninstall_button.clicked.connect(self.request_uninstall)
        bottom_layout.addWidget(uninstall_button)
        
        layout.addLayout(bottom_layout)
        
    def request_uninstall(self):
        """Request uninstallation of this game"""
        self.uninstall_requested.emit(
            str(self.game_data['app_id']), 
            self.game_data['game_name']
        )


class InstalledGamesDialog(QDialog):
    """Modern installed games dialog"""
    
    def __init__(self, logic, parent=None):
        super().__init__(parent)
        self.logic = logic
        self.load_worker = None
        self.uninstall_worker = None
        self.setup_ui()
        self.setup_window()
        self.load_games()
        
    def setup_window(self):
        """Setup dialog window properties"""
        self.setWindowTitle("Installed Games")
        self.setModal(True)
        self.resize(800, 700)
        
        # Set window icon
        try:
            icon_path = Path(__file__).parent / "sss.ico"
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
        except Exception:
            pass
            
        # Apply dark theme
        self.setStyleSheet(f"""
            QDialog {{
                background: {Theme.MAIN_GRADIENT};
                color: {Theme.TEXT_PRIMARY};
            }}
        """)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Installed Games")
        title.setStyleSheet(f"""
            QLabel {{
                color: {Theme.GOLD_PRIMARY};
                font-size: 28px;
                font-weight: bold;
            }}
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Status and refresh button
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("Loading installed games...")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_SECONDARY};
                font-size: 14px;
            }}
        """)
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        self.refresh_button = AnimatedButton("Refresh")
        self.refresh_button.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.BLUE_GRADIENT};
                color: {Theme.TEXT_PRIMARY};
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Theme.ACCENT_BLUE}, stop:1 #0099cc);
            }}
        """)
        self.refresh_button.clicked.connect(self.load_games)
        status_layout.addWidget(self.refresh_button)
        
        layout.addLayout(status_layout)
        
        # Games area
        games_frame = GradientFrame()
        games_layout = QVBoxLayout(games_frame)
        games_layout.setContentsMargins(10, 10, 10, 10)
        
        # Scrollable games area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: {Theme.SURFACE_DARK};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: {Theme.GOLD_PRIMARY};
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {Theme.GOLD_SECONDARY};
            }}
        """)
        
        self.games_widget = QWidget()
        self.games_layout = QVBoxLayout(self.games_widget)
        self.games_layout.setSpacing(10)
        self.games_layout.setContentsMargins(5, 5, 5, 5)
        
        # Initial loading state
        self.show_loading_state()
        
        self.scroll_area.setWidget(self.games_widget)
        games_layout.addWidget(self.scroll_area)
        
        layout.addWidget(games_frame, 1)
        
        # Close button
        close_button = AnimatedButton("✖ Close")
        close_button.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.ACCENT_RED};
                color: {Theme.TEXT_PRIMARY};
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: #f44336;
            }}
            QPushButton:pressed {{
                background: #d32f2f;
            }}
        """)
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
    def show_loading_state(self):
        """Show loading state in games area"""
        self.clear_games()
        
        loading_label = QLabel("⏳\n\nLoading installed games...")
        loading_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.ACCENT_BLUE};
                font-size: 16px;
                padding: 40px;
            }}
        """)
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.games_layout.addWidget(loading_label)
        
    def show_empty_state(self):
        """Show empty state when no games are installed"""
        self.clear_games()
        
        empty_label = QLabel("🎮\n\nNo games installed\n\nInstall some games first!")
        empty_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_MUTED};
                font-size: 16px;
                padding: 40px;
            }}
        """)
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.games_layout.addWidget(empty_label)
        
    def show_error_state(self, error_message):
        """Show error state"""
        self.clear_games()
        
        error_label = QLabel(f"❌\n\nError loading games:\n{error_message}")
        error_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.ACCENT_RED};
                font-size: 16px;
                padding: 40px;
            }}
        """)
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.games_layout.addWidget(error_label)
        
    def clear_games(self):
        """Clear all games from the layout"""
        while self.games_layout.count():
            child = self.games_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
    def load_games(self):
        """Load installed games"""
        self.show_loading_state()
        self.status_label.setText("Loading installed games...")
        self.status_label.setStyleSheet(f"color: {Theme.ACCENT_BLUE}; font-size: 14px;")
        
        # Disable refresh button
        self.refresh_button.setEnabled(False)
        self.refresh_button.setText("⏳ Loading...")
        
        # Start loading in worker thread
        self.load_worker = LoadGamesWorker(self.logic)
        self.load_worker.games_loaded.connect(self.on_games_loaded)
        self.load_worker.start()
        
    def on_games_loaded(self, result):
        """Handle games loading completion"""
        # Re-enable refresh button
        self.refresh_button.setEnabled(True)
        self.refresh_button.setText("🔄 Refresh")
        
        if not result['success']:
            self.status_label.setText(f"Error loading games: {result['error']}")
            self.status_label.setStyleSheet(f"color: {Theme.ACCENT_RED}; font-size: 14px;")
            self.show_error_state(result['error'])
            return
            
        games = result['games']
        
        if not games:
            self.status_label.setText("No games installed")
            self.status_label.setStyleSheet(f"color: {Theme.ACCENT_ORANGE}; font-size: 14px;")
            self.show_empty_state()
            return
            
        # Show games
        self.status_label.setText(f"Found {len(games)} installed games")
        self.status_label.setStyleSheet(f"color: {Theme.ACCENT_GREEN}; font-size: 14px;")
        
        self.clear_games()
        
        for game in games:
            game_widget = InstalledGameWidget(game)
            game_widget.uninstall_requested.connect(self.uninstall_game)
            self.games_layout.addWidget(game_widget)
            
        # Add stretch at the end
        self.games_layout.addStretch()
        
    def uninstall_game(self, app_id, game_name):
        """Uninstall a specific game"""
        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Confirm Uninstall",
            f"Are you sure you want to uninstall '{game_name}' (AppID: {app_id})?\n\n"
            "This will remove all related files and data.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        # Start uninstallation
        self.status_label.setText(f"Uninstalling {game_name}...")
        self.status_label.setStyleSheet(f"color: {Theme.ACCENT_ORANGE}; font-size: 14px;")
        
        # Disable refresh button during uninstall
        self.refresh_button.setEnabled(False)
        self.refresh_button.setText("⏳ Uninstalling...")
        
        # Start uninstall in worker thread
        self.uninstall_worker = UninstallWorker(self.logic, app_id)
        self.uninstall_worker.uninstall_completed.connect(
            lambda result: self.on_uninstall_completed(result, game_name)
        )
        self.uninstall_worker.start()
        
    def on_uninstall_completed(self, result, game_name):
        """Handle uninstall completion"""
        # Re-enable refresh button
        self.refresh_button.setEnabled(True)
        self.refresh_button.setText("🔄 Refresh")
        
        if result['success']:
            self.status_label.setText(f"Successfully uninstalled {game_name}")
            self.status_label.setStyleSheet(f"color: {Theme.ACCENT_GREEN}; font-size: 14px;")
            
            # Reload games list
            QTimer.singleShot(1000, self.load_games)
        else:
            self.status_label.setText(f"Failed to uninstall {game_name}: {result['error']}")
            self.status_label.setStyleSheet(f"color: {Theme.ACCENT_RED}; font-size: 14px;")
