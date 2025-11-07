"""
Handles all database creation and session management
for loading and saving player stats.
"""

from sqlmodel import SQLModel, create_engine, Session, select
from src.data.models import PlayerStats

# Define the database file
DATABASE_URL = "sqlite:///blackjack_stats.db"

# Create the engine. 'check_same_thread' is needed for SQLite.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def create_db_and_tables():
    """
    Called once on startup to create the database and tables if they
    don't already exist.
    """
    SQLModel.metadata.create_all(engine)

def load_stats() -> PlayerStats:
    """
    Loads player stats from the database.
    If no stats exist (first time playing), it creates them.
    We will use a single row with ID=1 for the player.
    """
    with Session(engine) as session:
        # Try to find the stats row with id=1
        statement = select(PlayerStats).where(PlayerStats.id == 1)
        stats = session.exec(statement).first()

        if stats:
            # Found existing stats
            print(f"Loaded stats: Balance ${stats.balance}")
            return stats
        else:
            # First time playing. Create new stats.
            print("No stats found. Creating new player file...")
            new_stats = PlayerStats(id=1, balance=1000, total_wins=0, total_losses=0)
            session.add(new_stats)
            session.commit()
            session.refresh(new_stats)
            print(f"New stats created: Balance ${new_stats.balance}")
            return new_stats

def save_stats(stats_data: PlayerStats):
    """
    Saves the provided PlayerStats object to the database.
    """
    with Session(engine) as session:
        # Get the existing row with id=1
        stats_to_update = session.get(PlayerStats, 1)
        
        if stats_to_update:
            # Update the values
            stats_to_update.balance = stats_data.balance
            stats_to_update.total_wins = stats_data.total_wins
            stats_to_update.total_losses = stats_data.total_losses
            
            session.add(stats_to_update)
            session.commit()
            # print(f"Stats saved: Balance ${stats_to_update.balance}") # Optional: for debugging
        else:
            # This shouldn't happen if load_stats was called, but as a fallback:
            session.add(stats_data)
            session.commit()
            print("Error: Could not find stats to save. Created new entry.")