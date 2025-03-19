import os
import time
import logging
import cv2
import numpy as np


from utils.image_utils import ImageUtils
from utils.adb_utils import ADBUtils
from utils.debug_utils import DebugVisualizer 
 
 
class Checktrainarmy:

    def __init__(self):
        self.adb = ADBUtils()
        self.image = ImageUtils()
        self.image_folder = os.path.join(os.path.dirname(__file__), "images")
        logging.info("\n" + "="*50)
        logging.info("TRAINING SEQUENCE INITIALIZED")
        logging.info("="*50)
    def check_army_state(self):
        self.click_initial_buttons()
        return self.check_army()  

    def click_initial_buttons(self):
        self.image.find_and_click_image(self.adb, self.image_folder, "train_button.png", confidence_threshold=0.8)
    def check_army(self, max_attempts=1000, wait_time=10):
        checks = ["troops.png", "spells.png", "heroes.png"]
        
        for attempt in range(max_attempts):
            results = {}

            for check in checks:
                logging.info(f"Attempting to find {check} (Attempt {attempt + 1}/{max_attempts})...")
                found = self.image.detect_image(self.adb, self.image_folder, check,confidence_threshold=0.8)

                if found:
                    logging.info(f"✅ Successfully found {check}")
                else:
                    logging.info(f"⏭️ {check} not found. Waiting {wait_time} seconds before retrying...")
                
                results[check] = found

            # If all images are found, return True
            if all(results.values()):
                logging.info("✅ All troops, spells, and heroes are trained.")
                return True

            # Wait before trying again
            time.sleep(wait_time)

        logging.info("❌ Training not completed within the allowed attempts.")
        return False

