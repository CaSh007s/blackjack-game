"""
Animation factory for creating high-quality, reusable
QPropertyAnimations for the game.
"""

from PySide6.QtCore import (
    QPropertyAnimation, QRect, QParallelAnimationGroup, 
    QEasingCurve, QPoint
)
from PySide6.QtWidgets import QWidget

def create_flip_animation(widget: QWidget) -> QPropertyAnimation:
    """
    Creates a 3D-style flip animation for a card widget.
    """
    anim = QPropertyAnimation(widget, b"geometry")
    anim.setDuration(400) # 400ms for the total flip
    
    start_rect = widget.geometry()
    mid_rect = QRect(
        start_rect.x() + start_rect.width() // 2,
        start_rect.y(),
        0,
        start_rect.height()
    )
    end_rect = start_rect
    
    anim.setEasingCurve(QEasingCurve.InOutQuad)
    anim.setKeyValueAt(0, start_rect)
    anim.setKeyValueAt(0.5, mid_rect)
    anim.setKeyValueAt(1, end_rect)
    
    return anim

# --- NEW FUNCTION ---
def create_deal_animation(
    widget: QWidget, 
    start_pos: QPoint, 
    end_pos: QPoint, 
    duration: int = 300
) -> QPropertyAnimation:
    """
    Creates a "fly-in" animation for a card.
    Moves the widget from the start_pos to the end_pos.
    """
    anim = QPropertyAnimation(widget, b"pos")
    anim.setDuration(duration)
    anim.setStartValue(start_pos)
    anim.setEndValue(end_pos)
    anim.setEasingCurve(QEasingCurve.OutQuad) # Eases out at the end
    return anim
# --- END NEW FUNCTION ---