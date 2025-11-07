"""
Defines the SQLModel table for storing player statistics.
"""

from typing import Optional
from sqlmodel import Field, SQLModel

class PlayerStats(SQLModel, table=True):
    """
    A table to store player stats. We'll use a single row with id=1.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    balance: int = Field(default=1000)
    total_wins: int = Field(default=0)
    total_losses: int = Field(default=0)
    # We could add more stats here later, like 'blackjacks_hit'