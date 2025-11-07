"""
Contains the logic for the Dealer's turn.
"""

from src.game.deck import Shoe  # <-- THIS IS THE FIX (was src.game.shoe)
from src.game.player import Dealer
from src.game.rules import GameRules, should_dealer_hit


def play_dealer_turn(dealer: Dealer, shoe: Shoe, rules: GameRules):
    """
    Plays out the dealer's turn automatically.

    The dealer will continue to hit until the 'should_dealer_hit'
    rule returns False.

    This function yields each time a card is dealt so the
    GameEngine can animate it.
    """
    while should_dealer_hit(dealer.hand, rules):
        new_card = shoe.deal()
        dealer.hand.add_card(new_card)
        # We 'yield' the card to signal to the engine that a
        # new card was added, allowing for animation.
        yield new_card

    # When the loop finishes, the dealer's turn is over.
    # We yield None to signify the end.
    yield None
