"""
SoundManager to handle all audio playback using pygame.mixer.
"""

import pygame.mixer
from src.utils.constants import SOUND_ASSET_PATH


class SoundManager:
    def __init__(self):
        try:
            pygame.mixer.init()
            # Load sounds into memory
            self.sounds = {
                "deal": pygame.mixer.Sound(f"{SOUND_ASSET_PATH}deal.wav"),
                "chip": pygame.mixer.Sound(f"{SOUND_ASSET_PATH}chip.wav"),
                "win": pygame.mixer.Sound(f"{SOUND_ASSET_PATH}win.wav"),
                "lose": pygame.mixer.Sound(f"{SOUND_ASSET_PATH}lose.wav"),
                "bust": pygame.mixer.Sound(
                    f"{SOUND_ASSET_PATH}lose.wav"
                ),  # Use same as lose
            }
            # Set volume (0.0 to 1.0)
            self.sounds["deal"].set_volume(0.5)
            self.sounds["chip"].set_volume(0.7)

        except Exception as e:
            print(f"Error initializing sound manager: {e}")
            print("Audio will be disabled.")
            self.sounds = None

    def play(self, sound_name: str):
        """Plays a sound by its key name."""
        if self.sounds and sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except Exception as e:
                print(f"Error playing sound '{sound_name}': {e}")
