"""
The core GameEngine, built on PySide6's QObject.
It manages the game state and flow, emitting signals
for the UI to react to.
"""

from PySide6.QtCore import QObject, Signal
from src.game.deck import Shoe, Rank
from src.game.player import Player, Dealer
from src.game.hand import Hand
from src.game.rules import GameRules, get_hand_result
from src.logic.ai_dealer import play_dealer_turn
from src.audio.sound_manager import SoundManager
from typing import Optional

# --- NEW IMPORTS ---
from src.data.database import load_stats, save_stats, create_db_and_tables
from src.data.models import PlayerStats
# --- END NEW IMPORTS ---


class GameState:
    """A simple class to hold the current game state for signals."""

    def __init__(self, player: Player, dealer: Dealer, active_hand_index: int):
        self.player = player
        self.dealer = dealer
        self.active_hand_index = active_hand_index
        self.player_balance = player.balance
        self.total_bet = player.total_bet


class GameEngine(QObject):
    """
    Manages the Blackjack game logic and state.
    Inherits from QObject to use signals and slots.
    """

    # --- Signals ---
    round_started = Signal(GameState)
    card_dealt = Signal(GameState)
    dealer_finished = Signal(GameState)        # Dealer done drawing
    next_hand_turn = Signal(GameState)

    round_over = Signal(str, str, int, int)   # simple, detailed, payout, balance
    show_message = Signal(str)
    player_split_successful = Signal(GameState)
    offer_insurance = Signal(GameState)

    def __init__(self):
        super().__init__()

        # --- NEW DATABASE LOGIC ---
        # 1. Ensure database and tables exist
        create_db_and_tables()
        # 2. Load stats from DB
        self.stats: PlayerStats = load_stats()
        # --- END NEW LOGIC ---

        self.sound_manager = SoundManager()

        self.shoe = Shoe(num_decks=6)
        
        # 3. Initialize player with loaded balance
        self.player = Player(balance=self.stats.balance)
        
        self.dealer = Dealer()
        self.rules = GameRules()

        self.current_bet = 0
        self.active_hand_index = 0
        self.insurance_is_offered = False

    def get_game_state(self) -> GameState:
        return GameState(
            player=self.player,
            dealer=self.dealer,
            active_hand_index=self.active_hand_index,
        )

    # --- Game Flow Methods ---

    def start_round(self, bet: int):
        self.player.clear_hands()
        self.dealer.clear_hand()
        self.active_hand_index = 0
        self.current_bet = bet
        self.insurance_is_offered = False

        if not self.player.place_bet(bet):
            self.sound_manager.play("lose")
            self.show_message.emit("Not enough balance to bet!")
            return

        self.sound_manager.play("chip")

        # Initial deal
        self.player.hands[0].add_card(self.shoe.deal())
        self.dealer.hand.add_card(self.shoe.deal())
        self.player.hands[0].add_card(self.shoe.deal())
        self.dealer.hand.add_card(self.shoe.deal())
        self.sound_manager.play("deal")

        self.round_started.emit(self.get_game_state())

        # Insurance?
        if self.dealer.visible_card and self.dealer.visible_card.rank == Rank.ACE:
            self.insurance_is_offered = True
            self.offer_insurance.emit(self.get_game_state())
            return

        # Check Blackjacks
        player_has_bj = self.player.hands[0].is_blackjack
        dealer_has_bj = self.dealer.hand.is_blackjack

        if player_has_bj or dealer_has_bj:
            self._end_round()
        else:
            self.show_message.emit("Your turn. Hit or Stand?")

    def _handle_insurance_result(self):
        self.insurance_is_offered = False
        player_has_bj = self.player.hands[0].is_blackjack
        dealer_has_bj = self.dealer.hand.is_blackjack

        if player_has_bj or dealer_has_bj:
            self._end_round()
        else:
            self.show_message.emit("Your turn. Hit or Stand?")
            self.round_started.emit(self.get_game_state())

    def player_accept_insurance(self):
        insurance_cost = int(self.player.hands[0].bet / 2)
        if self.player.balance < insurance_cost:
            self.sound_manager.play("lose")
            self.show_message.emit("Not enough balance for insurance!")
            self.player_decline_insurance()
            return

        self.player.balance -= insurance_cost
        self.player.insurance = insurance_cost
        self.sound_manager.play("chip")
        self._handle_insurance_result()

    def player_decline_insurance(self):
        self.player.insurance = 0
        self._handle_insurance_result()

    def player_hit(self):
        if self.active_hand_index >= len(self.player.hands):
            return

        hand = self.player.hands[self.active_hand_index]
        hand.add_card(self.shoe.deal())
        self.sound_manager.play("deal")
        self.card_dealt.emit(self.get_game_state())

        if hand.is_bust:
            self.sound_manager.play("bust")
            self.show_message.emit("Bust!")
            self._move_to_next_hand_or_dealer()
        elif hand.value == 21:
            self._move_to_next_hand_or_dealer()

    def player_stand(self):
        if self.active_hand_index >= len(self.player.hands):
            return
        self._move_to_next_hand_or_dealer()

    def player_double_down(self):
        if self.active_hand_index >= len(self.player.hands):
            return

        hand = self.player.hands[self.active_hand_index]
        if not hand.can_double_down:
            self.show_message.emit("Can only double down on 9, 10, or 11!")
            return

        if not self.player.place_bet(hand.bet):
            self.sound_manager.play("lose")
            self.show_message.emit("Not enough balance to double down!")
            return

        hand.bet *= 2
        self.sound_manager.play("chip")
        hand.add_card(self.shoe.deal())
        self.sound_manager.play("deal")
        self.card_dealt.emit(self.get_game_state())

        if hand.is_bust:
            self.sound_manager.play("bust")
            self.show_message.emit(f"Bust on double! Lost {hand.bet}.")
        self._move_to_next_hand_or_dealer()

    def player_split(self):
        if self.active_hand_index >= len(self.player.hands):
            return

        hand_to_split = self.player.hands[self.active_hand_index]
        if not hand_to_split.can_split:
            self.show_message.emit("Can only split two cards of the same rank!")
            return

        if len(self.player.hands) >= self.rules.max_splits + 1:
            self.show_message.emit(f"Cannot have more than {self.rules.max_splits + 1} hands.")
            return

        if not self.player.place_bet(hand_to_split.bet):
            self.sound_manager.play("lose")
            self.show_message.emit("Not enough balance to split!")
            return

        self.sound_manager.play("chip")
        new_hand = Hand(bet=hand_to_split.bet, is_split=True)
        new_hand.add_card(hand_to_split.cards.pop(1))
        self.player.hands.insert(self.active_hand_index + 1, new_hand)

        hand_to_split.add_card(self.shoe.deal())
        new_hand.add_card(self.shoe.deal())
        self.sound_manager.play("deal")

        self.player_split_successful.emit(self.get_game_state())

        if hand_to_split.is_blackjack:
            self._move_to_next_hand_or_dealer()

    def _move_to_next_hand_or_dealer(self):
        if self.active_hand_index < len(self.player.hands) - 1:
            self.active_hand_index += 1
            self.show_message.emit(f"Now playing Hand {self.active_hand_index + 1}")
            self.next_hand_turn.emit(self.get_game_state())
        else:
            self._start_dealer_turn()

    def _start_dealer_turn(self):
        all_busted = all(hand.is_bust for hand in self.player.hands)
        if all_busted:
            self.show_message.emit("All player hands busted.")
            self._end_round()
            return

        # Dealer draws all cards
        dealer_ai = play_dealer_turn(self.dealer, self.shoe, self.rules)
        for card in dealer_ai:
            if card:
                self.dealer.hand.add_card(card)
                self.card_dealt.emit(self.get_game_state())
            else:
                break

        # Dealer done → reveal hole card + end round
        self.dealer_finished.emit(self.get_game_state())
        self._end_round()

    def _translate_result_to_friendly_text(self, result_str: str) -> str:
        translations = {
            "blackjack": "Blackjack!",
            "win_dealer_bust": "You Win! (Dealer Busted)",
            "win_higher": "You Win! (Higher Hand)",
            "bust": "Bust! (You Lose)",
            "lose": "You Lose (Dealer Was Higher)",
            "push": "Push (Tie)",
            "push_blackjack": "Push (Both Blackjack)",
        }
        return translations.get(result_str, result_str.replace("_", " ").title())

    def _end_round(self):
        total_payout = 0
        detailed_summary = ""
        final_player_win_status = 0  # 0=push, 1=win, -1=lose

        current_insurance_bet = self.player.insurance
        if current_insurance_bet > 0:
            if self.dealer.hand.is_blackjack:
                insurance_payout = int(current_insurance_bet * self.rules.insurance_payout)
                total_payout += current_insurance_bet + insurance_payout
                self.player.balance += current_insurance_bet + insurance_payout
                detailed_summary += f"INSURANCE WIN: +${insurance_payout}\n"
            else:
                detailed_summary += f"INSURANCE LOSE: -${current_insurance_bet}\n"
            self.player.insurance = 0

        for i, hand in enumerate(self.player.hands):
            result_str, payout = get_hand_result(hand, self.dealer.hand, self.rules)
            total_payout += payout
            self.player.balance += payout

            if payout > hand.bet:
                final_player_win_status = 1
            elif payout == 0 and final_player_win_status != 1:
                final_player_win_status = -1

            friendly_text = self._translate_result_to_friendly_text(result_str)
            hand_prefix = f"Hand {i + 1} ({hand.value})"
            detailed_summary += f"{hand_prefix}: {friendly_text} (Bet: ${hand.bet}, Won: ${payout})\n"

        # Simple summary
        if final_player_win_status == 1:
            simple_summary = "You Won!"
        elif final_player_win_status == -1:
            simple_summary = "You Lost"
        else:
            simple_summary = "Push (It's a Tie)"

        if len(self.player.hands) == 1 and self.player.hands[0].is_blackjack:
            simple_summary = "Blackjack!"

        # Sound
        if final_player_win_status == 1:
            self.sound_manager.play("win")
        elif final_player_win_status == -1:
            self.sound_manager.play("lose")

        # --- NEW DATABASE LOGIC ---
        # Update and save stats
        if final_player_win_status == 1:
            self.stats.total_wins += 1
        elif final_player_win_status == -1:
            self.stats.total_losses += 1
        
        self.stats.balance = self.player.balance
        save_stats(self.stats)
        # --- END NEW LOGIC ---

        if not detailed_summary.strip():
            detailed_summary = "Round over."

        self.round_over.emit(simple_summary, detailed_summary, total_payout, self.player.balance)
        self.active_hand_index = 0