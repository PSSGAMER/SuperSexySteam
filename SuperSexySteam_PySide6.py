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
    QFileDialog, QMessageBox, QInputDialog, QComboBox, QStatusBar
)
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QThread, 
    Signal, QSize, QPoint, QParallelAnimationGroup, QSequentialAnimationGroup
)
from PySide6.QtGui import (
    QPainter, QLinearGradient, QRadialGradient, QColor, QPen, QBrush,
    QFont, QFontMetrics, QPalette, QPixmap, QIcon, QMovie, QTransform
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
        """Get modern button styling with gradients and hover effects"""
        if gradient_color is None:
            gradient_color = Theme.GOLD_GRADIENT
        if text_color is None:
            text_color = Theme.PRIMARY_DARK
            
        return f"""
        QPushButton {{
            background: {gradient_color};
            color: {text_color};
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: bold;
            font-size: 14px;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Theme.GOLD_SECONDARY}, stop:1 {Theme.GOLD_PRIMARY});
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
    """Custom button with smooth hover animations"""
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.default_style = Theme.get_button_style()
        self.setStyleSheet(self.default_style)
        
        # Animation setup
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(Theme.HOVER_ANIMATION_DURATION)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.original_geometry = None
        
    def enterEvent(self, event):
        """Animate button on hover"""
        if self.original_geometry is None:
            self.original_geometry = self.geometry()
        
        # Slightly grow the button
        new_geometry = QRect(
            self.original_geometry.x() - 2,
            self.original_geometry.y() - 2,
            self.original_geometry.width() + 4,
            self.original_geometry.height() + 4
        )
        
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(new_geometry)
        self.animation.start()
        
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Animate button when hover ends"""
        if self.original_geometry:
            self.animation.setStartValue(self.geometry())
            self.animation.setEndValue(self.original_geometry)
            self.animation.start()
        
        super().leaveEvent(event)


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


class StatsWidget(GradientFrame):
    """Animated statistics display widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent, [Theme.SURFACE_DARK, Theme.TERTIARY_DARK])
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Database Statistics")
        title.setStyleSheet(f"""
            QLabel {{
                color: {Theme.GOLD_PRIMARY};
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 10px;
            }}
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Stats container
        stats_layout = QGridLayout()
        
        # Create stat items
        self.total_games_label = self.create_stat_item("Games", "0")
        self.total_depots_label = self.create_stat_item("Depots", "0")
        self.total_manifests_label = self.create_stat_item("Manifests", "0")
        self.database_size_label = self.create_stat_item("Database Size", "0 KB")
        
        # Add to grid
        stats_layout.addWidget(self.total_games_label, 0, 0)
        stats_layout.addWidget(self.total_depots_label, 0, 1)
        stats_layout.addWidget(self.total_manifests_label, 1, 0)
        stats_layout.addWidget(self.database_size_label, 1, 1)
        
        layout.addLayout(stats_layout)
        
    def create_stat_item(self, label_text, value_text):
        """Create a single statistic item"""
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 {Theme.TERTIARY_DARK}, 
                    stop:1 {Theme.SURFACE_DARK});
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Label
        label = QLabel(label_text)
        label.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_SECONDARY};
                font-size: 12px;
                font-weight: normal;
            }}
        """)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Value
        value = QLabel(value_text)
        value.setStyleSheet(f"""
            QLabel {{
                color: {Theme.TEXT_PRIMARY};
                font-size: 16px;
                font-weight: bold;
            }}
        """)
        value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(label)
        layout.addWidget(value)
        
        # Store value label for updates
        container.value_label = value
        
        return container
        
    def update_stats(self, stats_data):
        """Update statistics with animation"""
        if 'total_games' in stats_data:
            self.total_games_label.value_label.setText(str(stats_data['total_games']))
        if 'total_depots' in stats_data:
            self.total_depots_label.value_label.setText(str(stats_data['total_depots']))
        if 'total_manifests' in stats_data:
            self.total_manifests_label.value_label.setText(str(stats_data['total_manifests']))
        if 'database_size_mb' in stats_data:
            size_text = f"{stats_data['database_size_mb']:.2f} MB"
            self.database_size_label.value_label.setText(size_text)


class DropZone(GradientFrame):
    """Modern drag-and-drop zone with animations"""
    
    files_dropped = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent, [Theme.SECONDARY_DARK, Theme.TERTIARY_DARK])
        self.setAcceptDrops(True)
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
            self.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 {Theme.GOLD_PRIMARY}33, 
                        stop:1 {Theme.GOLD_DARK}33);
                    border: 2px dashed {Theme.GOLD_PRIMARY};
                    border-radius: 12px;
                }}
            """)
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet("")
        
    def dropEvent(self, event):
        self.setStyleSheet("")
        if event.mimeData().hasUrls():
            files = [url.toLocalFile() for url in event.mimeData().urls()]
            self.files_dropped.emit(files)
            event.acceptProposedAction()


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
        
        # Depot cache page
        depot_page = self.create_depot_cache_page()
        self.addWidget(depot_page)
        
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
        
    def create_depot_cache_page(self):
        """Create depot cache path configuration page"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(30)
        
        # Title
        title = QLabel("Configure Depot Cache")
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
        label = QLabel("Depot Cache Directory:")
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
        
        self.depot_cache_input = QLineEdit()
        self.depot_cache_input.setPlaceholderText("C:\\Program Files (x86)\\Steam\\depotcache")
        self.depot_cache_input.setStyleSheet(Theme.get_input_style())
        path_layout.addWidget(self.depot_cache_input, 1)
        
        browse_button = AnimatedButton("Browse")
        browse_button.clicked.connect(self.browse_depot_cache_path)
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
        finish_button.clicked.connect(self.save_depot_cache_and_finish)
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
            
    def browse_depot_cache_path(self):
        """Browse for depot cache directory"""
        path = QFileDialog.getExistingDirectory(self, "Select Depot Cache Directory")
        if path:
            self.depot_cache_input.setText(path)
            
    def save_steam_path_and_continue(self):
        """Save steam path and continue to next page"""
        self.setup_data['steam_path'] = self.steam_path_input.text()
        
        # Auto-populate depot cache if empty
        if not self.depot_cache_input.text():
            steam_path = self.steam_path_input.text()
            if steam_path:
                depot_cache = os.path.join(steam_path, "depotcache")
                self.depot_cache_input.setText(depot_cache)
        
        self.setCurrentIndex(2)
        
    def save_depot_cache_and_finish(self):
        """Save depot cache path and go to completion page"""
        self.setup_data['depot_cache_path'] = self.depot_cache_input.text()
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
        self.update_stats()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header with logo and image
        header_widget = self.create_header_widget()
        layout.addWidget(header_widget)
        
        # Stats widget
        self.stats_widget = StatsWidget()
        layout.addWidget(self.stats_widget)
        
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
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Theme.GOLD_SECONDARY}, stop:1 {Theme.GOLD_PRIMARY});
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {Theme.GOLD_DARK}, stop:1 {Theme.GOLD_PRIMARY});
            }}
        """)
        layout.addWidget(self.run_steam_button)
        
        # Secondary buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.refresh_button = AnimatedButton("🔄 Refresh")
        # Try to set refresh icon
        try:
            refresh_icon_path = Path(__file__).parent / "refresh.ico"
            if refresh_icon_path.exists():
                self.refresh_button.setIcon(QIcon(str(refresh_icon_path)))
                self.refresh_button.setText("Refresh")
        except Exception:
            pass
        
        self.refresh_button.setStyleSheet(Theme.get_button_style(Theme.BLUE_GRADIENT, Theme.TEXT_PRIMARY))
        button_layout.addWidget(self.refresh_button)
        
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
        self.refresh_button.clicked.connect(self.update_stats)
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
            self.update_stats()
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
            
    def update_stats(self):
        """Update database statistics"""
        result = self.logic.get_database_stats()
        if result['success']:
            self.stats_widget.update_stats(result['stats'])
            self.status_bar.update_status("Statistics updated successfully", "success")
        else:
            self.status_bar.update_status("Failed to update statistics", "error")
            
    def open_search_dialog(self):
        """Open game search dialog"""
        from search_dialog import SearchDialog
        dialog = SearchDialog(self.logic, self)
        dialog.exec()
        
    def open_installed_games_dialog(self):
        """Open installed games dialog"""
        from installed_games_dialog import InstalledGamesDialog
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
                self.update_stats()
            else:
                self.status_bar.update_status(f"Uninstallation failed: {result['error']}", "error")
                
    def clear_data(self):
        """Clear all application data"""
        reply = QMessageBox.question(
            self, 
            "Clear All Data", 
            "Are you sure you want to clear all application data?\n\nThis will remove all installed games and database entries.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.status_bar.update_status("Clearing all data...", "loading")
            
            result = self.logic.clear_all_application_data()
            
            if result['success']:
                self.status_bar.update_status(f"Data cleared! {result['summary']}", "success")
                self.update_stats()
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
        self.setMinimumSize(900, 700)
        self.resize(1000, 800)
        
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
        # Save configuration
        config = {
            'steam_path': setup_data.get('steam_path', ''),
            'depot_cache_path': setup_data.get('depot_cache_path', '')
        }
        
        # Create config.ini
        try:
            config_path = Path(__file__).parent / "config.ini"
            config_parser = configparser.ConfigParser()
            config_parser['PATHS'] = config
            
            with open(config_path, 'w') as config_file:
                config_parser.write(config_file)
                
            # Initialize logic and show main interface
            self.logic = SuperSexySteamLogic(config)
            self.show_main_interface()
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            QMessageBox.critical(self, "Setup Error", f"Failed to save configuration: {e}")
            
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
