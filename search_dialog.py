# search_dialog.py
#
# Modern search dialog for SuperSexySteam using PySide6

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QScrollArea, QWidget, QFrame, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QClipboard, QIcon
from pathlib import Path

from SuperSexySteam_PySide6 import Theme, AnimatedButton, GradientFrame


class SearchWorker(QThread):
    """Worker thread for performing Steam game searches"""
    
    search_completed = Signal(dict)
    
    def __init__(self, logic, query, max_results=20):
        super().__init__()
        self.logic = logic
        self.query = query
        self.max_results = max_results
        
    def run(self):
        """Perform the search"""
        result = self.logic.search_steam_games(self.query, self.max_results)
        self.search_completed.emit(result)


class GameResultWidget(GradientFrame):
    """Widget to display a single game search result"""
    
    appid_copied = Signal(str)
    
    def __init__(self, game_data, parent=None):
        super().__init__(parent, [Theme.SURFACE_DARK, Theme.TERTIARY_DARK])
        self.game_data = game_data
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        
        # Game name
        name_label = QLabel(self.game_data['name'])
        name_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_PRIMARY};
                font-size: 16px;
                font-weight: bold;
            }}
        """)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
        # Game details
        details_layout = QHBoxLayout()
        
        # AppID
        appid_label = QLabel(f"AppID: {self.game_data['appid']}")
        appid_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_SECONDARY};
                font-size: 14px;
            }}
        """)
        details_layout.addWidget(appid_label)
        
        # Type
        type_label = QLabel(f"Type: {self.game_data.get('type', 'Unknown')}")
        type_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_SECONDARY};
                font-size: 14px;
            }}
        """)
        details_layout.addWidget(type_label)
        
        details_layout.addStretch()
        
        # Copy button
        copy_button = AnimatedButton(f"Copy AppID")
        copy_button.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.ACCENT_GREEN};
                color: {Theme.TEXT_PRIMARY};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background: #4caf50;
            }}
            QPushButton:pressed {{
                background: #388e3c;
            }}
        """)
        copy_button.clicked.connect(self.copy_appid)
        details_layout.addWidget(copy_button)
        
        layout.addLayout(details_layout)
        
    def copy_appid(self):
        """Copy AppID to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(str(self.game_data['appid']))
        self.appid_copied.emit(str(self.game_data['appid']))


class SearchDialog(QDialog):
    """Modern Steam game search dialog"""
    
    def __init__(self, logic, parent=None):
        super().__init__(parent)
        self.logic = logic
        self.search_worker = None
        self.setup_ui()
        self.setup_window()
        
    def setup_window(self):
        """Setup dialog window properties"""
        self.setWindowTitle("Steam Game Search")
        self.setModal(True)
        self.resize(700, 600)
        
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
        title = QLabel("Steam Game Search")
        title.setStyleSheet(f"""
            QLabel {{
                color: {Theme.GOLD_PRIMARY};
                font-size: 28px;
                font-weight: bold;
            }}
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Search input frame
        search_frame = GradientFrame()
        search_layout = QVBoxLayout(search_frame)
        search_layout.setContentsMargins(25, 25, 25, 25)
        search_layout.setSpacing(15)
        
        # Search label
        search_label = QLabel("Enter game name:")
        search_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_PRIMARY};
                font-size: 16px;
                font-weight: bold;
            }}
        """)
        search_layout.addWidget(search_label)
        
        # Search input and button
        input_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("e.g., Counter-Strike 2, Portal, Half-Life...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {Theme.SURFACE_DARK};
                color: {Theme.TEXT_PRIMARY};
                border: 2px solid transparent;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                min-height: 20px;
            }}
            QLineEdit:focus {{
                border: 2px solid {Theme.GOLD_PRIMARY};
                background: {Theme.TERTIARY_DARK};
            }}
            QLineEdit:hover {{
                border: 2px solid {Theme.GOLD_SECONDARY};
            }}
        """)
        self.search_input.returnPressed.connect(self.perform_search)
        input_layout.addWidget(self.search_input, 1)
        
        self.search_button = AnimatedButton("Search")
        self.search_button.clicked.connect(self.perform_search)
        input_layout.addWidget(self.search_button)
        
        search_layout.addLayout(input_layout)
        layout.addWidget(search_frame)
        
        # Status label
        self.status_label = QLabel("Enter a game name and click search")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_SECONDARY};
                font-size: 14px;
            }}
        """)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Results area
        results_frame = GradientFrame()
        results_layout = QVBoxLayout(results_frame)
        results_layout.setContentsMargins(10, 10, 10, 10)
        
        # Results title
        results_title = QLabel("Search Results")
        results_title.setStyleSheet(f"""
            QLabel {{
                color: {Theme.GOLD_PRIMARY};
                font-size: 18px;
                font-weight: bold;
                padding: 10px;
            }}
        """)
        results_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        results_layout.addWidget(results_title)
        
        # Scrollable results area
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
        
        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_layout.setSpacing(10)
        self.results_layout.setContentsMargins(5, 5, 5, 5)
        
        # Initial empty state
        self.show_empty_state()
        
        self.scroll_area.setWidget(self.results_widget)
        results_layout.addWidget(self.scroll_area)
        
        layout.addWidget(results_frame, 1)
        
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
        
        # Focus on search input
        self.search_input.setFocus()
        
    def show_empty_state(self):
        """Show empty state in results area"""
        self.clear_results()
        
        empty_label = QLabel("🎮\n\nEnter a game name above to search Steam's database")
        empty_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_MUTED};
                font-size: 16px;
                padding: 40px;
            }}
        """)
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.results_layout.addWidget(empty_label)
        
    def show_no_results_state(self, query):
        """Show no results state"""
        self.clear_results()
        
        no_results_label = QLabel(f"🚫\n\nNo games found for '{query}'\n\nTry a different search term")
        no_results_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_MUTED};
                font-size: 16px;
                padding: 40px;
            }}
        """)
        no_results_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.results_layout.addWidget(no_results_label)
        
    def show_loading_state(self):
        """Show loading state"""
        self.clear_results()
        
        loading_label = QLabel("⏳\n\nSearching...")
        loading_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.ACCENT_BLUE};
                font-size: 16px;
                padding: 40px;
            }}
        """)
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.results_layout.addWidget(loading_label)
        
    def clear_results(self):
        """Clear all results from the layout"""
        while self.results_layout.count():
            child = self.results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
    def perform_search(self):
        """Perform Steam game search"""
        query = self.search_input.text().strip()
        
        if not query:
            self.status_label.setText("Please enter a game name to search")
            self.status_label.setStyleSheet(f"color: {Theme.ACCENT_RED}; font-size: 14px;")
            return
            
        # Show loading state
        self.show_loading_state()
        self.status_label.setText(f"Searching for '{query}'...")
        self.status_label.setStyleSheet(f"color: {Theme.ACCENT_BLUE}; font-size: 14px;")
        
        # Disable search button
        self.search_button.setEnabled(False)
        self.search_button.setText("⏳ Searching...")
        
        # Start search in worker thread
        self.search_worker = SearchWorker(self.logic, query, 20)
        self.search_worker.search_completed.connect(self.on_search_completed)
        self.search_worker.start()
        
    def on_search_completed(self, result):
        """Handle search completion"""
        # Re-enable search button
        self.search_button.setEnabled(True)
        self.search_button.setText("🔍 Search")
        
        if not result['success']:
            self.status_label.setText(f"Error searching: {result['error']}")
            self.status_label.setStyleSheet(f"color: {Theme.ACCENT_RED}; font-size: 14px;")
            self.show_empty_state()
            return
            
        games = result['games']
        query = self.search_input.text().strip()
        
        if not games:
            self.status_label.setText(f"No games found for '{query}'")
            self.status_label.setStyleSheet(f"color: {Theme.ACCENT_ORANGE}; font-size: 14px;")
            self.show_no_results_state(query)
            return
            
        # Show results
        self.status_label.setText(f"Found {len(games)} games for '{query}'")
        self.status_label.setStyleSheet(f"color: {Theme.ACCENT_GREEN}; font-size: 14px;")
        
        self.clear_results()
        
        for i, game in enumerate(games, 1):
            game_widget = GameResultWidget(game)
            game_widget.appid_copied.connect(self.on_appid_copied)
            self.results_layout.addWidget(game_widget)
            
        # Add stretch at the end
        self.results_layout.addStretch()
        
    def on_appid_copied(self, appid):
        """Handle AppID copied to clipboard"""
        self.status_label.setText(f"AppID {appid} copied to clipboard!")
        self.status_label.setStyleSheet(f"color: {Theme.ACCENT_GREEN}; font-size: 14px;")
        
        # Reset status after 3 seconds
        QTimer.singleShot(3000, lambda: self.status_label.setText("Enter a game name and click search"))
