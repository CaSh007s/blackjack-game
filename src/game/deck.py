"""
Contains the data models for Card, Deck, and Shoe.
We use dataclasses for clean, type-safe models.
"""

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List


class Suit(str, Enum):
    HEARTS = "Hearts"
    DIAMONDS = "Diamonds"
    CLUBS = "Clubs"
    SPADES = "Spades"


class Rank(str, Enum):
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    ACE = "A"


@dataclass(frozen=True)
class Card:
    rank: Rank
    suit: Suit

    @property
    def value(self) -> int:
        if self.rank in [Rank.JACK, Rank.QUEEN, Rank.KING]:
            return 10
        if self.rank == Rank.ACE:
            return 11
        return int(self.rank.value)

    def __str__(self) -> str:
        return f"{self.rank.value} of {self.suit.value}"

    @property
    def image_name(self) -> str:
        suit_str = self.suit.value.lower()
        rank_str = ""
        if self.rank.value.isdigit():
            num_val = int(self.rank.value)
            if num_val == 10:
                rank_str = "10"
            else:
                rank_str = f"0{num_val}"
        else:
            rank_str = self.rank.value[0]
        return f"card_{suit_str}_{rank_str}.png"


class Deck:
    def __init__(self):
        self.cards: List[Card] = [Card(rank, suit) for suit in Suit for rank in Rank]
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self) -> Card | None:
        if not self.cards:
            return None
        return self.cards.pop()


class Shoe:
    def __init__(self, num_decks: int = 6):
        self.num_decks = num_decks
        self.cards: List[Card] = []
        self.penetration_marker = 0.75
        self.build_shoe()

    def build_shoe(self):
        self.cards = []
        for _ in range(self.num_decks):
            deck = Deck()
            self.cards.extend(deck.cards)
        random.shuffle(self.cards)
        self.reshuffle_threshold = int(len(self.cards) * (1 - self.penetration_marker))

    def deal(self) -> Card:
        if len(self.cards) < self.reshuffle_threshold:
            print("--- Reached penetration marker. Reshuffling shoe. ---")
            self.build_shoe()

        if not self.cards:
            print("--- Shoe is empty. Building new shoe. ---")
            self.build_shoe()

        # --- FIX: Return a NEW Card instance ---
        original_card = self.cards.pop()
        return Card(rank=original_card.rank, suit=original_card.suit)

    def __len__(self) -> int:
        return len(self.cards)