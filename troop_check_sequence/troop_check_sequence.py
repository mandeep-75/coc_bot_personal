import os
import time
import logging
import shutil
from utils.adb_utils import ADBUtils
from utils.image_utils import ImageUtils
from utils.game_utils import GameUtils
from starting_sequence.starting_sequence import StartingSequence
from train_sequence.training_sequence import TrainingSequence

class TroopCheckSequence:
    def __init__(self):
        """Initialize the troop check sequence"""
        self.adb = ADBUtils()
        self.image = ImageUtils()
        self.game = GameUtils()
        self.image_folder = os.path.join(os.path.dirname(__file__), "images")
        self.start_sequence = StartingSequence()
        self.train_sequence = TrainingSequence()
        
        # Create the images folder if it doesn't exist
        os.makedirs(self.image_folder, exist_ok=True)
        
        # Copy necessary images from train_sequence folder
        self._copy_train_images()
        
        logging.info("\n" + "="*50)
        logging.info("TROOP CHECK SEQUENCE INITIALIZED")
        logging.info("="*50)

    def _copy_train_images(self):
        """Copy essential images from train_sequence folder"""
        train_images_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                          "train_sequence", "images")
        
        # List of critical images needed for operation
        images_to_copy = [
            "train_button.png",  # Button to open training menu
            "close.png",         # Button to close training menu
            "train_menu.png"     # For verifying we're in training menu
        ]
        
        for image_name in images_to_copy:
            src_path = os.path.join(train_images_folder, image_name)
            dst_path = os.path.join(self.image_folder, image_name)
            
            # Copy only if source exists and destination doesn't
            if os.path.exists(src_path) and not os.path.exists(dst_path):
                try:
                    shutil.copy2(src_path, dst_path)
                    logging.info(f"Copied {image_name} to troop check images folder")
                except Exception as e:
                    logging.error(f"Could not copy {image_name}: {e}")
                    logging.error("This might cause the troop check to fail!")

    def check_troops_ready(self, max_wait_time=60):
        """
        Check if troops are already trained and ready for attack.
        Waits until all indicators are found or max_wait_time is reached.
        
        Args:
            max_wait_time: Maximum time in seconds to wait for troops to be ready
            
        Returns:
            bool: True if all troops are ready, False if not all indicators found
        """
        logging.info("\n" + "-"*40)
        logging.info("CHECKING TROOP AVAILABILITY")
        logging.info("-"*40)
        
        # Make sure we're on the home screen
        if not self.start_sequence.is_home_screen():
            logging.info("Not on home screen, navigating home first...")
            if not self.start_sequence.navigate_to_home():
                logging.error("❌ Failed to navigate to home screen")
                return False
        
        # Attempt to open the training tab
        logging.info("Attempting to open training tab...")
        
        # Use GameUtils for more reliable button clicking
        if not self.game.click_button(self.image_folder, "train_button.png", max_attempts=3):
            logging.error("❌ Could not find train button")
            return False
        
        time.sleep(2)  # Wait for screen transition
        
        # Now check if troops are ready
        indicators = ["troops_ready.png", "spells_ready.png", "heroes_ready.png"]
        ready_indicators = []
        
        # Take a fresh screenshot for analysis
        self.game.take_screenshot("screen.png")
        
        # Check all indicators and count how many are found
        for indicator in indicators:
            indicator_path = os.path.join(self.image_folder, indicator)
            if not os.path.exists(indicator_path):
                continue
                
            pos, confidence = self.image.find_image("screen.png", indicator_path)
            if pos and confidence > 70:
                ready_indicators.append(indicator)
                logging.info(f"✅ {indicator} is ready")
            else:
                logging.info(f"❌ {indicator} is not ready")
        
        # Close training menu and return to home
        logging.info("Closing training menu...")
        self.game.click_button(self.image_folder, "close.png")
        time.sleep(1)
        self.start_sequence.navigate_to_home()
        
        # All indicators must be found to be considered ready
        all_ready = len(ready_indicators) == len(indicators)
        
        if all_ready:
            logging.info("✅ All troops are ready for attack")
        else:
            logging.info(f"⚠️ Not all troops are ready ({len(ready_indicators)}/{len(indicators)})")
            
        return all_ready

    def wait_for_troops_ready(self, max_wait_time=300):
        """
        Wait for troops to become ready by checking indicators periodically.
        
        Args:
            max_wait_time: Maximum time in seconds to wait for troops to be ready
            
        Returns:
            bool: True if all troops became ready, False if timeout reached
        """
        logging.info("\n" + "-"*40)
        logging.info("WAITING FOR TROOPS TO BE READY")
        logging.info("-"*40)
        
        # Make sure we're on the home screen
        if not self.start_sequence.is_home_screen():
            logging.info("Not on home screen, navigating home first...")
            if not self.start_sequence.navigate_to_home():
                logging.error("❌ Failed to navigate to home screen")
                return False
        
        # Open the training tab
        logging.info("Opening training tab...")
        if not self.game.click_button(self.image_folder, "train_button.png", max_attempts=3):
            logging.error("❌ Could not find train button")
            return False
        
        time.sleep(2)  # Wait for screen transition
        
        # Now wait for troops to become ready
        start_time = time.time()
        indicators = ["troops_ready.png", "spells_ready.png", "heroes_ready.png"]
        
        # Initialize tracking
        all_indicators_found = False
        
        while time.time() - start_time < max_wait_time:
            # Update elapsed time
            current_wait_time = time.time() - start_time
            time_remaining = max_wait_time - current_wait_time
            
            # Take a fresh screenshot for analysis
            if not self.game.take_screenshot("screen.png"):
                time.sleep(5)  # Wait if screenshot fails
                continue
            
            # Check all indicators and count how many are found
            found_count = 0
            missing_indicators = []
            
            for indicator in indicators:
                indicator_path = os.path.join(self.image_folder, indicator)
                if not os.path.exists(indicator_path):
                    continue
                
                pos, confidence = self.image.find_image("screen.png", indicator_path)
                if pos and confidence > 70:
                    found_count += 1
                    logging.info(f"✅ {indicator} is ready")
                else:
                    missing_indicators.append(indicator)
            
            # If all indicators are found, we're done waiting
            if found_count == len(indicators):
                logging.info("✅ All troops, spells and heroes are ready!")
                all_indicators_found = True
                break
            
            # Log progress
            logging.info(f"⏳ {found_count}/{len(indicators)} ready, {int(time_remaining)}s remaining")
            for missing in missing_indicators:
                logging.info(f"  ⏳ Waiting for: {missing}")
            
            # Wait before checking again
            time.sleep(10)
        
        # Close training menu and return to home
        logging.info("Closing training menu...")
        self.game.click_button(self.image_folder, "close.png")
        time.sleep(1)
        self.start_sequence.navigate_to_home()
        
        if all_indicators_found:
            logging.info("✅ Successfully waited for all troops to be ready")
        else:
            logging.warning(f"⚠️ Timeout after {max_wait_time}s, not all troops ready")
        
        return all_indicators_found

    def ensure_troops_ready(self, max_wait_time=300):
        """
        Comprehensive method to ensure troops are ready: check, train if needed, and wait.
        
        Args:
            max_wait_time: Maximum time to wait for troops to be ready
            
        Returns:
            bool: True if troops are ready after the process
        """
        logging.info("\n" + "="*50)
        logging.info("ENSURING TROOPS ARE READY")
        logging.info("="*50)
        
        # First check if troops are already ready
        logging.info("First checking if troops are already ready...")
        if self.check_troops_ready():
            logging.info("✅ All troops are already ready")
            return True
            
        # If not ready, train them
        logging.info("Troops not ready, initiating training sequence...")
        if not self.train_sequence.train_troops():
            logging.error("❌ Failed to train troops")
            return False
            
        # Wait for training to complete
        logging.info("Training initiated, now waiting for completion...")
        return self.wait_for_troops_ready(max_wait_time)