"""
Defines the game rules and payout logic.
"""

from dataclasses import dataclass
from src.game.hand import Hand
from src.game.player import Dealer


# Using a dataclass makes rules easy to change or load from a config
@dataclass(frozen=True)
class GameRules:
    """Stores all configurable game rules."""

    blackjack_payout: float = 1.5  # 3:2
    standard_payout: float = 1.0  # 1:1
    insurance_payout: float = 2.0  # 2:1
    dealer_hits_on_soft_17: bool = True
    max_splits: int = 3  # Max 3 splits (for a total of 4 hands)


# This file is a great place for static helper functions
# that implement the rules.


def should_dealer_hit(dealer_hand: Hand, rules: GameRules) -> bool:
    """
    Implements the 'Dealer hits on soft 17' rule.
    """
    dealer_value = dealer_hand.value

    # Dealer always hits on 16 or less
    if dealer_value < 17:
        return True

    # Dealer always stands on 18 or more
    if dealer_value > 17:
        return False

    # The value is exactly 17. Now we check for "soft" 17.
    # A hand is "soft" if an Ace is being counted as 11.
    # We can check this by seeing if the "hard" value (all Aces=1)
    # is different from the "soft" value (calculated by hand.value)

    hard_value = 0
    for card in dealer_hand.cards:
        hard_value += 1 if card.rank == "A" else card.value

    # Example: A-6
    # hard_value = 1 + 6 = 7
    # dealer_value = 17
    # 7 != 17, so it's a soft hand.

    # Example: 10-7
    # hard_value = 10 + 7 = 17
    # dealer_value = 17
    # 17 == 17, so it's a hard hand.

    is_soft = hard_value != dealer_value

    if is_soft and rules.dealer_hits_on_soft_17:
        return True

    # It's a hard 17, or it's a soft 17 and the rule is to stand.
    return False


def get_hand_result(
    player_hand: Hand, dealer_hand: Hand, rules: GameRules
) -> tuple[str, int]:
    """
    Compares a single player hand to the dealer's hand and calculates the payout.

    Returns:
        A tuple of (result_string, payout_amount)
        Payout_amount INCLUDES the original bet (e.g., bet 10, win 10, returns 20)
    """
    player_value = player_hand.value
    dealer_value = dealer_hand.value
    bet = player_hand.bet

    if player_hand.is_blackjack:
        if dealer_hand.is_blackjack:
            return ("push_blackjack", bet)  # Push
        else:
            # Blackjack win!
            payout = bet + int(bet * rules.blackjack_payout)
            return ("blackjack", payout)

    if player_hand.is_bust:
        return ("bust", 0)  # Player loses bet

    if dealer_hand.is_bust:
        payout = bet + int(bet * rules.standard_payout)
        return ("win_dealer_bust", payout)  # Player wins

    if player_value > dealer_value:
        payout = bet + int(bet * rules.standard_payout)
        return ("win_higher", payout)  # Player wins

    if player_value == dealer_value:
        return ("push", bet)  # Push

    return ("lose", 0)  # Player loses (dealer_value > player_value)
