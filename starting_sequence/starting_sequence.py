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
        logging.info("\n" + "="*50)
        logging.info("STARTING SEQUENCE INITIALIZED")
        logging.info("="*50)

    def check_game_state(self):
        """Check if the game is in the expected state."""
        logging.info("\n" + "-"*40)
        logging.info("CHECKING GAME STATE")
        logging.info("-"*40)
        
        home_anker = os.path.join(self.image_folder, "home_anker.png")
        
        if not self.adb.take_screenshot("screen.png"):
            logging.error("❌ Failed to take screenshot while checking game state")
            return False
            
        home_anker_pos = self.image.find_image("screen.png", home_anker)

        if home_anker_pos:
            logging.info("✅ Game is in the expected state")
            return True

        logging.warning("❌ Game is not in expected state")
        return False

    def click_pre_collection_buttons(self):
        """Click buttons needed before collecting resources, ensuring proper battle sequence."""
        
        logging.info("\n" + "-" * 40)
        logging.info("CENTERING SCREEN (MUST FOR TROOP DEPLOYMENT)")
        logging.info("-" * 40)

        # Step 1: Click "attack_button.png" first to open the attack menu
        for attempt in range(3):  # Try up to 3 times
            logging.info(f"Attempting to click 'attack_button.png' (attempt {attempt + 1}/3)")

            if self.image.find_and_click_image(self.adb, self.image_folder, "attack_button.png", confidence_threshold=0.6):
                logging.info("✅ Successfully clicked 'attack_button.png'")
                time.sleep(1)  # Short delay before checking for find match button
                break  # Exit retry loop once clicked
            else:
                logging.warning(f"⚠️ Could not find 'attack_button.png' on attempt {attempt + 1}")
                time.sleep(1)  # Short delay before retrying

        # Step 2: Now, attempt to click "find_match.png" (if available)
        find_match_clicked = False
        for attempt in range(3):  # Try up to 3 times
            logging.info(f"Attempting to click 'find_match.png' (attempt {attempt + 1}/3)")

            if self.image.detect_image(self.adb, self.image_folder, "find_match.png"):
                if self.image.find_and_click_image(self.adb, self.image_folder, "find_match.png", confidence_threshold=0.6):
                    logging.info("✅ Successfully clicked 'find_match.png'")
                    find_match_clicked = True  # Mark that we clicked find match
                    logging.info("⏳ Waiting for resources to load...")
                    time.sleep(random.uniform(2.5, 3.5))  # Mimic human delay
                    break  # Exit loop once successful
            else:
                logging.warning(f"🚫 'find_match.png' not found on attempt {attempt + 1}, retrying...")
                time.sleep(1)  # Short delay before retrying

        # Step 3: If "find_match.png" was NOT found, retry clicking "attack_button.png" after 3 failed attempts
        if not find_match_clicked:
            logging.info("🔄 'find_match.png' not found, retrying 'attack_button.png' to reopen the menu")
            self.image.find_and_click_image(self.adb, self.image_folder, "attack_button.png", confidence_threshold=0.6)
            time.sleep(2)  # Give time for UI to update

            # Final check for "find_match.png"
            logging.info("🔍 Final attempt to find 'find_match.png'...")
            if self.image.detect_image(self.adb, self.image_folder, "find_match.png"):
                self.image.find_and_click_image(self.adb, self.image_folder, "find_match.png", confidence_threshold=0.6)
                logging.info("✅ Successfully clicked 'find_match.png' on final attempt")
                find_match_clicked = True
                time.sleep(2)  # Extra wait for stability

        # Step 4: Only wait & click "end_battle.png" if "find_match.png" was successfully clicked
        if find_match_clicked:
            logging.info("⏳ Waiting 2 seconds before checking for 'end_battle.png'...")
            time.sleep(2)

            if self.image.find_and_click_image(self.adb, self.image_folder, "end_battle.png", confidence_threshold=0.7):
                logging.info("✅ Successfully clicked 'end_battle.png'")
                time.sleep(random.uniform(1, 2))  # Mimic human delay
            else:
                logging.warning("⏭️ 'end_battle.png' not found or could not be clicked")
        else:
            logging.error("❌ 'find_match.png' could not be found after multiple attempts. Skipping end battle.")

        # Final short delay to ensure UI stability
        logging.info("⏳ Waiting for UI stabilization...")
        time.sleep(2)

    def collect_resources(self):
        """Collect resources by clicking on resource icons."""
        logging.info("\n" + "="*50)
        logging.info("STARTING RESOURCE COLLECTION")
        logging.info("="*50)
        
        # Click additional buttons before collecting resources
        self.click_pre_collection_buttons()
        
        if not self.check_game_state():
            logging.warning("❌ Game not in expected state, cannot collect resources")
            return False
      
        resources = ["gold.png", "elixir.png", "dark_elixir.png"]
        
        logging.info("\n" + "-"*40)
        logging.info("COLLECTING RESOURCES")
        logging.info("-"*40)
        
        resource_count = 0
        for resource in resources:
            logging.info(f"Attempting to collect {resource}...")
            if self.image.find_and_click_image(self.adb, self.image_folder, resource):
                logging.info(f"✅ Successfully clicked on {resource}")
                resource_count += 1
                time.sleep(random.uniform(1, 2))  # Mimic human delay
            else:
                logging.info(f"⏭️ {resource} not found or could not be clicked")

        logging.info("\n" + "-"*40)
        logging.info(f"RESOURCE COLLECTION COMPLETED: {resource_count}/{len(resources)} resources collected")
        logging.info("-"*40)
        return True

    def is_home_screen(self):
        """Check if the game is currently on the home screen"""
        logging.info("Checking if we are on the home screen...")
        
        if not self.adb.take_screenshot("screen.png"):
            logging.error("❌ Failed to take screenshot while checking home screen")
            return False
            
        # Check for home screen indicators
        for marker in ["home_anker.png"]:
            if self.image.detect_image(self.adb, self.image_folder, marker):
                logging.info(f"✅ Home screen detected using {marker}")
                return True
        
        logging.warning("❌ Not on home screen")
        return False

    def navigate_to_home(self, max_attempts=5):
        """Attempt to navigate back to the home screen"""
        logging.info("\n" + "-"*40)
        logging.info("NAVIGATING TO HOME SCREEN")
        logging.info("-"*40)
        
        # First check if already on home screen
        if self.is_home_screen():
            return True
        
        # Try clicking UI elements that can lead back to home
        for _ in range(max_attempts):
            # Take a screenshot
            if not self.adb.take_screenshot("screen.png"):
                continue
            
            # Check for buttons that can help return to home
            buttons = [
                "close.png",
                "back_anchor.png", 
                "back_anchor.png",
            ]
            
            clicked = False
            for button in buttons:
                if self.image.find_and_click_image(self.adb, self.image_folder, button):
                    logging.info(f"✅ Clicked {button} to return home")
                    clicked = True
                    time.sleep(1.5)
                    break
            
            # If we didn't click anything, try a special technique - click top left corner
            if not clicked:
                logging.info("Trying to click top-left area (often has home/back button)")
                self.adb.humanlike_click(50, 50)  # Top left is often a back button
                time.sleep(1.5)
            
            # Check if we reached home
            if self.is_home_screen():
                logging.info("✅ Successfully navigated to home screen")
                return True
        
        logging.error("❌ Failed to navigate to home screen after multiple attempts")
        return False
