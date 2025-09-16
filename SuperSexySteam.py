# SuperSexySteam_PySide6.py
#
# A modern, sleek, and powerful GUI for SuperSexySteam using PySide6
# Features smooth animations, gradients, and a sophisticated interface
# with a focus on user experience and performance.

import sys
import os
import json
import logging
import subprocess
import configparser
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging for the entire application
class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[91m',    # Red
        'ERROR': '\033[91m',      # Red
        'CRITICAL': '\033[95m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Get the original formatted message
        log_message = super().format(record)
        
        # Add color for logs
        level_name = record.levelname
        if level_name in self.COLORS:
            color = self.COLORS[level_name]
            reset = self.COLORS['RESET']
            # Color the entire log message
            log_message = f"{color}{log_message}{reset}"
        
        return log_message

# Create colored formatter
colored_formatter = ColoredFormatter('[%(name)s] [%(levelname)s] %(message)s')

# Create stream handler with colored formatter
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(colored_formatter)

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[stream_handler]
)

# Suppress verbose logs from Steam client and related libraries
# These libraries generate excessive DEBUG logs that clutter the output
logging.getLogger('steam').setLevel(logging.WARNING)
logging.getLogger('SteamClient').setLevel(logging.WARNING)
logging.getLogger('CMServerList').setLevel(logging.WARNING)
logging.getLogger('Connection').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('connection').setLevel(logging.WARNING)

# Get logger for this module
logger = logging.getLogger(__name__)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QScrollArea, QTextEdit,
    QProgressBar, QTabWidget, QSplitter, QListWidget, QListWidgetItem,
    QGridLayout, QGroupBox, QSpacerItem, QSizePolicy, QStackedWidget,
    QFileDialog, QMessageBox, QInputDialog, QComboBox, QStatusBar, QDialog
)
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QThread,
    Signal, QSize, QPoint, QParallelAnimationGroup, QSequentialAnimationGroup
)
from PySide6.QtGui import (
    QPainter, QLinearGradient, QRadialGradient, QColor, QPen, QBrush,
    QFont, QFontMetrics, QPalette, QPixmap, QIcon, QMovie, QTransform, QClipboard
)

# Import our application logic
from app_logic import SuperSexySteamLogic


class Theme:
    """Modern dark theme with gradients and smooth animations"""
    
    # Color Palette - Modern dark theme with gold accents
    PRIMARY_DARK = "#0a0a0a"
    SECONDARY_DARK = "#1a1a1a" 
    TERTIARY_DARK = "#2a2a2a"
    SURFACE_DARK = "#333333"
    
    GOLD_PRIMARY = "#ffd700"
    GOLD_SECONDARY = "#ffed4e"
    GOLD_DARK = "#b8860b"
    
    ACCENT_BLUE = "#00d4ff"
    ACCENT_PURPLE = "#9c27b0"
    ACCENT_GREEN = "#4caf50"
    ACCENT_RED = "#f44336"
    ACCENT_ORANGE = "#ff9800"
    
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#b0b0b0"
    TEXT_MUTED = "#777777"
    
    # Gradients
    MAIN_GRADIENT = f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {PRIMARY_DARK}, stop:1 {SECONDARY_DARK})"
    GOLD_GRADIENT = f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {GOLD_PRIMARY}, stop:1 {GOLD_DARK})"
    BLUE_GRADIENT = f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {ACCENT_BLUE}, stop:0.5 #0099cc, stop:1 #006699)"
    
    # Animations
    ANIMATION_DURATION = 300
    HOVER_ANIMATION_DURATION = 150
    
    @staticmethod
    def get_button_style(gradient_color=None, text_color=None):
        """Get modern button styling with gradients and smooth hover effects (no transforms)"""
        if gradient_color is None:
            gradient_color = Theme.GOLD_GRADIENT
        if text_color is None:
            text_color = Theme.PRIMARY_DARK
            
        # Determine hover colors based on the base gradient
        hover_gradient = gradient_color
        if gradient_color == Theme.GOLD_GRADIENT:
            hover_gradient = f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Theme.GOLD_SECONDARY}, stop:1 {Theme.GOLD_PRIMARY})"
        elif gradient_color == Theme.BLUE_GRADIENT:
            hover_gradient = f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00e6ff, stop:0.5 #00b3e6, stop:1 #0080b3)"
        elif gradient_color == Theme.ACCENT_RED:
            hover_gradient = "#f44336"
        elif gradient_color == Theme.ACCENT_GREEN:
            hover_gradient = "#4caf50"
        elif gradient_color == Theme.ACCENT_ORANGE:
            hover_gradient = "#ff9800"
            
        return f"""
        QPushButton {{
            background: {gradient_color};
            color: {text_color};
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: bold;
            font-size: 14px;
            outline: none;
        }}
        QPushButton:hover {{
            background: {hover_gradient};
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        QPushButton:focus {{
            background: {hover_gradient};
            border: 2px solid {Theme.GOLD_PRIMARY};
        }}
        QPushButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Theme.GOLD_DARK}, stop:1 {Theme.GOLD_PRIMARY});
        }}
        QPushButton:disabled {{
            background: {Theme.SURFACE_DARK};
            color: {Theme.TEXT_MUTED};
        }}
        """
    
    @staticmethod
    def get_frame_style():
        """Get modern frame styling with subtle gradients"""
        return f"""
        QFrame {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {Theme.TERTIARY_DARK}, stop:1 {Theme.SURFACE_DARK});
            border: 1px solid {Theme.SURFACE_DARK};
            border-radius: 12px;
        }}
        """
    
    @staticmethod
    def get_input_style():
        """Get modern input field styling"""
        return f"""
        QLineEdit {{
            background: {Theme.SURFACE_DARK};
            color: {Theme.TEXT_PRIMARY};
            border: 2px solid transparent;
            border-radius: 8px;
            padding: 12px;
            font-size: 14px;
        }}
        QLineEdit:focus {{
            border: 2px solid {Theme.GOLD_PRIMARY};
            background: {Theme.TERTIARY_DARK};
        }}
        QLineEdit:hover {{
            border: 2px solid {Theme.GOLD_SECONDARY};
        }}
        """


class AnimatedButton(QPushButton):
    """Custom button with smooth hover animations using proper Qt geometry animations"""
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        
        # Set up size policies for better layout handling
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        
        # Store original geometry for animations
        self.is_hovered = False
        self.is_pressed = False
        self.base_size = None
        
        # Animation setup for smooth scaling
        self.hover_animation = QPropertyAnimation(self, b"geometry")
        self.hover_animation.setDuration(Theme.HOVER_ANIMATION_DURATION)
        self.hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.press_animation = QPropertyAnimation(self, b"geometry")
        self.press_animation.setDuration(100)
        self.press_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Apply CSS styling without transforms
        self.update_style()
        
        # Set a minimum size to prevent layout issues
        self.setMinimumSize(120, 40)
        
    def update_style(self):
        """Update button style with CSS-based effects (no transforms)"""
        style = f"""
        QPushButton {{
            background: {Theme.GOLD_GRADIENT};
            color: {Theme.PRIMARY_DARK};
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: bold;
            font-size: 14px;
            outline: none;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Theme.GOLD_SECONDARY}, stop:1 {Theme.GOLD_PRIMARY});
            border: 2px solid rgba(255, 237, 78, 0.3);
        }}
        QPushButton:focus {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Theme.GOLD_SECONDARY}, stop:1 {Theme.GOLD_PRIMARY});
            border: 2px solid {Theme.GOLD_PRIMARY};
        }}
        QPushButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Theme.GOLD_DARK}, stop:1 {Theme.GOLD_PRIMARY});
            border: 2px solid rgba(184, 134, 11, 0.5);
        }}
        QPushButton:disabled {{
            background: {Theme.SURFACE_DARK};
            color: {Theme.TEXT_MUTED};
        }}
        """
        self.setStyleSheet(style)
        
    def showEvent(self, event):
        """Handle initial show to store base size"""
        super().showEvent(event)
        if self.base_size is None:
            self.base_size = self.size()
        
    def resizeEvent(self, event):
        """Handle resize events properly"""
        super().resizeEvent(event)
        # Update base size when widget is resized by layout
        if not self.is_hovered and not self.is_pressed:
            self.base_size = event.size()
        
    def enterEvent(self, event):
        """Handle mouse enter with smooth scaling animation"""
        if not self.is_hovered and self.isEnabled():
            self.is_hovered = True
            self.animate_scale(1.03)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave with smooth return to normal size"""
        if self.is_hovered:
            self.is_hovered = False
            self.is_pressed = False
            self.animate_scale(1.0)
        super().leaveEvent(event)
        
    def mousePressEvent(self, event):
        """Handle mouse press with subtle scale down"""
        if not self.is_pressed and self.isEnabled():
            self.is_pressed = True
            self.animate_scale(0.97)
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if self.is_pressed:
            self.is_pressed = False
            # Return to hover state if still hovering, otherwise normal
            scale = 1.03 if self.is_hovered else 1.0
            self.animate_scale(scale)
        super().mouseReleaseEvent(event)
        
    def animate_scale(self, scale_factor):
        """Animate button scaling with proper geometry handling"""
        if self.base_size is None:
            self.base_size = self.size()
            
        current_rect = self.geometry()
        
        # Calculate new size
        new_width = int(self.base_size.width() * scale_factor)
        new_height = int(self.base_size.height() * scale_factor)
        
        # Calculate position to center the scaling
        width_diff = new_width - current_rect.width()
        height_diff = new_height - current_rect.height()
        
        new_x = current_rect.x() - width_diff // 2
        new_y = current_rect.y() - height_diff // 2
        
        new_rect = QRect(new_x, new_y, new_width, new_height)
        
        # Stop any running animation
        if self.hover_animation.state() == QPropertyAnimation.State.Running:
            self.hover_animation.stop()
            
        # Animate to new geometry
        self.hover_animation.setStartValue(current_rect)
        self.hover_animation.setEndValue(new_rect)
        self.hover_animation.start()


class GradientFrame(QFrame):
    """Custom frame with gradient background"""
    
    def __init__(self, parent=None, gradient_colors=None):
        super().__init__(parent)
        self.gradient_colors = gradient_colors or [Theme.TERTIARY_DARK, Theme.SURFACE_DARK]
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create gradient
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(self.gradient_colors[0]))
        gradient.setColorAt(1, QColor(self.gradient_colors[1]))
        
        # Draw rounded rectangle with gradient
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 12, 12)


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


class RefreshWorker(QThread):
    """Worker thread for refreshing games"""
    
    refresh_completed = Signal(dict)
    
    def __init__(self, logic, app_id, game_name):
        super().__init__()
        self.logic = logic
        self.app_id = app_id
        self.game_name = game_name
        
    def run(self):
        """Refresh game by simulating drag and drop with existing files"""
        result = self.logic.refresh_game_from_data_folder(self.app_id, self.game_name)
        self.refresh_completed.emit(result)


class InstalledGameWidget(GradientFrame):
    """Widget to display a single installed game with expandable depot details"""
    
    uninstall_requested = Signal(str, str)  # app_id, game_name
    refresh_requested = Signal(str, str)  # app_id, game_name
    expansion_requested = Signal(object)  # self
    
    def __init__(self, game_data, parent=None):
        super().__init__(parent, [Theme.SURFACE_DARK, Theme.TERTIARY_DARK])
        self.game_data = game_data
        self.is_expanded = False
        self.depot_widget = None
        self.expand_button = None
        self.parent_dialog = None  # Reference to parent dialog for exclusive expansion
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(12)
        
        # Top section: Game name with expand button
        top_layout = QHBoxLayout()
        
        # Expand/collapse button
        self.expand_button = QPushButton("▶")
        self.expand_button.setFixedSize(20, 20)
        self.expand_button.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.GOLD_PRIMARY};
                border: none;
                font-size: 12px;
                font-weight: bold;
                padding: 0px;
                outline: none;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
            }}
        """)
        self.expand_button.clicked.connect(self.toggle_expansion)
        top_layout.addWidget(self.expand_button)
        
        # Game name
        name_label = QLabel(self.game_data['game_name'])
        name_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_PRIMARY};
                font-size: 18px;
                font-weight: bold;
            }}
        """)
        name_label.setWordWrap(True)
        top_layout.addWidget(name_label, 1)
        
        layout.addLayout(top_layout)
        
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
        
        # Refresh button
        refresh_button = AnimatedButton("Refresh")
        refresh_button.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.GOLD_PRIMARY};
                color: {Theme.TEXT_PRIMARY};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
                min-width: 100px;
                outline: none;
            }}
            QPushButton:hover {{
                background: {Theme.GOLD_SECONDARY};
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
            QPushButton:focus {{
                background: {Theme.GOLD_SECONDARY};
                border: 2px solid {Theme.GOLD_PRIMARY};
            }}
            QPushButton:pressed {{
                background: #b8860b;
            }}
        """)
        refresh_button.clicked.connect(self.request_refresh)
        bottom_layout.addWidget(refresh_button)
        
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
                outline: none;
            }}
            QPushButton:hover {{
                background: #f44336;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
            QPushButton:focus {{
                background: #f44336;
                border: 2px solid {Theme.ACCENT_RED};
            }}
            QPushButton:pressed {{
                background: #d32f2f;
            }}
        """)
        uninstall_button.clicked.connect(self.request_uninstall)
        bottom_layout.addWidget(uninstall_button)
        
        layout.addLayout(bottom_layout)
        
        # Create depot widget (initially hidden)
        self.create_depot_widget()
        layout.addWidget(self.depot_widget)
        
    def create_depot_widget(self):
        """Create the expandable depot list widget"""
        self.depot_widget = QWidget()
        depot_layout = QVBoxLayout(self.depot_widget)
        depot_layout.setContentsMargins(30, 10, 10, 10)
        depot_layout.setSpacing(8)
        
        # Get depots from game data (assuming it's available)
        depots = self.game_data.get('depots', [])
        
        if depots:
            # Depot list header
            header_label = QLabel("Depot Details:")
            header_label.setStyleSheet(f"""
                QLabel {{
                    color: {Theme.GOLD_SECONDARY};
                    font-size: 14px;
                    font-weight: bold;
                    margin-bottom: 5px;
                }}
            """)
            depot_layout.addWidget(header_label)
            
            # Individual depot entries
            for depot in depots:
                depot_item = self.create_depot_item(depot)
                depot_layout.addWidget(depot_item)
        else:
            # No depots message
            no_depots_label = QLabel("No depot information available")
            no_depots_label.setStyleSheet(f"""
                QLabel {{
                    color: {Theme.TEXT_MUTED};
                    font-size: 12px;
                    font-style: italic;
                }}
            """)
            depot_layout.addWidget(no_depots_label)
        
        # Initially hidden
        self.depot_widget.hide()
        
    def create_depot_item(self, depot):
        """Create a single depot item with delete button"""
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(0, 5, 0, 5)
        item_layout.setSpacing(10)
        
        # Depot info
        depot_id = depot.get('depot_id', 'Unknown')
        depot_name = depot.get('depot_name', 'No Name')
        depot_text = f"{depot_id} - {depot_name}"
        
        depot_label = QLabel(depot_text)
        depot_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_SECONDARY};
                font-size: 13px;
                padding: 5px 10px;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 4px;
            }}
        """)
        item_layout.addWidget(depot_label, 1)
        
        return item_widget
    
    def toggle_expansion(self):
        """Toggle the expansion state of the depot list"""
        if self.is_expanded:
            # Collapse this widget
            self.collapse()
        else:
            # Request expansion (parent will handle exclusive logic)
            self.expansion_requested.emit(self)
    
    def expand(self):
        """Expand the depot list"""
        if not self.is_expanded:
            self.depot_widget.show()
            self.expand_button.setText("▼")
            self.is_expanded = True
    
    def collapse(self):
        """Collapse the depot list"""
        if self.is_expanded:
            self.depot_widget.hide()
            self.expand_button.setText("▶")
            self.is_expanded = False
        
    def set_parent_dialog(self, parent_dialog):
        """Set reference to parent dialog for exclusive expansion management"""
        self.parent_dialog = parent_dialog
    
    def request_uninstall(self):
        """Request uninstallation of this game"""
        self.uninstall_requested.emit(
            str(self.game_data['app_id']), 
            self.game_data['game_name']
        )
    
    def request_refresh(self):
        """Request refresh/reinstallation of this game"""
        self.refresh_requested.emit(
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
        self.game_widgets = []  # List to track all game widgets
        self.currently_expanded_widget = None  # Track currently expanded widget
        self.setup_ui()
        self.setup_window()
        self.load_games()
        
    def setup_window(self):
        """Setup dialog window properties"""
        self.setWindowTitle("Installed Games")
        self.setModal(True)
        
        # Match the parent window size if available, otherwise use main window default size
        if self.parent():
            parent_size = self.parent().size()
            self.resize(parent_size)
        else:
            self.resize(800, 600)  # Match main window default size
        
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
                outline: none;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00e6ff, stop:0.5 #00b3e6, stop:1 #0080b3);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
            QPushButton:focus {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00e6ff, stop:0.5 #00b3e6, stop:1 #0080b3);
                border: 2px solid {Theme.ACCENT_BLUE};
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #006699, stop:1 #0099cc);
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
                outline: none;
            }}
            QPushButton:hover {{
                background: #f44336;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
            QPushButton:focus {{
                background: #f44336;
                border: 2px solid {Theme.ACCENT_RED};
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
        
        # Ensure the widget is properly updated
        self.games_widget.update()
        
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
        
        # Ensure the widget is properly updated
        self.games_widget.update()
        
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
        
        # Ensure the widget is properly updated
        self.games_widget.update()
        
    def handle_expansion_request(self, requesting_widget):
        """Handle exclusive expansion - only one widget can be expanded at a time"""
        # If there's a currently expanded widget that's different from the requesting one, collapse it
        if (self.currently_expanded_widget and 
            self.currently_expanded_widget != requesting_widget and 
            self.currently_expanded_widget.is_expanded):
            self.currently_expanded_widget.collapse()
        
        # Expand the requesting widget
        requesting_widget.expand()
        self.currently_expanded_widget = requesting_widget
    
    def clear_games(self):
        """Clear all games from the layout"""
        # Reset tracking variables
        self.currently_expanded_widget = None
        self.game_widgets.clear()
        
        while self.games_layout.count():
            child = self.games_layout.takeAt(0)
            if child.widget():
                widget = child.widget()
                widget.setParent(None)
                widget.deleteLater()
        
        # Process events to ensure widgets are actually removed
        QApplication.processEvents()
                
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
        self.refresh_button.setText("Refresh")
        
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
            game_widget.refresh_requested.connect(self.refresh_game)
            game_widget.expansion_requested.connect(self.handle_expansion_request)
            game_widget.set_parent_dialog(self)
            self.game_widgets.append(game_widget)
            self.games_layout.addWidget(game_widget)
            
        # Add stretch at the end
        self.games_layout.addStretch()
        
    def uninstall_game(self, app_id, game_name):
        """Uninstall a specific game"""
        # Show beautiful animated confirmation dialog
        confirmation = ConfirmationOverlay(
            title="Confirm Uninstall",
            message=f"Are you sure you want to uninstall '{game_name}' (AppID: {app_id})?\n\n"
                   "This will remove all related files and data.",
            confirm_text="✓ Yes, Uninstall",
            cancel_text="✗ Cancel",
            parent=self
        )
        
        # Connect the signals
        confirmation.confirmed.connect(lambda: self.proceed_with_uninstall(app_id, game_name))
        # If cancelled, nothing happens (dialog just closes)
        
        # Show the confirmation dialog
        confirmation.exec()
        
    def proceed_with_uninstall(self, app_id, game_name):
        """Proceed with the actual uninstallation after confirmation"""
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
        self.refresh_button.setText("Refresh")
        
        if result['success']:
            self.status_label.setText(f"Successfully uninstalled {game_name}")
            self.status_label.setStyleSheet(f"color: {Theme.ACCENT_GREEN}; font-size: 14px;")
            
            # Reload games list
            QTimer.singleShot(1000, self.load_games)
        else:
            self.status_label.setText(f"Failed to uninstall {game_name}: {result['error']}")
            self.status_label.setStyleSheet(f"color: {Theme.ACCENT_RED}; font-size: 14px;")
    
    def refresh_game(self, app_id, game_name):
        """Refresh a specific game by simulating drag and drop"""
        # Start refresh process
        self.status_label.setText(f"Refreshing {game_name}...")
        self.status_label.setStyleSheet(f"color: {Theme.ACCENT_ORANGE}; font-size: 14px;")
        
        # Disable refresh button during refresh
        self.refresh_button.setEnabled(False)
        self.refresh_button.setText("⏳ Refreshing...")
        
        # Start refresh in worker thread
        self.refresh_worker = RefreshWorker(self.logic, app_id, game_name)
        self.refresh_worker.refresh_completed.connect(
            lambda result: self.on_refresh_completed(result, game_name)
        )
        self.refresh_worker.start()
    
    def on_refresh_completed(self, result, game_name):
        """Handle refresh completion"""
        # Re-enable refresh button
        self.refresh_button.setEnabled(True)
        self.refresh_button.setText("Refresh")
        
        if result['success']:
            self.status_label.setText(f"Successfully refreshed {game_name}")
            self.status_label.setStyleSheet(f"color: {Theme.ACCENT_GREEN}; font-size: 14px;")
            
            # Reload games list
            QTimer.singleShot(1000, self.load_games)
        else:
            self.status_label.setText(f"Failed to refresh {game_name}: {result['error']}")
            self.status_label.setStyleSheet(f"color: {Theme.ACCENT_RED}; font-size: 14px;")


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
                outline: none;
            }}
            QPushButton:hover {{
                background: #4caf50;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
            QPushButton:focus {{
                background: #4caf50;
                border: 2px solid {Theme.ACCENT_GREEN};
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


class ConfirmationOverlay(QDialog):
    """Beautiful animated confirmation dialog that matches the app's aesthetic"""
    
    confirmed = Signal()
    cancelled = Signal()
    
    def __init__(self, title, message, confirm_text="Yes", cancel_text="No", 
                 dialog_type="warning", parent=None):
        super().__init__(parent)
        self.title = title
        self.message = message
        self.confirm_text = confirm_text
        self.cancel_text = cancel_text
        self.dialog_type = dialog_type  # "warning", "error", "info"
        self.result_confirmed = False
        
        self.setup_window()
        self.setup_ui()
        self.setup_animations()
        
    def setup_window(self):
        """Setup dialog window properties"""
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Set a fixed size for the overlay to avoid positioning issues
        self.resize(800, 600)
        
        # Always center on screen - this is the most reliable approach
        self.center_on_screen()
            
    def center_on_screen(self):
        """Center dialog on screen"""
        try:
            # Get the screen that contains the parent widget, or primary screen
            screen = QApplication.primaryScreen()
            if self.parent() and hasattr(self.parent(), 'window'):
                # Try to get the screen that contains the parent window
                parent_window = self.parent().window()
                if hasattr(parent_window, 'screen') and parent_window.screen():
                    screen = parent_window.screen()
            
            screen_geometry = screen.geometry()
            
            # Calculate center position
            x = (screen_geometry.width() - self.width()) // 2 + screen_geometry.x()
            y = (screen_geometry.height() - self.height()) // 2 + screen_geometry.y()
            
            self.move(x, y)
        except Exception:
            # Ultimate fallback positioning
            self.move(200, 200)
            
    def setup_ui(self):
        """Setup the confirmation dialog UI"""
        # Main layout with transparent background
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Semi-transparent background overlay
        self.background_overlay = QWidget()
        self.background_overlay.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(10, 10, 10, 180),
                    stop:1 rgba(26, 26, 26, 180));
            }}
        """)
        main_layout.addWidget(self.background_overlay)
        
        # Center the dialog content
        overlay_layout = QVBoxLayout(self.background_overlay)
        overlay_layout.addStretch()
        
        # Create the confirmation card
        self.confirmation_card = GradientFrame()
        self.confirmation_card.setMaximumWidth(500)
        self.confirmation_card.setMinimumWidth(400)
        self.confirmation_card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        
        self.confirmation_card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 {Theme.SECONDARY_DARK}, 
                    stop:1 {Theme.TERTIARY_DARK});
                border: none;
                border-radius: 16px;
            }}
        """)
        
        card_layout = QVBoxLayout(self.confirmation_card)
        card_layout.setContentsMargins(40, 30, 40, 30)
        card_layout.setSpacing(25)
        
        # Icon based on dialog type
        icon_text = "⚠️"
        icon_color = Theme.ACCENT_ORANGE
        if self.dialog_type == "error":
            icon_text = "❌"
            icon_color = Theme.ACCENT_RED
        elif self.dialog_type == "info":
            icon_text = "ℹ️"
            icon_color = Theme.ACCENT_BLUE
            
        icon_label = QLabel(icon_text)
        icon_label.setStyleSheet(f"""
            QLabel {{
                color: {icon_color};
                font-size: 48px;
            }}
        """)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_PRIMARY};
                font-size: 24px;
                font-weight: bold;
            }}
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        card_layout.addWidget(title_label)
        
        # Message
        message_label = QLabel(self.message)
        message_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_SECONDARY};
                font-size: 16px;
                line-height: 1.4;
            }}
        """)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setWordWrap(True)
        card_layout.addWidget(message_label)
        
        # Button layout (only show if it's not an error-only dialog)
        if self.dialog_type != "error" or self.cancel_text != "No":
            button_layout = QHBoxLayout()
            button_layout.setSpacing(15)
            
            # Cancel button (if needed)
            if self.cancel_text and self.cancel_text != "No" or self.dialog_type != "error":
                self.cancel_button = AnimatedButton(self.cancel_text)
                self.cancel_button.setStyleSheet(f"""
                    QPushButton {{
                        background: {Theme.SURFACE_DARK};
                        color: {Theme.TEXT_PRIMARY};
                        border: 2px solid {Theme.TEXT_MUTED};
                        border-radius: 8px;
                        padding: 15px 30px;
                        font-weight: bold;
                        font-size: 14px;
                        min-width: 100px;
                        outline: none;
                    }}
                    QPushButton:hover {{
                        background: {Theme.TERTIARY_DARK};
                        border: 2px solid {Theme.TEXT_SECONDARY};
                    }}
                    QPushButton:focus {{
                        background: {Theme.TERTIARY_DARK};
                        border: 2px solid {Theme.TEXT_PRIMARY};
                    }}
                    QPushButton:pressed {{
                        background: {Theme.PRIMARY_DARK};
                    }}
                """)
                self.cancel_button.clicked.connect(self.on_cancel)
                button_layout.addWidget(self.cancel_button)
            
            # Confirm button
            confirm_bg_color = Theme.ACCENT_RED
            confirm_pressed_color = "#d32f2f"  # Darker red
            if self.dialog_type == "info":
                confirm_bg_color = Theme.ACCENT_BLUE
                confirm_pressed_color = "#0080b3"  # Darker blue
            elif self.dialog_type == "error":
                confirm_bg_color = Theme.ACCENT_RED
                confirm_pressed_color = "#d32f2f"  # Darker red
                
            self.confirm_button = AnimatedButton(self.confirm_text)
            self.confirm_button.setStyleSheet(f"""
                QPushButton {{
                    background: {confirm_bg_color};
                    color: {Theme.TEXT_PRIMARY};
                    border: none;
                    border-radius: 8px;
                    padding: 15px 30px;
                    font-weight: bold;
                    font-size: 14px;
                    min-width: 100px;
                    outline: none;
                }}
                QPushButton:hover {{
                    background: {confirm_bg_color};
                    border: 2px solid rgba(255, 255, 255, 0.2);
                }}
                QPushButton:focus {{
                    background: {confirm_bg_color};
                    border: 2px solid rgba(255, 255, 255, 0.4);
                }}
                QPushButton:pressed {{
                    background: {confirm_pressed_color};
                }}
            """)
            self.confirm_button.clicked.connect(self.on_confirm)
            button_layout.addWidget(self.confirm_button)
            
            card_layout.addLayout(button_layout)
        else:
            # Error dialog with just OK button
            self.confirm_button = AnimatedButton("OK")
            self.confirm_button.setStyleSheet(f"""
                QPushButton {{
                    background: {Theme.ACCENT_RED};
                    color: {Theme.TEXT_PRIMARY};
                    border: none;
                    border-radius: 8px;
                    padding: 15px 30px;
                    font-weight: bold;
                    font-size: 14px;
                    min-width: 100px;
                    outline: none;
                }}
                QPushButton:hover {{
                    background: #f44336;
                    border: 2px solid rgba(255, 255, 255, 0.2);
                }}
                QPushButton:focus {{
                    background: #f44336;
                    border: 2px solid rgba(255, 255, 255, 0.4);
                }}
                QPushButton:pressed {{
                    background: #d32f2f;
                }}
            """)
            self.confirm_button.clicked.connect(self.on_confirm)
            card_layout.addWidget(self.confirm_button)
        
        # Center the card horizontally
        center_layout = QHBoxLayout()
        center_layout.addStretch()
        center_layout.addWidget(self.confirmation_card)
        center_layout.addStretch()
        
        overlay_layout.addLayout(center_layout)
        overlay_layout.addStretch()
        
    def setup_animations(self):
        """Setup smooth entrance and exit animations"""
        # Fade in animation for background
        self.fade_animation = QPropertyAnimation(self.background_overlay, b"windowOpacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Scale animation for the card - removed as it causes positioning issues
        # We'll use CSS-based hover effects instead for better reliability
        
    def showEvent(self, event):
        """Animate the dialog entrance"""
        super().showEvent(event)
        
        # Ensure proper positioning every time the dialog is shown
        self.center_on_screen()
        
        # Start with invisible background
        self.background_overlay.setWindowOpacity(0.0)
        
        # Simple fade in animation - no complex geometry animations
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
        
    def hide_with_animation(self):
        """Animate the dialog exit and properly close"""
        # Create a simple fade out animation
        fade_out = QPropertyAnimation(self.background_overlay, b"windowOpacity")
        fade_out.setDuration(150)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        
        # Connect to proper cleanup and close
        fade_out.finished.connect(self.close_dialog)
        fade_out.start()
        
        # Store reference to prevent garbage collection
        self.exit_animation = fade_out
        
    def close_dialog(self):
        """Properly close the dialog"""
        # Clean up animations
        if hasattr(self, 'fade_animation'):
            self.fade_animation.stop()
        if hasattr(self, 'exit_animation'):
            self.exit_animation.stop()
            
        # Ensure the dialog closes
        try:
            self.accept()
        except Exception:
            # Fallback to direct close if accept fails
            self.close()
            
    def reject(self):
        """Override reject to ensure proper cleanup"""
        self.result_confirmed = False
        self.cancelled.emit()
        self.close_dialog()
        
    def accept(self):
        """Override accept to ensure proper cleanup"""
        super().accept()
        
    def on_confirm(self):
        """Handle confirmation"""
        self.result_confirmed = True
        self.confirmed.emit()
        self.hide_with_animation()
        
    def on_cancel(self):
        """Handle cancellation"""
        self.result_confirmed = False
        self.cancelled.emit()
        self.hide_with_animation()
        
    def closeEvent(self, event):
        """Handle close event properly"""
        # Stop any running animations
        if hasattr(self, 'fade_animation'):
            self.fade_animation.stop()
        if hasattr(self, 'exit_animation'):
            self.exit_animation.stop()
        event.accept()
        
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key.Key_Escape:
            self.on_cancel()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.on_confirm()
        else:
            super().keyPressEvent(event)


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
        
        # Match the parent window size if available, otherwise use main window default size
        if self.parent():
            parent_size = self.parent().size()
            self.resize(parent_size)
        else:
            self.resize(800, 600)  # Match main window default size
        
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
                outline: none;
            }}
            QPushButton:hover {{
                background: #f44336;
            }}
            QPushButton:focus {{
                background: #f44336;
                border: 2px solid {Theme.ACCENT_RED};
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


class DepotSelectionDialog(QDialog):
    """Dialog for selecting and managing depots after game installation"""
    
    depot_deleted = Signal(str, str)  # app_id, depot_id
    installation_completed = Signal(dict)  # installation result
    
    def __init__(self, app_id, game_name, depots, data_folder, game_installer, parent=None):
        super().__init__(parent)
        self.app_id = app_id
        self.game_name = game_name
        self.depots = depots
        self.data_folder = data_folder
        self.game_installer = game_installer
        self.depot_widgets = []
        self.setup_ui()
        self.setup_window()
        
    def setup_window(self):
        """Setup dialog window properties"""
        self.setWindowTitle(f"Depot Selection - {self.game_name}")
        self.setModal(True)
        self.resize(700, 500)
        
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
        title = QLabel(f"Depot Selection for {self.game_name}")
        title.setStyleSheet(f"""
            QLabel {{
                color: {Theme.GOLD_PRIMARY};
                font-size: 24px;
                font-weight: bold;
            }}
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel(f"AppID: {self.app_id} • {len(self.depots)} depot(s) found")
        subtitle.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_SECONDARY};
                font-size: 16px;
                margin-bottom: 10px;
            }}
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Info message
        info_label = QLabel("🗑️ Click the trash icon next to any depot you want to remove")
        info_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_SECONDARY};
                font-size: 14px;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 10px;
            }}
        """)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)
        
        # Scrollable depot list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(f"""
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
        
        depot_container = QWidget()
        depot_layout = QVBoxLayout(depot_container)
        depot_layout.setSpacing(10)
        depot_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create depot widgets
        for depot in self.depots:
            depot_widget = DepotItemWidget(depot, self)
            depot_widget.delete_requested.connect(self.on_depot_delete_requested)
            self.depot_widgets.append(depot_widget)
            depot_layout.addWidget(depot_widget)
        
        depot_layout.addStretch()
        scroll_area.setWidget(depot_container)
        layout.addWidget(scroll_area, 1)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # Continue button
        continue_button = AnimatedButton("✓ Continue with Installation")
        continue_button.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.ACCENT_GREEN};
                color: {Theme.TEXT_PRIMARY};
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 14px;
                outline: none;
            }}
            QPushButton:hover {{
                background: #66bb6a;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
            QPushButton:focus {{
                background: #66bb6a;
                border: 2px solid {Theme.ACCENT_GREEN};
            }}
            QPushButton:pressed {{
                background: #4caf50;
            }}
        """)
        continue_button.clicked.connect(self.accept)
        button_layout.addWidget(continue_button)
        
        button_layout.addStretch()
        
        # Cancel button
        cancel_button = AnimatedButton("✖ Cancel Installation")
        cancel_button.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.ACCENT_RED};
                color: {Theme.TEXT_PRIMARY};
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 14px;
                outline: none;
            }}
            QPushButton:hover {{
                background: #f44336;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
            QPushButton:focus {{
                background: #f44336;
                border: 2px solid {Theme.ACCENT_RED};
            }}
            QPushButton:pressed {{
                background: #d32f2f;
            }}
        """)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def on_depot_delete_requested(self, depot_id):
        """Handle depot deletion request"""
        # Find the depot info
        depot_info = None
        for depot in self.depots:
            if depot.get('depot_id') == depot_id:
                depot_info = depot
                break
        
        if not depot_info:
            return
        
        depot_name = depot_info.get('depot_name', 'No Name')
        
        # Show confirmation
        confirmation = ConfirmationOverlay(
            title="Delete Depot",
            message=f"Are you sure you want to remove this depot?\n\n"
                   f"Depot ID: {depot_id}\n"
                   f"Name: {depot_name}\n\n"
                   f"This will remove the depot from the lua file, delete its manifest file (if present), "
                   f"and remove it from the database.",
            confirm_text="Delete",
            parent=self
        )
        
        if confirmation.exec() == QDialog.DialogCode.Accepted:
            # Perform deletion
            self.delete_depot(depot_id)
    
    def delete_depot(self, depot_id):
        """Delete a depot from the game"""
        # Show loading state
        self.setEnabled(False)
        self.setCursor(Qt.CursorShape.WaitCursor)
        
        try:
            # Use the game installer to remove the depot
            result = self.game_installer.remove_depot_from_game(
                self.app_id, depot_id, self.data_folder
            )
            
            if result['success']:
                # Remove from UI
                self.remove_depot_from_ui(depot_id)
                
                # Remove from internal list
                self.depots = [d for d in self.depots if d.get('depot_id') != depot_id]
                
                # Update subtitle
                subtitle_widget = self.findChild(QLabel)
                if subtitle_widget and "depot(s) found" in subtitle_widget.text():
                    subtitle_widget.setText(f"AppID: {self.app_id} • {len(self.depots)} depot(s) found")
                
                # Emit signal
                self.depot_deleted.emit(self.app_id, depot_id)
                
                logger.info(f"Successfully deleted depot {depot_id} from AppID {self.app_id}")
                
            else:
                # Show error
                error_msg = '; '.join(result['errors']) if result['errors'] else "Unknown error"
                logger.error(f"Failed to delete depot {depot_id}: {error_msg}")
                
                # Show error dialog
                error_dialog = ConfirmationOverlay(
                    title="Deletion Failed",
                    message=f"Failed to remove depot {depot_id}:\n\n{error_msg}",
                    confirm_text="OK",
                    cancel_text="",
                    parent=self
                )
                error_dialog.exec()
                
        except Exception as e:
            logger.error(f"Exception during depot deletion: {e}")
            error_dialog = ConfirmationOverlay(
                title="Deletion Failed",
                message=f"An unexpected error occurred:\n\n{str(e)}",
                confirm_text="OK",
                cancel_text="",
                parent=self
            )
            error_dialog.exec()
        finally:
            self.setEnabled(True)
            self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def remove_depot_from_ui(self, depot_id):
        """Remove depot widget from UI"""
        for widget in self.depot_widgets[:]:  # Create copy to avoid modification during iteration
            if hasattr(widget, 'depot') and widget.depot.get('depot_id') == depot_id:
                widget.setParent(None)
                widget.deleteLater()
                self.depot_widgets.remove(widget)
                break
    
    def accept(self):
        """Continue installation when dialog is accepted (closed)"""
        try:
            logger.info(f"Depot selection complete for AppID {self.app_id}, continuing installation...")
            
            # First emit signal to update UI that installation is continuing
            progress_result = {
                'success': 'continuing',
                'app_id': self.app_id,
                'message': f"Continuing installation for AppID {self.app_id}..."
            }
            
            # Process events to ensure signal is delivered before continuing
            from PySide6.QtWidgets import QApplication
            self.installation_completed.emit(progress_result)
            QApplication.processEvents()
            
            # Continue the installation process
            result = self.game_installer.continue_installation(self.app_id, self.data_folder)
            
            if result['success']:
                stats = result['stats']
                logger.info(f"Installation continuation completed for AppID {self.app_id}")
                
                # Emit signal to notify main window about completion
                result['app_id'] = self.app_id
                self.installation_completed.emit(result)
                QApplication.processEvents()
            else:
                error_msg = '; '.join(result['errors']) if result['errors'] else "Installation continuation failed"
                logger.error(f"Installation continuation failed for AppID {self.app_id}: {error_msg}")
                
                # Emit signal with error result
                result['error_message'] = error_msg
                result['app_id'] = self.app_id
                self.installation_completed.emit(result)
                QApplication.processEvents()
                    
        except Exception as e:
            logger.error(f"Error during installation continuation: {e}")
            logger.debug("Installation continuation exception:", exc_info=True)
            
            # Emit signal with exception result
            error_result = {
                'success': False,
                'error_message': str(e),
                'app_id': self.app_id
            }
            self.installation_completed.emit(error_result)
            QApplication.processEvents()
        
        # Call parent accept to close dialog
        super().accept()


class DepotItemWidget(GradientFrame):
    """Widget for displaying a single depot with delete option"""
    
    delete_requested = Signal(str)  # depot_id
    
    def __init__(self, depot, parent=None):
        super().__init__(parent, [Theme.SURFACE_DARK, Theme.TERTIARY_DARK])
        self.depot = depot
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        
        # Depot info section
        info_layout = QVBoxLayout()
        
        # Depot ID and name
        depot_id = self.depot.get('depot_id', 'Unknown')
        depot_name = self.depot.get('depot_name', 'No Name')
        
        main_label = QLabel(f"Depot ID: {depot_id}")
        main_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_PRIMARY};
                font-size: 16px;
                font-weight: bold;
            }}
        """)
        info_layout.addWidget(main_label)
        
        name_label = QLabel(f"Name: {depot_name}")
        name_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_SECONDARY};
                font-size: 14px;
            }}
        """)
        info_layout.addWidget(name_label)
        
        # Additional info
        has_key = 'depot_key' in self.depot and self.depot['depot_key'] is not None
        key_status = "✓ Has decryption key" if has_key else "✗ No decryption key"
        key_color = Theme.ACCENT_GREEN if has_key else Theme.TEXT_MUTED
        
        key_label = QLabel(key_status)
        key_label.setStyleSheet(f"""
            QLabel {{
                color: {key_color};
                font-size: 12px;
                font-style: italic;
            }}
        """)
        info_layout.addWidget(key_label)
        
        layout.addLayout(info_layout, 1)
        
        # Delete button
        delete_button = QPushButton("🗑️")
        delete_button.setFixedSize(40, 40)
        delete_button.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.ACCENT_RED};
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 16px;
                font-weight: bold;
                outline: none;
            }}
            QPushButton:hover {{
                background: #f44336;
            }}
            QPushButton:focus {{
                background: #f44336;
                border: 2px solid {Theme.ACCENT_RED};
            }}
            QPushButton:pressed {{
                background: #d32f2f;
            }}
        """)
        delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_button.clicked.connect(lambda: self.delete_requested.emit(depot_id))
        layout.addWidget(delete_button)


class DropZone(GradientFrame):
    """Modern drag-and-drop zone with animations"""
    
    files_dropped = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent, [Theme.SECONDARY_DARK, Theme.TERTIARY_DARK])
        self.setAcceptDrops(True)
        self.is_hovering = False
        self.setup_ui()
        
        # Animation for hover effect
        self.hover_animation = QPropertyAnimation(self, b"geometry")
        self.hover_animation.setDuration(200)
        self.hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Drop icon
        drop_label = QLabel("⬇")
        drop_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_MUTED};
                font-size: 72px;
                font-weight: bold;
            }}
        """)
        drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(drop_label)
        
        # Main text
        text_label = QLabel("Drag and drop Lua + Manifest files here")
        text_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_SECONDARY};
                font-size: 18px;
                font-weight: bold;
            }}
        """)
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text_label)
        
        # Supported formats
        formats_label = QLabel("Supported: .lua, .manifest files")
        formats_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_MUTED};
                font-size: 14px;
            }}
        """)
        formats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(formats_label)
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.is_hovering = True
            self.setStyleSheet(f"""
                DropZone {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 rgba(255, 215, 0, 0.3), 
                        stop:1 rgba(184, 134, 11, 0.3));
                    border: 2px solid {Theme.GOLD_PRIMARY};
                    border-radius: 12px;
                }}
            """)
            self.update()
    
    def dragLeaveEvent(self, event):
        self.is_hovering = False
        self.setStyleSheet("")
        self.update()
        
    def dropEvent(self, event):
        self.is_hovering = False
        self.setStyleSheet("")
        self.update()
        if event.mimeData().hasUrls():
            files = [url.toLocalFile() for url in event.mimeData().urls()]
            self.files_dropped.emit(files)
            event.acceptProposedAction()
    
    def paintEvent(self, event):
        """Override paint event to disable gradient when hovering"""
        if self.is_hovering:
            # Let the stylesheet handle the painting when hovering
            super(QFrame, self).paintEvent(event)
        else:
            # Use normal gradient painting when not hovering
            super().paintEvent(event)


class StatusBar(QStatusBar):
    """Modern animated status bar"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
        # Animation for status changes
        self.fade_animation = QPropertyAnimation(self.status_label, b"windowOpacity")
        self.fade_animation.setDuration(300)
        
    def setup_ui(self):
        self.setFixedHeight(60)
        self.setStyleSheet(f"""
            QStatusBar {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {Theme.TERTIARY_DARK}, 
                    stop:1 {Theme.SURFACE_DARK});
                border-top: 1px solid {Theme.SURFACE_DARK};
                color: {Theme.TEXT_PRIMARY};
            }}
        """)
        
        # Main status widget
        self.status_widget = QWidget()
        layout = QHBoxLayout(self.status_widget)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Status icon
        self.status_icon = QLabel("ℹ")
        self.status_icon.setStyleSheet("font-size: 16px;")
        layout.addWidget(self.status_icon)
        
        # Status text
        self.status_label = QLabel("Ready for action! Drop files to install games instantly.")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_SECONDARY};
                font-size: 14px;
                padding-left: 10px;
            }}
        """)
        layout.addWidget(self.status_label, 1)
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {Theme.SURFACE_DARK};
                border: none;
                border-radius: 8px;
                height: 16px;
            }}
            QProgressBar::chunk {{
                background: {Theme.GOLD_GRADIENT};
                border-radius: 8px;
            }}
        """)
        layout.addWidget(self.progress_bar)
        
        self.addWidget(self.status_widget)
        
    def update_status(self, message, status_type="info", show_progress=False):
        """Update status with animation"""
        logger.debug(f"Status bar update: '{message}' (type: {status_type}, progress: {show_progress})")
        
        # Icon mapping
        icons = {
            "info": "ℹ",
            "success": "✓", 
            "error": "✗",
            "warning": "⚠",
            "loading": "⟳"
        }
        
        # Color mapping
        colors = {
            "info": Theme.TEXT_SECONDARY,
            "success": Theme.ACCENT_GREEN,
            "error": Theme.ACCENT_RED,
            "warning": Theme.ACCENT_ORANGE,
            "loading": Theme.ACCENT_BLUE
        }
        
        self.status_icon.setText(icons.get(status_type, "ℹ️"))
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {colors.get(status_type, Theme.TEXT_SECONDARY)};
                font-size: 14px;
                padding-left: 10px;
            }}
        """)
        
        self.progress_bar.setVisible(show_progress)


class FirstTimeSetupWidget(QStackedWidget):
    """Modern first-time setup interface"""
    
    setup_completed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_data = {}
        self.setup_ui()
        
    def setup_ui(self):
        # Welcome page
        welcome_page = self.create_welcome_page()
        self.addWidget(welcome_page)
        
        # Steam path page
        steam_page = self.create_steam_path_page()
        self.addWidget(steam_page)
        
        # GreenLuma path page
        greenluma_page = self.create_greenluma_path_page()
        self.addWidget(greenluma_page)
        
        # Completion page
        completion_page = self.create_completion_page()
        self.addWidget(completion_page)
        
    def create_header_widget(self):
        """Create header widget with image or fallback text (same as main interface)"""
        try:
            # Try to load header.png
            header_path = Path(__file__).parent / "header.png"
            if header_path.exists():
                # Load and resize the header image
                pixmap = QPixmap(str(header_path))
                
                # Scale the image to a reasonable size while maintaining aspect ratio
                max_width = 500
                if pixmap.width() > max_width:
                    pixmap = pixmap.scaledToWidth(max_width, Qt.TransformationMode.SmoothTransformation)
                
                header_label = QLabel()
                header_label.setPixmap(pixmap)
                header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                header_label.setStyleSheet("background: transparent;")
                return header_label
            else:
                # Fallback to text header
                header_label = QLabel("SuperSexySteam")
                header_label.setStyleSheet(f"""
                    QLabel {{
                        color: {Theme.GOLD_PRIMARY};
                        font-size: 48px;
                        font-weight: bold;
                        background: transparent;
                        padding: 10px;
                    }}
                """)
                header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                return header_label
                
        except Exception as e:
            logger.warning(f"Failed to load header image in setup: {e}")
            # Fallback to text header
            header_label = QLabel("SuperSexySteam")
            header_label.setStyleSheet(f"""
                QLabel {{
                    color: {Theme.GOLD_PRIMARY};
                    font-size: 48px;
                    font-weight: bold;
                    background: transparent;
                    padding: 10px;
                }}
            """)
            header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            return header_label
        
    def create_welcome_page(self):
        """Create welcome page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(30)
        
        # Header with logo/banner (same as main interface)
        header_widget = self.create_header_widget()
        layout.addWidget(header_widget)
        
        # Subtitle
        subtitle = QLabel("Welcome to the most advanced Steam depot manager")
        subtitle.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_SECONDARY};
                font-size: 18px;
            }}
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Description
        description = QLabel("""
        SuperSexySteam provides powerful tools for managing Steam depot files,
        game installations, and database operations with a beautiful modern interface.
        
        Let's get you set up in just a few steps!
        """)
        description.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_PRIMARY};
                font-size: 16px;
                line-height: 1.6;
                padding: 20px;
                background: {Theme.SURFACE_DARK};
                border-radius: 12px;
            }}
        """)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Next button
        next_button = AnimatedButton("Get Started →")
        next_button.clicked.connect(lambda: self.setCurrentIndex(1))
        layout.addWidget(next_button)
        
        layout.addStretch()
        return page
        
    def create_steam_path_page(self):
        """Create Steam path configuration page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(30)
        
        # Title
        title = QLabel("Configure Steam Path")
        title.setStyleSheet(f"""
            QLabel {{
                color: {Theme.GOLD_PRIMARY};
                font-size: 32px;
                font-weight: bold;
            }}
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Input group
        input_group = GradientFrame()
        input_layout = QVBoxLayout(input_group)
        input_layout.setContentsMargins(30, 30, 30, 30)
        input_layout.setSpacing(15)
        
        # Label
        label = QLabel("Steam Installation Directory:")
        label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_PRIMARY};
                font-size: 16px;
                font-weight: bold;
            }}
        """)
        input_layout.addWidget(label)
        
        # Path input with browse button
        path_layout = QHBoxLayout()
        
        self.steam_path_input = QLineEdit()
        self.steam_path_input.setPlaceholderText("C:\\Program Files (x86)\\Steam")
        self.steam_path_input.setStyleSheet(Theme.get_input_style())
        self.steam_path_input.setText("C:\\Program Files (x86)\\Steam")  # Default
        path_layout.addWidget(self.steam_path_input, 1)
        
        browse_button = AnimatedButton("Browse")
        browse_button.clicked.connect(self.browse_steam_path)
        path_layout.addWidget(browse_button)
        
        input_layout.addLayout(path_layout)
        layout.addWidget(input_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        back_button = AnimatedButton("← Back")
        back_button.clicked.connect(lambda: self.setCurrentIndex(0))
        button_layout.addWidget(back_button)
        
        button_layout.addStretch()
        
        next_button = AnimatedButton("Next →")
        next_button.clicked.connect(self.save_steam_path_and_continue)
        button_layout.addWidget(next_button)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        return page
        
    def create_greenluma_path_page(self):
        """Create GreenLuma path configuration page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(30)
        
        # Title
        title = QLabel("Configure GreenLuma Path")
        title.setStyleSheet(f"""
            QLabel {{
                color: {Theme.GOLD_PRIMARY};
                font-size: 32px;
                font-weight: bold;
            }}
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Input group
        input_group = GradientFrame()
        input_layout = QVBoxLayout(input_group)
        input_layout.setContentsMargins(30, 30, 30, 30)
        input_layout.setSpacing(15)
        
        # Label
        label = QLabel("GreenLuma Directory:")
        label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_PRIMARY};
                font-size: 16px;
                font-weight: bold;
            }}
        """)
        input_layout.addWidget(label)
        
        # Path input with browse button
        path_layout = QHBoxLayout()
        
        self.greenluma_path_input = QLineEdit()
        self.greenluma_path_input.setPlaceholderText("C:\\Users\\Administrator\\Documents\\SuperSexySteam\\SuperSexySteam\\GreenLuma")
        self.greenluma_path_input.setStyleSheet(Theme.get_input_style())
        # Set default value to match existing config
        default_greenluma_path = str(Path(__file__).parent / "GreenLuma")
        self.greenluma_path_input.setText(default_greenluma_path)
        path_layout.addWidget(self.greenluma_path_input, 1)
        
        browse_button = AnimatedButton("Browse")
        browse_button.clicked.connect(self.browse_greenluma_path)
        path_layout.addWidget(browse_button)
        
        input_layout.addLayout(path_layout)
        layout.addWidget(input_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        back_button = AnimatedButton("← Back")
        back_button.clicked.connect(lambda: self.setCurrentIndex(1))
        button_layout.addWidget(back_button)
        
        button_layout.addStretch()
        
        finish_button = AnimatedButton("Complete Setup →")
        finish_button.clicked.connect(self.save_greenluma_and_finish)
        button_layout.addWidget(finish_button)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        return page
        
    def create_completion_page(self):
        """Create setup completion page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(30)
        
        # Success icon - keep this one as it looks good
        success_icon = QLabel("🎉")
        success_icon.setStyleSheet("font-size: 72px;")
        success_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(success_icon)
        
        # Title
        title = QLabel("Setup Complete!")
        title.setStyleSheet(f"""
            QLabel {{
                color: {Theme.GOLD_PRIMARY};
                font-size: 32px;
                font-weight: bold;
            }}
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Description
        description = QLabel("""
        Congratulations! SuperSexySteam is now configured and ready to use.
        
        You can now:
        • Drag and drop .lua and .manifest files to install games
        • Search for Steam games and copy AppIDs
        • View and manage your installed games
        • Launch Steam with enhanced features
        """)
        description.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_PRIMARY};
                font-size: 16px;
                line-height: 1.6;
                padding: 20px;
                background: {Theme.SURFACE_DARK};
                border-radius: 12px;
            }}
        """)
        description.setAlignment(Qt.AlignmentFlag.AlignLeft)
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Launch button
        launch_button = AnimatedButton("Launch SuperSexySteam")
        launch_button.clicked.connect(self.complete_setup)
        layout.addWidget(launch_button)
        
        layout.addStretch()
        return page
        
    def browse_steam_path(self):
        """Browse for Steam installation directory"""
        path = QFileDialog.getExistingDirectory(self, "Select Steam Installation Directory")
        if path:
            self.steam_path_input.setText(path)
            
    def browse_greenluma_path(self):
        """Browse for GreenLuma directory"""
        path = QFileDialog.getExistingDirectory(self, "Select GreenLuma Directory")
        if path:
            self.greenluma_path_input.setText(path)
            
    def save_steam_path_and_continue(self):
        """Save steam path and continue to next page"""
        self.setup_data['steam_path'] = self.steam_path_input.text()
        self.setCurrentIndex(2)
        
    def save_greenluma_and_finish(self):
        """Save greenluma path and go to completion page"""
        self.setup_data['greenluma_path'] = self.greenluma_path_input.text()
        self.setCurrentIndex(3)
        
    def complete_setup(self):
        """Complete the setup process"""
        self.setup_completed.emit(self.setup_data)


class MainInterface(QWidget):
    """Main application interface"""
    
    def __init__(self, logic: SuperSexySteamLogic, status_bar, parent=None):
        super().__init__(parent)
        self.logic = logic
        self.status_bar = status_bar
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header with logo and image
        header_widget = self.create_header_widget()
        layout.addWidget(header_widget)
        
        # Drop zone
        self.drop_zone = DropZone()
        self.drop_zone.setMinimumHeight(200)
        layout.addWidget(self.drop_zone, 1)
        
        # Secondary buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.installed_button = AnimatedButton("Installed Games")
        self.installed_button.setStyleSheet(Theme.get_button_style(
            f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Theme.ACCENT_GREEN}, stop:1 #2e7d32)", 
            Theme.TEXT_PRIMARY
        ))
        button_layout.addWidget(self.installed_button)
        
        self.clear_button = AnimatedButton("Clear Data")
        self.clear_button.setStyleSheet(Theme.get_button_style(
            f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Theme.ACCENT_ORANGE}, stop:1 #e65100)", 
            Theme.TEXT_PRIMARY
        ))
        button_layout.addWidget(self.clear_button)
        
        self.achievements_button = AnimatedButton("Generate Achievements")
        self.achievements_button.setStyleSheet(Theme.get_button_style(
            f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Theme.ACCENT_PURPLE}, stop:1 #6a1b9a)", 
            Theme.TEXT_PRIMARY
        ))
        button_layout.addWidget(self.achievements_button)
        
        self.fix_steam_button = AnimatedButton("Fix Steam")
        self.fix_steam_button.setStyleSheet(Theme.get_button_style(
            f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Theme.ACCENT_BLUE}, stop:1 #1565c0)", 
            Theme.TEXT_PRIMARY
        ))
        button_layout.addWidget(self.fix_steam_button)
        
        layout.addLayout(button_layout)
        
    def create_header_widget(self):
        """Create header widget with image or fallback text"""
        try:
            # Try to load header.png
            header_path = Path(__file__).parent / "header.png"
            if header_path.exists():
                # Load and resize the header image
                pixmap = QPixmap(str(header_path))
                
                # Scale the image to a reasonable size while maintaining aspect ratio
                max_width = 500
                if pixmap.width() > max_width:
                    pixmap = pixmap.scaledToWidth(max_width, Qt.TransformationMode.SmoothTransformation)
                
                header_label = QLabel()
                header_label.setPixmap(pixmap)
                header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                header_label.setStyleSheet("background: transparent;")
                return header_label
            else:
                # Fallback to text header
                header_label = QLabel("SuperSexySteam")
                header_label.setStyleSheet(f"""
                    QLabel {{
                        color: {Theme.GOLD_PRIMARY};
                        font-size: 36px;
                        font-weight: bold;
                        background: transparent;
                        padding: 10px;
                    }}
                """)
                header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                return header_label
                
        except Exception as e:
            logger.warning(f"Failed to load header image: {e}")
            # Fallback to text header
            header_label = QLabel("SuperSexySteam")
            header_label.setStyleSheet(f"""
                QLabel {{
                    color: {Theme.GOLD_PRIMARY};
                    font-size: 36px;
                    font-weight: bold;
                    background: transparent;
                    padding: 10px;
                }}
            """)
            header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            return header_label
        
    def setup_connections(self):
        """Setup signal connections"""
        self.drop_zone.files_dropped.connect(self.handle_files_dropped)
        self.installed_button.clicked.connect(self.open_installed_games_dialog)
        self.clear_button.clicked.connect(self.clear_data)
        self.achievements_button.clicked.connect(self.run_achievements)
        self.fix_steam_button.clicked.connect(self.fix_steam_offline)
        
    def handle_files_dropped(self, files):
        """Handle dropped files"""
        logger.info(f"Files dropped: {len(files)} files")
        self.status_bar.update_status("Processing dropped files...", "loading", True)
        
        # Force UI update before starting processing
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
        
        # Add a small delay to ensure the status is visible
        import time
        time.sleep(0.1)  # 100ms delay to ensure UI updates
        
        # Process files using app logic
        result = self.logic.process_game_installation(files)
        
        if result['success'] == "waiting":
            # Installation is paused for depot selection
            app_id = result['app_id']
            
            # Update status to show waiting for user input BEFORE showing popup
            self.status_bar.update_status(f"Depot selection required for AppID {app_id}", "info")
            QApplication.processEvents()
            
            # Check if depot popup should be shown
            if result.get('show_depot_popup', False):
                popup_data = result['popup_data']
                self.show_depot_selection_popup(
                    popup_data['app_id'],
                    popup_data['game_name'],
                    popup_data['depots'],
                    popup_data['destination_directory']
                )
            else:
                # No popup needed, just waiting
                self.status_bar.update_status(f"Awaiting depot selection for AppID {app_id}...", "loading")
            
        elif result['success']:
            action_verb = result['action_verb']
            app_id = result['app_id']
            stats = result['stats']
            
            # Build comprehensive success message
            success_parts = [f"{stats['depots_processed']} depots"]
            
            if stats.get('manifests_copied', 0) > 0:
                success_parts.append(f"{stats['manifests_copied']} manifests")
                
            if stats.get('steam_manifests_copied', 0) > 0:
                success_parts.append(f"{stats['steam_manifests_copied']} Steam manifests")
                
            if stats.get('steam_lua_copied', False):
                success_parts.append("lua file copied")
            
            success_details = ", ".join(success_parts)
            success_msg = f"{action_verb} AppID {app_id} successfully! ({success_details})"
            self.status_bar.update_status(success_msg, "success")
            
        else:
            error_msg = result.get('error', 'Installation failed')
            if 'errors' in result and result['errors']:
                error_msg = '; '.join(result['errors'])
            self.status_bar.update_status(f"Installation failed: {error_msg}", "error")
            
    def show_depot_selection_popup(self, app_id, game_name, depots, data_folder):
        """Show depot selection popup for optional depot removal"""
        try:
            # Update status to show depot selection is active
            self.status_bar.update_status(f"Select depots to install for {game_name}...", "info")
            
            dialog = DepotSelectionDialog(
                app_id=app_id,
                game_name=game_name,
                depots=depots,
                data_folder=data_folder,
                game_installer=self.logic.game_installer,
                parent=self
            )
            
            # Connect signals
            dialog.depot_deleted.connect(self.on_depot_deleted)
            dialog.installation_completed.connect(self.on_installation_completed)
            
            # Track if we received the completion signal
            self._installation_signal_received = False
            
            def mark_signal_received(result):
                self._installation_signal_received = True
                self.on_installation_completed(result)
            
            dialog.installation_completed.disconnect()  # Remove previous connection
            dialog.installation_completed.connect(mark_signal_received)
            
            # Show the dialog
            result = dialog.exec()
            
            # Check what happened after dialog closes
            if result == 1:  # QDialog.Accepted
                if not self._installation_signal_received:
                    # Dialog was accepted but no signal received - fallback
                    logger.warning(f"Dialog accepted but no installation signal received for AppID {app_id}")
                    self.status_bar.update_status(f"Installation status unknown for AppID {app_id}", "error")
            elif result == 0:  # QDialog.Rejected
                # Installation was cancelled - uninstall the partially installed game
                logger.info(f"Installation cancelled for AppID {app_id}, removing partial installation...")
                self.status_bar.update_status(f"Cancelling installation for AppID {app_id}...", "info")
                
                try:
                    # Call the uninstall method to clean up the partially installed game
                    uninstall_result = self.logic.uninstall_game(app_id)
                    
                    if uninstall_result.get('success', False):
                        logger.info(f"Successfully cleaned up cancelled installation for AppID {app_id}")
                        self.status_bar.update_status(f"Installation cancelled and cleaned up for AppID {app_id}", "success")
                        
                        # Refresh the installed games view to remove it from the list
                        self.installed_games_dialog.load_games() if hasattr(self, 'installed_games_dialog') else None
                    else:
                        error_msg = uninstall_result.get('error', 'Unknown error during cleanup')
                        logger.error(f"Failed to clean up cancelled installation for AppID {app_id}: {error_msg}")
                        self.status_bar.update_status(f"Installation cancelled but cleanup failed for AppID {app_id}", "error")
                        
                except Exception as e:
                    logger.error(f"Exception during installation cleanup for AppID {app_id}: {e}")
                    logger.debug("Installation cleanup exception:", exc_info=True)
                    self.status_bar.update_status(f"Installation cancelled for AppID {app_id}", "error")
            
        except Exception as e:
            logger.error(f"Error showing depot selection popup: {e}")
            logger.debug("Depot popup exception:", exc_info=True)
            self.status_bar.update_status(f"Error showing depot selection: {str(e)}", "error")
    
    def on_depot_deleted(self, app_id, depot_id):
        """Handle depot deletion notification"""
        logger.info(f"Depot {depot_id} was deleted from AppID {app_id}")
        self.status_bar.update_status(f"Depot {depot_id} removed from AppID {app_id}", "success")
    
    def on_installation_completed(self, result):
        """Handle installation completion from depot selection dialog"""
        try:
            app_id = result.get('app_id', 'Unknown')
            success = result.get('success')
            
            logger.debug(f"Installation completion signal received for AppID {app_id}, success: {success}")
            
            if success == 'continuing':
                # Installation is continuing after depot selection
                message = result.get('message', f"Continuing installation for AppID {app_id}...")
                self.status_bar.update_status(message, "loading")
                logger.info(f"Installation continuing for AppID {app_id}")
            elif success:
                # Installation completed successfully
                stats = result.get('stats', {})
                # Build comprehensive success message
                success_parts = [f"{stats.get('depots_processed', 0)} depots"]
                
                if stats.get('manifests_copied', 0) > 0:
                    success_parts.append(f"{stats['manifests_copied']} manifests")
                    
                if stats.get('steam_manifests_copied', 0) > 0:
                    success_parts.append(f"{stats['steam_manifests_copied']} Steam manifests")
                    
                if stats.get('steam_lua_copied', False):
                    success_parts.append("lua file copied")
                
                success_details = ", ".join(success_parts)
                success_msg = f"Installation completed for AppID {app_id}! ({success_details})"
                self.status_bar.update_status(success_msg, "success")
                logger.info(f"Successfully completed installation for AppID {app_id}")
            else:
                # Installation failed
                error_msg = result.get('error_message', 'Installation failed')
                self.status_bar.update_status(f"Installation failed: {error_msg}", "error")
                logger.error(f"Installation failed for AppID {app_id}: {error_msg}")
        except Exception as e:
            logger.error(f"Error handling installation completion: {e}")
            logger.debug("Installation completion handler exception:", exc_info=True)
            self.status_bar.update_status("Installation status update failed", "error")
            
    def launch_steam(self):
        """Launch Steam"""
        self.status_bar.update_status("Launching Steam...", "loading")
        
        result = self.logic.launch_steam()
        
        if result['success']:
            final_message = result['messages'][-1] if result['messages'] else "Steam launched successfully! 🚀"
            self.status_bar.update_status(final_message, "success")
        else:
            error_msg = '; '.join(result['errors']) if result['errors'] else "Failed to launch Steam"
            self.status_bar.update_status(f"Failed to launch Steam: {error_msg}", "error")
            
    def fix_steam_offline(self):
        """Fix Steam offline mode without launching Steam"""
        self.status_bar.update_status("Fixing Steam offline mode...", "loading")
        
        result = self.logic.fix_steam_offline()
        
        if result['success']:
            final_message = result['messages'][-1] if result['messages'] else "Steam offline mode fixed successfully! ✅"
            self.status_bar.update_status(final_message, "success")
        else:
            error_msg = '; '.join(result['errors']) if result['errors'] else "Failed to fix Steam offline mode"
            self.status_bar.update_status(f"Failed to fix Steam offline mode: {error_msg}", "error")
            
    def open_search_dialog(self):
        """Open game search dialog"""
        dialog = SearchDialog(self.logic, self)
        dialog.exec()
        
    def open_installed_games_dialog(self):
        """Open installed games dialog"""
        dialog = InstalledGamesDialog(self.logic, self)
        dialog.exec()
        
    def uninstall_game(self):
        """Uninstall a game"""
        app_id, ok = QInputDialog.getText(self, "Uninstall Game", "Enter AppID to uninstall:")
        
        if ok and app_id.strip():
            self.status_bar.update_status(f"Uninstalling AppID {app_id.strip()}...", "loading")
            
            result = self.logic.uninstall_game(app_id)
            
            if result['success']:
                self.status_bar.update_status(f"AppID {result['app_id']} uninstalled! {result['summary']}", "success")
            else:
                self.status_bar.update_status(f"Uninstallation failed: {result['error']}", "error")
                
    def clear_data(self):
        """Clear all application data"""
        confirmation = ConfirmationOverlay(
            title="Clear All Data",
            message="Are you sure you want to clear all application data?\n\n"
                   "This will remove all installed games and database entries.",
            confirm_text="🗑️ Yes, Clear All",
            cancel_text="✗ Cancel",
            dialog_type="warning",
            parent=self
        )
        
        # Connect the signals
        confirmation.confirmed.connect(self.proceed_with_clear_data)
        # If cancelled, nothing happens
        
        # Show the confirmation dialog
        confirmation.exec()
        
    def proceed_with_clear_data(self):
        """Proceed with clearing all data after confirmation"""
        self.status_bar.update_status("Clearing all data...", "loading")
        
        result = self.logic.clear_all_application_data()
        
        if result['success']:
            self.status_bar.update_status(f"Data cleared! {result['summary']}", "success")
            # Close the application after successfully clearing data
            QApplication.instance().quit()
        else:
            self.status_bar.update_status(f"Failed to clear data: {result['error']}", "error")
    
    def run_achievements(self):
        """Run the achievements.py script"""
        try:
            self.status_bar.update_status("Running achievements script...", "loading")
            self.achievements_button.setEnabled(False)
            self.achievements_button.setText("🔄 Running...")
            
            if getattr(sys, 'frozen', False):
                # Running in a PyInstaller bundle - run in a separate thread with console
                import threading
                import achievements
                
                def run_achievements_with_console():
                    try:
                        # Try to allocate a console window for output
                        try:
                            import ctypes
                            ctypes.windll.kernel32.AllocConsole()
                            
                            # Properly redirect all streams to the new console
                            import sys
                            import os
                            
                            # Open console handles
                            stdin_handle = ctypes.windll.kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE
                            stdout_handle = ctypes.windll.kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
                            stderr_handle = ctypes.windll.kernel32.GetStdHandle(-12)  # STD_ERROR_HANDLE
                            
                            # Redirect streams
                            sys.stdin = open('CONIN$', 'r')
                            sys.stdout = open('CONOUT$', 'w')
                            sys.stderr = open('CONOUT$', 'w')
                            
                            # Also redirect os level file descriptors
                            os.dup2(sys.stdin.fileno(), 0)
                            os.dup2(sys.stdout.fileno(), 1)
                            os.dup2(sys.stderr.fileno(), 2)
                            
                            # Reconfigure logging to use the new console
                            import logging
                            
                            # Remove all existing handlers
                            root_logger = logging.getLogger()
                            for handler in root_logger.handlers[:]:
                                root_logger.removeHandler(handler)
                            
                            # Create a new console handler
                            console_handler = logging.StreamHandler(sys.stdout)
                            formatter = logging.Formatter('%(levelname)s: %(message)s')
                            console_handler.setFormatter(formatter)
                            console_handler.setLevel(logging.INFO)
                            
                            # Add the console handler
                            root_logger.addHandler(console_handler)
                            root_logger.setLevel(logging.INFO)
                            
                        except Exception as console_err:
                            print(f"Warning: Could not allocate console: {console_err}")
                        
                        print("SuperSexySteam - Achievements Generator")
                        print("=" * 50)
                        achievements.main()
                        
                    except Exception as e:
                        print(f"\nError running achievements: {e}")
                        import traceback
                        traceback.print_exc()
                    finally:
                        print("\nAchievements script completed.")
                        
                        # Better input handling that won't block forever or crash main app
                        # Only start auto-close AFTER the script is completely done
                        try:
                            import msvcrt
                            print("Press any key to close this window...")
                            msvcrt.getch()  # Wait for any key press
                        except:
                            try:
                                # Fallback to simple input - no auto-close timer to avoid interrupting
                                print("Press Enter to close this window...")
                                input()
                                    
                            except:
                                # Final fallback - wait longer since script is done
                                import time
                                print("Console will auto-close in 30 seconds if no interaction...")
                                time.sleep(30)
                        
                        # Free the console when done to prevent it from affecting main app
                        try:
                            import ctypes
                            ctypes.windll.kernel32.FreeConsole()
                        except:
                            pass
                
                # Start in separate thread
                achievement_thread = threading.Thread(target=run_achievements_with_console)
                achievement_thread.daemon = True
                achievement_thread.start()
                
                self.status_bar.update_status("Achievements script started in console window", "success")
                logger.info("Achievements script started in separate thread with console")
                
            else:
                # Running from source - use subprocess with new console
                script_dir = Path(__file__).parent
                achievements_script = script_dir / "achievements.py"
                
                if not achievements_script.exists():
                    self.status_bar.update_status("achievements.py script not found!", "error")
                    self.achievements_button.setEnabled(True)
                    self.achievements_button.setText("Generate Achievements")
                    return
                
                # Run the achievements script in new console
                process = subprocess.Popen(
                    [sys.executable, str(achievements_script)],
                    cwd=str(script_dir),
                    creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
                )
                
                self.status_bar.update_status("Achievements script launched in new console window", "success")
                
        except Exception as e:
            logger.error(f"Failed to run achievements script: {e}")
            self.status_bar.update_status(f"Failed to run achievements script: {str(e)}", "error")
        finally:
            # Re-enable the button
            self.achievements_button.setEnabled(True)
            self.achievements_button.setText("Generate Achievements")


class SuperSexySteamApp(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.logic = None
        self.setup_ui()
        self.setup_window()
        self.start_setup_or_main()
        
    def setup_window(self):
        """Setup main window properties"""
        self.setWindowTitle("SuperSexySteam")
        self.setMinimumSize(700, 500)
        self.resize(800, 600)
        
        # Set window icon
        try:
            icon_path = Path(__file__).parent / "sss.ico"
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
            else:
                # Try alternative icon paths
                alt_paths = ["icon.ico", "steam.ico", "refresh.ico"]
                for alt_path in alt_paths:
                    alt_icon_path = Path(__file__).parent / alt_path
                    if alt_icon_path.exists():
                        self.setWindowIcon(QIcon(str(alt_icon_path)))
                        break
        except Exception as e:
            logger.warning(f"Failed to load window icon: {e}")
        
        # Center window
        self.center_window()
        
    def center_window(self):
        """Center the window on screen"""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.geometry()
            window_geometry = self.frameGeometry()
            center_point = screen_geometry.center()
            window_geometry.moveCenter(center_point)
            self.move(window_geometry.topLeft())
            
    def setup_ui(self):
        """Setup main UI components"""
        # Set dark theme
        self.setStyleSheet(f"""
            QMainWindow {{
                background: {Theme.MAIN_GRADIENT};
                color: {Theme.TEXT_PRIMARY};
            }}
        """)
        
        # Main widget container
        self.main_widget = QStackedWidget()
        self.setCentralWidget(self.main_widget)
        
        # Status bar
        self.status_bar = StatusBar()
        self.setStatusBar(self.status_bar)
        
    def start_setup_or_main(self):
        """Start setup process or main interface"""
        # Try to load existing configuration
        config = SuperSexySteamLogic.load_configuration()
        
        if config is None:
            # Show first-time setup
            self.show_setup()
        else:
            # Initialize logic and show main interface
            self.logic = SuperSexySteamLogic(config)
            self.show_main_interface()
            
    def show_setup(self):
        """Show first-time setup interface"""
        self.setup_widget = FirstTimeSetupWidget()
        self.setup_widget.setup_completed.connect(self.on_setup_completed)
        self.main_widget.addWidget(self.setup_widget)
        self.main_widget.setCurrentWidget(self.setup_widget)
        
    def on_setup_completed(self, setup_data):
        """Handle setup completion"""
        try:
            # Use the proper create_configuration method which includes DLLInjector.ini setup
            steam_path = setup_data.get('steam_path', '')
            greenluma_path = setup_data.get('greenluma_path', '')
            
            # Import here to avoid circular imports
            from app_logic import SuperSexySteamLogic
            config_parser = SuperSexySteamLogic.create_configuration(steam_path, greenluma_path)
                
            # Initialize logic and show main interface
            self.logic = SuperSexySteamLogic(config_parser)
            self.show_main_interface()
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            error_dialog = ConfirmationOverlay(
                title="Setup Error",
                message=f"Failed to save configuration:\n\n{e}",
                confirm_text="OK",
                cancel_text="",
                dialog_type="error",
                parent=self
            )
            error_dialog.exec()
            
    def show_main_interface(self):
        """Show main application interface"""
        self.main_interface = MainInterface(self.logic, self.status_bar)
        self.main_widget.addWidget(self.main_interface)
        self.main_widget.setCurrentWidget(self.main_interface)


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("SuperSexySteam")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("SuperSexySteam")
    
    # Set application font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Create and show main window
    window = SuperSexySteamApp()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()