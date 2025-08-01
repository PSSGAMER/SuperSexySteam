# SuperSexySteam_PySide6.py
#
# A modern, sleek, and powerful GUI for SuperSexySteam using PySide6
# Features smooth animations, gradients, and a sophisticated interface
# with a focus on user experience and performance.

import sys
import os
import json
import logging
import configparser
from pathlib import Path
from typing import Dict, List, Any, Optional

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

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(name)s] [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


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
        
    def clear_games(self):
        """Clear all games from the layout"""
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
        self.refresh_button.setText("🔄 Refresh")
        
        if result['success']:
            self.status_label.setText(f"Successfully uninstalled {game_name}")
            self.status_label.setStyleSheet(f"color: {Theme.ACCENT_GREEN}; font-size: 14px;")
            
            # Reload games list
            QTimer.singleShot(1000, self.load_games)
        else:
            self.status_label.setText(f"Failed to uninstall {game_name}: {result['error']}")
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
        
    def create_welcome_page(self):
        """Create welcome page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(30)
        
        # Logo/Title
        title = QLabel("SuperSexySteam")
        title.setStyleSheet(f"""
            QLabel {{
                color: {Theme.GOLD_PRIMARY};
                font-size: 48px;
                font-weight: bold;
            }}
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
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
        
        # Main action button
        self.run_steam_button = AnimatedButton("🚀 LAUNCH STEAM")
        # Try to set Steam icon
        try:
            steam_icon_path = Path(__file__).parent / "steam.ico"
            if steam_icon_path.exists():
                self.run_steam_button.setIcon(QIcon(str(steam_icon_path)))
                self.run_steam_button.setText("LAUNCH STEAM")
        except Exception:
            pass
        
        self.run_steam_button.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.GOLD_GRADIENT};
                color: {Theme.PRIMARY_DARK};
                border: none;
                border-radius: 12px;
                padding: 20px 40px;
                font-weight: bold;
                font-size: 18px;
                min-height: 20px;
                outline: none;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Theme.GOLD_SECONDARY}, stop:1 {Theme.GOLD_PRIMARY});
            }}
            QPushButton:focus {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Theme.GOLD_SECONDARY}, stop:1 {Theme.GOLD_PRIMARY});
                border: 2px solid {Theme.GOLD_PRIMARY};
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Theme.GOLD_DARK}, stop:1 {Theme.GOLD_PRIMARY});
            }}
        """)
        layout.addWidget(self.run_steam_button)
        
        # Secondary buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.search_button = AnimatedButton("Search Games")
        self.search_button.setStyleSheet(Theme.get_button_style(Theme.BLUE_GRADIENT, Theme.TEXT_PRIMARY))
        button_layout.addWidget(self.search_button)
        
        self.installed_button = AnimatedButton("Installed Games")
        self.installed_button.setStyleSheet(Theme.get_button_style(
            f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Theme.ACCENT_GREEN}, stop:1 #2e7d32)", 
            Theme.TEXT_PRIMARY
        ))
        button_layout.addWidget(self.installed_button)
        
        self.uninstall_button = AnimatedButton("Uninstall Game")
        self.uninstall_button.setStyleSheet(Theme.get_button_style(
            f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Theme.ACCENT_RED}, stop:1 #c62828)", 
            Theme.TEXT_PRIMARY
        ))
        button_layout.addWidget(self.uninstall_button)
        
        self.clear_button = AnimatedButton("Clear Data")
        self.clear_button.setStyleSheet(Theme.get_button_style(
            f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Theme.ACCENT_ORANGE}, stop:1 #e65100)", 
            Theme.TEXT_PRIMARY
        ))
        button_layout.addWidget(self.clear_button)
        
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
        self.run_steam_button.clicked.connect(self.launch_steam)
        self.search_button.clicked.connect(self.open_search_dialog)
        self.installed_button.clicked.connect(self.open_installed_games_dialog)
        self.uninstall_button.clicked.connect(self.uninstall_game)
        self.clear_button.clicked.connect(self.clear_data)
        
    def handle_files_dropped(self, files):
        """Handle dropped files"""
        self.status_bar.update_status("Processing dropped files...", "loading", True)
        
        # Process files using app logic
        result = self.logic.process_game_installation(files)
        
        if result['success']:
            action_verb = result['action_verb']
            app_id = result['app_id']
            stats = result['stats']
            success_msg = f"{action_verb} AppID {app_id} successfully! ({stats['depots_processed']} depots, {stats['manifests_copied']} manifests)"
            self.status_bar.update_status(success_msg, "success")
        else:
            error_msg = result.get('error', 'Installation failed')
            if 'errors' in result and result['errors']:
                error_msg = '; '.join(result['errors'])
            self.status_bar.update_status(f"Installation failed: {error_msg}", "error")
            
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
        else:
            self.status_bar.update_status(f"Failed to clear data: {result['error']}", "error")


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