"""
Defines the Player and Dealer classes.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from src.game.hand import Hand
from src.game.deck import Card


@dataclass
class Player:
    """
    Represents the user/player.
    """

    balance: int = 1000
    hands: List[Hand] = field(default_factory=list)
    insurance: int = 0

    def place_bet(self, amount: int, hand_index: int = 0) -> bool:
        """
        Places a bet on a specific hand and subtracts from balance.
        Returns False if a bet can't be made.
        """
        if amount > self.balance:
            print(f"Error: Bet amount {amount} > balance {self.balance}")
            return False

        self.balance -= amount

        # Ensure hand exists (for the very first bet)
        if not self.hands:
            self.hands.append(Hand())

        self.hands[hand_index].bet = amount
        return True

    def clear_hands(self):
        """Resets the player's hands for the next round."""
        self.hands = []
        self.insurance = 0

    @property
    def total_bet(self) -> int:
        """Calculates the total bet across all split hands."""
        return sum(hand.bet for hand in self.hands) + self.insurance


@dataclass
class Dealer:
    """
    Represents the dealer.
    """

    hand: Hand = field(default_factory=Hand)

    @property
    def hidden_card(self) -> Optional[Card]:
        """
        The dealer's first card (the "hole card").
        This is hidden until the player's turn is over.
        """
        if len(self.hand.cards) > 0:
            return self.hand.cards[0]
        return None

    @property
    def visible_card(self) -> Optional[Card]:
        """
        The dealer's second card (the "up card").
        This is visible to the player.
        """
        if len(self.hand.cards) > 1:
            return self.hand.cards[1]
        return None

    @property
    def visible_value(self) -> int:
        """
        Calculates the value of the dealer's visible (up) card.
        Used for insurance and player strategy.
        """
        if self.visible_card:
            # An Ace's value is 11 by default, which is correct for checking insurance
            return self.visible_card.value
        return 0

    def clear_hand(self):
        """Resets the dealer's hand."""
        self.hand.clear()
