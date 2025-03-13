import os
import time
import random
import logging

from utils.image_utils import ImageUtils
from utils.adb_utils import ADBUtils 
class StartingSequence:
    def __init__(self):
        self.adb = ADBUtils()
        self.image = ImageUtils()
        self.image_folder = os.path.join(os.path.dirname(__file__), "images")

    def check_game_state(self):
        """Check if the game is in the expected state."""
        home_anker = os.path.join(self.image_folder, "home_anker.png")
        
        if not self.adb.take_screenshot("screen.png"):
            logging.error("Failed to take screenshot while checking game state.")
            return False
            
        home_anker_pos = self.image.find_image("screen.png", home_anker)

        if home_anker_pos:
            logging.info("Game is in the expected state")
            return True

        logging.warning("Game not in expected state")
        return False

    def collect_resources(self):
        """Collect resources by clicking on resource icons."""
        logging.info("Starting resource collection process.")
        if not self.check_game_state():
            logging.warning("Game not in expected state, cannot collect resources.")
            return False

        resources = ["gold.png", "elixir.png", "dark_elixir.png"]
        for resource in resources:
            logging.info(f"Attempting to collect {resource}.")
            if self.image.find_and_click_image(self.adb, self.image_folder, resource):
                logging.info(f"Successfully clicked on {resource}")
                time.sleep(random.uniform(1, 2))  # Mimic human delay
            else:
                logging.info(f"{resource} not found or could not be clicked")

        logging.info("Resource collection process completed.")
        return True
