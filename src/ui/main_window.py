"""
Main application window (QMainWindow) — ANIMATED CARDS + CLEAN UI
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSpacerItem, QSizePolicy
)
from PySide6.QtGui import QIcon, QPixmap, QImage
from PySide6.QtCore import Qt, Slot, QSize, QByteArray, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from src.logic.game_engine import GameEngine, GameState
from src.ui.components.card_widget import CardWidget
from src.utils.constants import GOLD_ACCENT


# === SVG DATA (EMBEDDED) ===
UP_ARROW_SVG = '''
<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 90 90">
  <path d="M 46.969 0.896 c -1.041 -1.194 -2.897 -1.194 -3.937 0 L 13.299 35.011 c -0.932 1.072 -0.171 2.743 1.25 2.743 h 14.249 V 88.09 c 0 1.055 0.855 1.91 1.91 1.91 h 28.584 c 1.055 0 1.91 -0.855 1.91 -1.91 V 37.754 h 14.249 c 1.421 0 2.182 -1.671 1.25 -2.743 L 46.969 0.896 z"
        fill="#27c127"/>
</svg>
'''

DOWN_ARROW_SVG = '''
<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 90 90">
  <path d="M 46.969 89.104 c -1.041 1.194 -2.897 1.194 -3.937 0 L 13.299 54.989 c -0.932 -1.072 -0.171 -2.743 1.25 -2.743 h 14.249 V 1.91 c 0 -1.055 0.855 -1.91 1.91 -1.91 h 28.584 c 1.055 0 1.91 0.855 1.91 1.91 v 50.336 h 14.249 c 1.421 0 2.182 1.671 1.25 2.743 L 46.969 89.104 z"
        fill="#d62929"/>
</svg>
'''


class MainWindow(QMainWindow):
    def __init__(self, engine: GameEngine):
        super().__init__()
        self.engine = engine

        self.dealer_hand_widgets: list[CardWidget] = []
        self.player_hands_widgets: list[list[CardWidget]] = []
        self.player_hands_layouts: list[QVBoxLayout] = []
        self.player_hands_score_labels: list[QLabel] = []

        self.animating_cards: list[tuple[CardWidget, QHBoxLayout, QPoint]] = []
        self.animation_timer = QTimer()
        self.animation_timer.setSingleShot(True)
        self.animation_timer.timeout.connect(self.finish_animations)

        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        self.setWindowTitle("Blackjack 2025")
        self.setGeometry(100, 100, 1200, 800)
        self.setObjectName("MainWindow")

        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)

        # --- Invisible deck reference point ---
        self.deck_reference = QLabel(central_widget)
        self.deck_reference.setFixedSize(120, 160)
        self.deck_reference.move(50, 50)
        self.deck_reference.hide()

        # --- Dealer Area ---
        self.dealer_score_label = QLabel("Dealer: ?")
        self.dealer_score_label.setObjectName("ScoreLabel")
        self.dealer_score_label.setAlignment(Qt.AlignCenter)

        self.dealer_hand_layout = QHBoxLayout()
        self.dealer_hand_layout.setAlignment(Qt.AlignCenter)

        # --- Player Area ---
        self.player_area_label = QLabel("Player Hands")
        self.player_area_label.setObjectName("ScoreLabel")
        self.player_area_label.setAlignment(Qt.AlignCenter)

        self.player_hand_layout = QHBoxLayout()
        self.player_hand_layout.setAlignment(Qt.AlignCenter)

        # --- Message Area ---
        self.message_label = QLabel("Place your bet to start!")
        self.message_label.setObjectName("TitleLabel")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet("font-size: 28px;")

        # --- Controls ---
        controls_layout = QHBoxLayout()
        controls_layout.setAlignment(Qt.AlignCenter)

        # --- BET SECTION (SVG ARROWS) ---
        bet_layout = QVBoxLayout()
        bet_layout.addWidget(QLabel("BET AMOUNT"))

        bet_controls_layout = QHBoxLayout()
        bet_controls_layout.setSpacing(0)
        bet_controls_layout.setContentsMargins(0, 0, 0, 0)

        # Decrease button
        self.bet_decrease_btn = QPushButton()
        self.bet_decrease_btn.setFixedSize(50, 50)
        self.bet_decrease_btn.setObjectName("BetDecreaseBtn")
        down_svg_data = QByteArray(DOWN_ARROW_SVG.encode())
        down_image = QImage.fromData(down_svg_data)
        down_pixmap = QPixmap.fromImage(down_image)
        down_icon = QIcon(down_pixmap)
        self.bet_decrease_btn.setIcon(down_icon)
        self.bet_decrease_btn.setIconSize(QSize(36, 36))

        # Bet display
        self.bet_display = QLabel("$10")
        self.bet_display.setFixedHeight(50)
        self.bet_display.setAlignment(Qt.AlignCenter)
        self.bet_display.setObjectName("BetDisplay")

        # Increase button
        self.bet_increase_btn = QPushButton()
        self.bet_increase_btn.setFixedSize(50, 50)
        self.bet_increase_btn.setObjectName("BetIncreaseBtn")
        up_svg_data = QByteArray(UP_ARROW_SVG.encode())
        up_image = QImage.fromData(up_svg_data)
        up_pixmap = QPixmap.fromImage(up_image)
        up_icon = QIcon(up_pixmap)
        self.bet_increase_btn.setIcon(up_icon)
        self.bet_increase_btn.setIconSize(QSize(36, 36))

        bet_controls_layout.addWidget(self.bet_decrease_btn)
        bet_controls_layout.addWidget(self.bet_display)
        bet_controls_layout.addWidget(self.bet_increase_btn)
        bet_layout.addLayout(bet_controls_layout)

        # Balance
        self.balance_label = QLabel(f"Balance: ${self.engine.player.balance}")
        self.balance_label.setObjectName("BalanceLabel")
        bet_layout.addWidget(self.balance_label)

        # DEAL button
        self.deal_button = QPushButton("DEAL")
        self.deal_button.setFixedHeight(50)
        self.deal_button.setObjectName("DealButton")
        bet_layout.addWidget(self.deal_button)

        # --- Action Buttons ---
        self.hit_button = QPushButton("HIT")
        self.stand_button = QPushButton("STAND")
        self.double_button = QPushButton("DOUBLE")
        self.split_button = QPushButton("SPLIT")
        self.insurance_yes_button = QPushButton("Insurance: YES")
        self.insurance_no_button = QPushButton("Insurance: NO")

        for btn in (self.hit_button, self.stand_button, self.double_button,
                    self.split_button, self.insurance_yes_button, self.insurance_no_button):
            btn.setVisible(False)

        # --- Assemble Controls ---
        controls_layout.addLayout(bet_layout)
        controls_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        controls_layout.addWidget(self.insurance_yes_button)
        controls_layout.addWidget(self.insurance_no_button)
        controls_layout.addWidget(self.hit_button)
        controls_layout.addWidget(self.stand_button)
        controls_layout.addWidget(self.double_button)
        controls_layout.addWidget(self.split_button)

        # --- Final Layout ---
        main_layout.addWidget(self.dealer_score_label)
        main_layout.addLayout(self.dealer_hand_layout)
        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        main_layout.addWidget(self.message_label)
        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        main_layout.addWidget(self.player_area_label)
        main_layout.addLayout(self.player_hand_layout)
        main_layout.addLayout(controls_layout)

    def connect_signals(self):
        self.deal_button.clicked.connect(self.on_deal_clicked)
        self.hit_button.clicked.connect(self.engine.player_hit)
        self.stand_button.clicked.connect(self.engine.player_stand)
        self.double_button.clicked.connect(self.engine.player_double_down)
        self.split_button.clicked.connect(self.engine.player_split)
        self.insurance_yes_button.clicked.connect(self.engine.player_accept_insurance)
        self.insurance_no_button.clicked.connect(self.engine.player_decline_insurance)

        self.bet_increase_btn.clicked.connect(self.on_bet_increase)
        self.bet_decrease_btn.clicked.connect(self.on_bet_decrease)

        self.engine.round_started.connect(self.on_round_started)
        self.engine.card_dealt.connect(self.on_card_dealt)
        self.engine.dealer_finished.connect(self.on_dealer_finished)
        self.engine.round_over.connect(self.on_round_over)
        self.engine.show_message.connect(self.on_show_message)
        self.engine.player_split_successful.connect(self.on_player_split)
        self.engine.next_hand_turn.connect(self.on_next_hand)
        self.engine.offer_insurance.connect(self.on_offer_insurance)

    def _clear_layout_widgets(self, layout):
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
            else:
                child = item.layout()
                if child:
                    self._clear_layout_widgets(child)
                    child.deleteLater()

    def clear_table(self):
        self._clear_layout_widgets(self.dealer_hand_layout)
        self.dealer_hand_widgets = []
        self._clear_layout_widgets(self.player_hand_layout)
        self.player_hands_widgets = []
        self.player_hands_layouts = []
        self.player_hands_score_labels = []
        self.animating_cards = []

    def _get_current_bet(self) -> int:
        return int(self.bet_display.text().replace("$", ""))

    def _set_bet(self, value: int):
        self.bet_display.setText(f"${value}")

    @Slot()
    def on_bet_increase(self):
        cur = self._get_current_bet()
        new_val = min(cur + 5, 500)
        if new_val <= self.engine.player.balance:
            self._set_bet(new_val)

    @Slot()
    def on_bet_decrease(self):
        cur = self._get_current_bet()
        new_val = max(cur - 5, 5)
        self._set_bet(new_val)

    @Slot()
    def on_deal_clicked(self):
        bet = self._get_current_bet()
        self.engine.start_round(bet)

    def _show_betting_controls(self, show: bool):
        self.deal_button.setVisible(show)
        self.deal_button.setEnabled(show)

    def _show_action_controls(self, show: bool):
        for btn in (self.hit_button, self.stand_button, self.double_button, self.split_button):
            btn.setVisible(show)
            btn.setEnabled(show)
        self.double_button.setEnabled(False)
        self.split_button.setEnabled(False)

    def _show_insurance_controls(self, show: bool):
        self.insurance_yes_button.setVisible(show)
        self.insurance_no_button.setVisible(show)
        self.insurance_yes_button.setEnabled(show)
        self.insurance_no_button.setEnabled(show)

    @Slot(GameState)
    def on_round_started(self, state: GameState):
        self.clear_table()
        self._show_betting_controls(False)
        self._show_action_controls(False)
        self._show_insurance_controls(False)

        self.animating_cards = []
        self.animate_initial_deal(state)
        self.animation_timer.start(800)

    def animate_initial_deal(self, state: GameState):
        # Deck center (top-left reference point)
        deck_global = self.deck_reference.mapToGlobal(self.deck_reference.rect().center())

        # Player and dealer target centers
        player_widget = self.player_hand_layout.parentWidget()
        player_global = player_widget.mapToGlobal(player_widget.rect().center())

        dealer_widget = self.dealer_hand_layout.parentWidget()
        dealer_global = dealer_widget.mapToGlobal(dealer_widget.rect().center())

        # Cards: (card, layout, show_front)
        cards = [
            (state.player.hands[0].cards[0], self.player_hand_layout, True),
            (state.dealer.hand.cards[0], self.dealer_hand_layout, False),
            (state.player.hands[0].cards[1], self.player_hand_layout, True),
            (state.dealer.hand.cards[1], self.dealer_hand_layout, True),
        ]

        offset = 0
        for card, target_layout, show_front in cards:
            cw = CardWidget(card, self.centralWidget())
            cw.show_front() if show_front else cw.show_back()

            start_pos = deck_global - QPoint(60, 80)
            cw.move(start_pos)
            cw.raise_()
            cw.show()

            base_center = player_global if target_layout == self.player_hand_layout else dealer_global
            end_pos = base_center + QPoint(offset * 80, 0)
            offset += 1

            anim = QPropertyAnimation(cw, b"pos", self)
            anim.setDuration(600)
            anim.setStartValue(start_pos)
            anim.setEndValue(end_pos)
            anim.setEasingCurve(QEasingCurve.OutQuad)
            anim.start()

            self.animating_cards.append((cw, target_layout, end_pos))

    @Slot()
    def finish_animations(self):
        for cw, layout, end_pos in self.animating_cards:
            local_pos = layout.parentWidget().mapFromGlobal(end_pos)
            cw.setParent(layout.parentWidget())
            layout.addWidget(cw)
            cw.move(local_pos)
        self.animating_cards = []

        self.update_ui(self.engine.get_game_state())

        if not self.engine.insurance_is_offered:
            self._show_action_controls(True)
            hand = self.engine.player.hands[0]
            self.double_button.setEnabled(hand.can_double_down)
            self.split_button.setEnabled(hand.can_split)
            self.message_label.setText("Good luck!")

    @Slot(GameState)
    def on_card_dealt(self, state: GameState):
        self.update_ui(state)
        if self.hit_button.isVisible():
            hand = state.player.hands[state.active_hand_index]
            self.double_button.setEnabled(hand.can_double_down)
            self.split_button.setEnabled(hand.can_split)

    @Slot(GameState)
    def on_dealer_finished(self, state: GameState):
        self.update_ui(state, reveal_dealer=True)

    @Slot(str, str, int, int)
    def on_round_over(self, simple_summary: str, detailed_summary: str, payout: int, new_balance: int):
        self.balance_label.setText(f"Balance: ${new_balance}")
        self._show_action_controls(False)
        self._show_insurance_controls(False)
        self._show_betting_controls(True)

        win_text = simple_summary
        payout_text = f"Payout: ${payout}" if payout >= 0 else f"Lost: ${-payout}"
        full_msg = f"{win_text} — {payout_text}"

        self.message_label.setText(full_msg)
        self.message_label.setStyleSheet("color: #d4af37; font-weight: bold; font-size: 32px;")

        QTimer.singleShot(5000, lambda: [
            self.clear_table(),
            self.message_label.setText("Place your bet to start!"),
            self.message_label.setStyleSheet("font-size: 28px;"),
            self.dealer_score_label.setText("Dealer: ?")
        ])

    @Slot(str)
    def on_show_message(self, msg: str):
        self.message_label.setText(msg)

    @Slot(GameState)
    def on_player_split(self, state: GameState):
        self.update_ui(state)
        hand = state.player.hands[state.active_hand_index]
        self.double_button.setEnabled(hand.can_double_down)
        self.split_button.setEnabled(hand.can_split)

    @Slot(GameState)
    def on_next_hand(self, state: GameState):
        self.update_ui(state)
        hand = state.player.hands[state.active_hand_index]
        self.double_button.setEnabled(hand.can_double_down)
        self.split_button.setEnabled(hand.can_split)

    @Slot(GameState)
    def on_offer_insurance(self, state: GameState):
        self.message_label.setText("Dealer has Ace. Insurance?")
        self._show_action_controls(False)
        self._show_insurance_controls(True)

    def update_ui(self, state: GameState, reveal_dealer: bool = False):
        self._clear_layout_widgets(self.player_hand_layout)
        self._clear_layout_widgets(self.dealer_hand_layout)
        self.dealer_hand_widgets = []
        self.player_hands_widgets = []
        self.player_hands_layouts = []
        self.player_hands_score_labels = []

        for i, hand in enumerate(state.player.hands):
            vlay = QVBoxLayout()
            vlay.setAlignment(Qt.AlignCenter)
            score = QLabel(f"Hand {i+1}: {hand.value}")
            score.setObjectName("ScoreLabel")
            if i == state.active_hand_index and len(state.player.hands) > 1:
                score.setStyleSheet(f"color: {GOLD_ACCENT};")
            vlay.addWidget(score)

            hlay = QHBoxLayout()
            hand_widgets = []
            for card in hand.cards:
                cw = CardWidget(card)
                cw.show_front()
                hlay.addWidget(cw)
                hand_widgets.append(cw)
            vlay.addLayout(hlay)
            self.player_hand_layout.addLayout(vlay)

            self.player_hands_layouts.append(vlay)
            self.player_hands_score_labels.append(score)
            self.player_hands_widgets.append(hand_widgets)

        for i, card in enumerate(state.dealer.hand.cards):
            cw = CardWidget(card)
            if i == 0 and not reveal_dealer:
                cw.show_back()
            else:
                cw.show_front()
            self.dealer_hand_layout.addWidget(cw)
            self.dealer_hand_widgets.append(cw)

        if reveal_dealer:
            self.dealer_score_label.setText(f"Dealer: {state.dealer.hand.value}")
        else:
            self.dealer_score_label.setText(f"Dealer: {state.dealer.visible_value}")

        self.balance_label.setText(f"Balance: ${state.player.balance}")