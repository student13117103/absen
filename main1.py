#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tampilan utama sistem absensi dengan PyQt5.
"""

import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, 
                            QWidget, QVBoxLayout, QHBoxLayout, QFrame, 
                            QGridLayout, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QRect
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPalette, QBrush, QColor

class AttendanceSystemUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Setup UI
        self.init_ui()
        
        # Start timer for clock update
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)  # Update every second
        
        # Drawer state
        self.drawer_open = False
        
    def init_ui(self):
        """Initialize the user interface"""
        # Set window properties
        self.setWindowTitle("Sistem Absensi dengan Pengenalan Wajah")
        self.showFullScreen()
        
        # Create main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QGridLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Set background image
        self.set_background()
        
        # Create top bar for clock and login button
        self.create_top_bar()
        
        # Create drawer
        self.create_drawer()
        
    def set_background(self):
        """Set the background image for the application"""
        # Check if background image exists
        bg_path = "assets/background.jpg"
        if os.path.exists(bg_path):
            try:
                # Create a full-screen background label
                self.bg_label = QLabel(self.central_widget)
                self.bg_label.setMinimumSize(1, 1)
                self.bg_label.lower()  # Send to back
                
                # Load pixmap
                self.bg_pixmap = QPixmap(bg_path)
                if not self.bg_pixmap.isNull():
                    # Set to fill entire window
                    self.bg_label.setScaledContents(True)  # Stretch to fill
                    self.resize_background()  # Initial sizing
                else:
                    raise Exception("Failed to load background image")
            except Exception as e:
                print(f"Error setting background with QLabel: {e}")
                # Fallback to a solid color background
                self.central_widget.setStyleSheet("""
                    background-color: #1e272e;
                """)
        else:
            # Fallback to a gradient background if image doesn't exist
            self.central_widget.setStyleSheet("""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #2c3e50, stop:1 #3498db);
            """)
            print(f"Warning: Background image not found at {bg_path}")
            
    def resize_background(self):
        """Resize background image to fill the entire window"""
        if hasattr(self, 'bg_label'):
            # Make the background label fill the entire central widget
            self.bg_label.setGeometry(0, 0, self.width(), self.height())
            
            # If we have a pixmap, update it
            if hasattr(self, 'bg_pixmap') and not self.bg_pixmap.isNull():
                self.bg_label.setPixmap(self.bg_pixmap)
            
    def create_top_bar(self):
        """Create the top bar with clock and login button"""
        # Top bar container
        self.top_bar = QWidget()
        self.top_bar.setMinimumHeight(80)
        self.top_bar.setMaximumHeight(80)
        self.top_bar.setStyleSheet("""
            background-color: rgba(0, 0, 0, 50%);
        """)
        
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(20, 0, 20, 0)
        
        # Drawer toggle button (left side)
        self.drawer_toggle_btn = QPushButton()
        self.drawer_toggle_btn.setIcon(QIcon("assets/menu.png"))  # Ensure you have this icon
        self.drawer_toggle_btn.setIconSize(QSize(32, 32))
        self.drawer_toggle_btn.setFlat(True)
        self.drawer_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 20%);
            }
        """)
        self.drawer_toggle_btn.clicked.connect(self.toggle_drawer)
        top_layout.addWidget(self.drawer_toggle_btn)
        
        # Add spacer
        top_layout.addStretch()
        
        # Clock and date in center
        self.clock_container = QWidget()
        clock_layout = QVBoxLayout(self.clock_container)
        clock_layout.setAlignment(Qt.AlignCenter)
        
        # Time label
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("""
            color: white;
            font-size: 32px;
            font-weight: bold;
        """)
        
        # Date label
        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignCenter)
        self.date_label.setStyleSheet("""
            color: white;
            font-size: 16px;
        """)
        
        clock_layout.addWidget(self.time_label)
        clock_layout.addWidget(self.date_label)
        
        top_layout.addWidget(self.clock_container)
        
        # Add spacer
        top_layout.addStretch()
        
        # Login button (right side)
        self.login_btn = QPushButton("Login")
        self.login_btn.setMinimumSize(100, 40)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c6ea4;
            }
        """)
        top_layout.addWidget(self.login_btn)
        
        # Add top bar to main layout
        self.main_layout.addWidget(self.top_bar, 0, 0, 1, 2)
        
        # Initial clock update
        self.update_clock()
        
    def create_drawer(self):
        """Create the drawer panel that slides from left"""
        # Drawer container
        self.drawer = QWidget(self)
        self.drawer.setMinimumWidth(300)
        self.drawer.setMaximumWidth(300)
        self.drawer.setStyleSheet("""
            background-color: rgba(44, 62, 80, 95%);
            border-right: 1px solid rgba(255, 255, 255, 30%);
        """)
        
        # Set initial position off-screen
        self.drawer.setGeometry(-300, 80, 300, self.height() - 80)
        
        # Drawer layout
        drawer_layout = QVBoxLayout(self.drawer)
        drawer_layout.setContentsMargins(15, 20, 15, 20)
        drawer_layout.setSpacing(20)
        
        # User info box
        self.user_box = QFrame()
        self.user_box.setFrameShape(QFrame.StyledPanel)
        self.user_box.setStyleSheet("""
            background-color: rgba(255, 255, 255, 10%);
            border-radius: 10px;
            padding: 10px;
        """)
        
        user_layout = QVBoxLayout(self.user_box)
        
        # User avatar/icon
        user_icon_layout = QHBoxLayout()
        user_icon_layout.setAlignment(Qt.AlignCenter)
        
        user_icon = QLabel()
        user_icon.setPixmap(QPixmap("assets/user.png").scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        user_icon_layout.addWidget(user_icon)
        user_layout.addLayout(user_icon_layout)
        
        # Username and ID
        self.username_label = QLabel("Username")
        self.username_label.setAlignment(Qt.AlignCenter)
        self.username_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        
        self.user_id_label = QLabel("ID")
        self.user_id_label.setAlignment(Qt.AlignCenter)
        self.user_id_label.setStyleSheet("color: rgba(255, 255, 255, 70%); font-size: 14px;")
        
        user_layout.addWidget(self.username_label)
        user_layout.addWidget(self.user_id_label)
        
        drawer_layout.addWidget(self.user_box)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: rgba(255, 255, 255, 20%);")
        drawer_layout.addWidget(separator)
        
        # Menu buttons
        self.create_menu_button("Dosen", "assets/teacher.png", drawer_layout)
        self.create_menu_button("Kelas", "assets/classroom.png", drawer_layout)
        
        drawer_layout.addStretch()  # Push everything to the top
        
    def create_menu_button(self, text, icon_path, parent_layout):
        """Create a button for the drawer menu"""
        button = QPushButton(text)
        button.setMinimumHeight(50)
        
        # Check if icon exists
        if os.path.exists(icon_path):
            button.setIcon(QIcon(icon_path))
            button.setIconSize(QSize(24, 24))
        
        button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 10%);
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                text-align: left;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 20%);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 30%);
            }
        """)
        
        parent_layout.addWidget(button)
        return button
        
    def update_clock(self):
        """Update the clock and date display"""
        now = datetime.now()
        
        # Update time
        time_str = now.strftime("%H:%M:%S")
        self.time_label.setText(time_str)
        
        # Update date
        date_str = now.strftime("%A, %d %B %Y")
        self.date_label.setText(date_str)
        
    def toggle_drawer(self):
        """Toggle the drawer open/closed state"""
        target_x = 0 if not self.drawer_open else -300
        
        # Create animation
        self.animation = QPropertyAnimation(self.drawer, b"geometry")
        self.animation.setDuration(300)  # Animation duration in ms
        
        current_geometry = self.drawer.geometry()
        self.animation.setStartValue(current_geometry)
        self.animation.setEndValue(QRect(target_x, 80, 300, self.height() - 80))
        
        self.animation.start()
        
        # Update state
        self.drawer_open = not self.drawer_open
        
    def resizeEvent(self, event):
        """Handle window resize events"""
        super().resizeEvent(event)
        
        # Resize background image
        if hasattr(self, 'bg_label'):
            self.resize_background()
        
        # Update drawer height when window is resized
        if hasattr(self, 'drawer'):
            current_geometry = self.drawer.geometry()
            x = current_geometry.x()
            self.drawer.setGeometry(x, 80, 300, self.height() - 80)
        
def main():
    app = QApplication(sys.argv)
    window = AttendanceSystemUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()