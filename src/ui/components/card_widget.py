"""
Custom CardWidget component.
"""

from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap, QPixmapCache
from PySide6.QtCore import Qt, QPropertyAnimation, QTimer
from src.game.deck import Card
from src.utils.constants import CARD_ASSET_PATH, CARD_WIDTH, CARD_HEIGHT
from typing import Optional

# --- NEW IMPORT ---
from src.utils.animations import create_flip_animation
# --- END IMPORT ---

# Your cache-disabling code
QPixmapCache.setCacheLimit(1)


class CardWidget(QLabel):
    def __init__(self, card: Optional[Card] = None, parent=None):
        super().__init__(parent)
        self.card = card
        self.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
        self.is_face_up = False # Track state
        self.animation = None # To hold the animation

        # Your force-load logic
        back_path = f"{CARD_ASSET_PATH}card_back.png"
        self.back_pixmap = QPixmap(back_path)
        if self.back_pixmap.isNull():
            print(f"Failed to load: {back_path}")
        self.back_pixmap = self.back_pixmap.scaled(
            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

        self.front_pixmap = None
        if self.card:
            self.load_front_pixmap() # Load front pixmap

        self.show_back()

    def load_front_pixmap(self):
        """Helper to load the front pixmap."""
        if not self.card:
            return
        image_file = f"{CARD_ASSET_PATH}{self.card.image_name}"
        self.front_pixmap = QPixmap(image_file)
        if self.front_pixmap.isNull():
            print(f"Failed to load: {image_file}")
        self.front_pixmap = self.front_pixmap.scaled(
            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

    def set_card(self, card: Card):
        self.card = card
        self.load_front_pixmap()

    def show_back(self):
        self.setPixmap(self.back_pixmap)
        self.is_face_up = False

    def show_front(self):
        if self.front_pixmap and not self.front_pixmap.isNull():
            self.setPixmap(self.front_pixmap)
        else:
            self.setText(str(self.card) if self.card else "?")
        self.is_face_up = True

    # --- NEW FLIP ANIMATION METHOD ---
    def flip(self):
        """
        Animates a flip from back-to-front.
        Does nothing if the card is already face-up.
        """
        if self.is_face_up or not self.front_pixmap:
            return

        # 1. Create the animation
        self.animation = create_flip_animation(self)
        
        # 2. Connect the halfway point (at 200ms) to the
        #    function that actually switches the image.
        QTimer.singleShot(200, self.show_front)
        
        # 3. Start the animation
        self.animation.start(QPropertyAnimation.DeleteWhenStopped)
    # --- END NEW METHOD ---

    def __del__(self):
        if self.front_pixmap and not self.front_pixmap.isNull():
            self.front_pixmap = QPixmap()
        if self.back_pixmap and not self.back_pixmap.isNull():
            self.back_pixmap = QPixmap()