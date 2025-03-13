from utils.adb_utils import ADBUtils
from utils.image_utils import ImageUtils
import logging
import time
import random
import os

class TrainingSequence:
    def __init__(self):
        self.adb = ADBUtils()
        self.image = ImageUtils()
        self.image_folder = os.path.join(os.path.dirname(__file__), "images")
        logging.info("TrainingSequence initialized.")

    def is_training_tab_open(self) -> bool:
        """Check if the training tab is open by looking for the training menu."""
        logging.info("Checking if the training tab is open.")
        return self.image.detect_image(self.adb, self.image_folder, "train_menu.png")

    def train_troops(self):
        """Train troops by navigating the training menu and clicking train button."""
        logging.info("Starting troop training process.")
        
        # First check if we're already in the training tab
        if not self.is_training_tab_open():
            logging.info("Not in training tab, attempting to navigate to army screen.")
            
            # Try to find and click the army button - try up to 3 times
            success = False
            for attempt in range(3):
                logging.info(f"Attempting to click train button (attempt {attempt+1}/3)")
                if self.image.find_and_click_image(self.adb, self.image_folder, "train_button.png"):
                    logging.info("Successfully clicked train button")
                    success = True
                    time.sleep(1)  # Wait for UI to update
                    break
                elif attempt < 2:  # Only wait if not the last attempt
                    time.sleep(1)
            
            if not success:
                logging.error("Failed to click train button after multiple attempts")
                return False
                
            # Check if we successfully navigated to training tab
            if not self.is_training_tab_open():
                logging.error("Could not navigate to training tab.")
                return False
        
        # Now find and click the quick train button
        logging.info("Attempting to click quick train button.")
        if not self.image.find_and_click_image(self.adb, self.image_folder, "quick_train_button.png"):
            logging.error("Could not find or click quick train button.")
            return False
            
        # Perform train confirmation sequence - this is a series of clicks 
        # with multiple verification points
        for i in range(3):
            try:
                # Click the train button
                logging.info(f"Attempting to click train button (attempt {i+1}/3)")
                if not self.image.find_and_click_image(self.adb, self.image_folder, "train_button_2.png"):
                    logging.error(f"Could not find or click train confirmation button on attempt {i+1}")
                    if i == 2:  # If this is the last attempt, return failure
                        return False
                    continue  # Try the next iteration
                
                # Small delay for UI update
                time.sleep(0.5)
                
                # Click the okay button if present
                logging.info(f"Attempting to click OK confirmation button (attempt {i+1}/3)")
                self.image.find_and_click_image(self.adb, self.image_folder, "okay.png")
                # Don't fail if we can't find the okay button - it might not appear every time
                
                # Second attempt at train button in case first didn't register or UI changed
                logging.info(f"Attempting second click on train button (attempt {i+1}/3)")
                if self.image.find_and_click_image(self.adb, self.image_folder, "train_button_2.png"):
                    logging.info(f"Successfully clicked train button on attempt {i+1}")
                    
                    # Small delay for UI update
                    time.sleep(0.5)
                    
                    # Second attempt at okay button
                    logging.info(f"Attempting second click on OK button (attempt {i+1}/3)")
                    self.image.find_and_click_image(self.adb, self.image_folder, "okay.png")
                    
                    # If we made it this far, we're probably done training
                    logging.info("Troops training sequence completed.")
                    return True
            
            except Exception as e:
                logging.error(f"Error during training attempt {i+1}: {e}")
                # Continue to next attempt
        
        # If we get here, we tried 3 times but didn't get confirmation
        logging.warning("Training sequence finished but couldn't confirm success. Proceeding anyway.")
        return True
        
    def save_from_misclick(self):
        """Emergency function to exit from unexpected screens."""
        logging.info("Attempting to recover from potential misclick...")
        # Press back button
        self.adb.execute_adb("input keyevent 4")
        time.sleep(0.5)
        # Press home button for game (if we have an image for it)
        if not self.image.find_and_click_image(self.adb, self.image_folder, "home_button.png"):
            logging.warning("Could not find home button, recovery may be incomplete")
        logging.info("Recovery attempt completed.")
        return True

    def cleanup(self):
        """Remove temporary screenshot file."""
        logging.info("Starting cleanup process.")
        if os.path.exists("screen.png"):
            try:
                os.remove("screen.png")
                logging.info("Screenshot file removed successfully.")
            except Exception as e:
                logging.warning(f"Failed to remove screenshot: {e}")
        else:
            logging.info("No screenshot file to remove.")