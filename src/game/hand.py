"""
Contains the logic for a single hand of Blackjack.
"""

from dataclasses import dataclass, field
from typing import List
from src.game.deck import Card  # We import from our own module


@dataclass
class Hand:
    """
    Represents a player's or dealer's hand.
    """

    cards: List[Card] = field(default_factory=list)
    is_split: bool = False
    bet: int = 0

    def add_card(self, card: Card):
        """Adds a card to the hand."""
        self.cards.append(card)

    @property
    def value(self) -> int:
        """
        Calculates the total value of the hand, handling Aces (1 or 11)
        dynamically.
        """
        total = 0
        num_aces = 0

        for card in self.cards:
            total += card.value
            if card.rank == "A":  # Check against the Enum value
                num_aces += 1

        # Adjust for Aces
        # While the total is over 21 and we have Aces,
        # convert Ace value from 11 to 1
        while total > 21 and num_aces > 0:
            total -= 10
            num_aces -= 1

        return total

    @property
    def is_bust(self) -> bool:
        """Checks if the hand value is over 21."""
        return self.value > 21

    @property
    def is_blackjack(self) -> bool:
        """Checks for a natural Blackjack (2 cards totaling 21)."""
        return len(self.cards) == 2 and self.value == 21

    @property
    def can_split(self) -> bool:
        """
        Checks if the hand is eligible to be split.
        (Two cards of the same rank, e.g., two Kings, or two 8s).

        --- THIS WAS THE BROKEN FUNCTION ---
        """
        return len(self.cards) == 2 and self.cards[0].rank == self.cards[1].rank

    @property
    def can_double_down(self) -> bool:
        """
        Checks if the hand is eligible to double down.
        (Typically on the first two cards, with a total of 9, 10, or 11).
        """
        return len(self.cards) == 2 and self.value in [9, 10, 11]

    def clear(self):
        """Resets the hand for the next round."""
        self.cards = []
        self.is_split = False
        self.bet = 0

    def __str__(self) -> str:
        """String representation of the hand."""
        # Use the card's __str__ method
        return f"[{', '.join(str(c) for c in self.cards)}] (Value: {self.value})"
