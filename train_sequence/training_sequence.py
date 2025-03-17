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
        logging.info("\n" + "="*50)
        logging.info("TRAINING SEQUENCE INITIALIZED")
        logging.info("="*50)

    def is_training_tab_open(self) -> bool:
        """Check if the training tab is open"""
        result = self.image.detect_image(self.adb, self.image_folder, "train_menu.png")
        if result:
            logging.info("✅ Training tab is open")
        else:
            logging.info("❌ Training tab is not open")
        return result
    
    def is_something_open(self) -> bool:
        """Check if any popup or panel is open by looking for close button"""
        result = self.image.detect_image(self.adb, self.image_folder, "close.png")
        if result:
            logging.info("⚠️ Detected open popup/panel (close button visible)")
        return result

    def train_troops(self):
        """Train troops by navigating the training menu and clicking buttons"""
        logging.info("\n" + "="*50)
        logging.info("STARTING TROOP TRAINING")
        logging.info("="*50)
        
        # Close any popups if open
        if self.is_something_open():
            logging.info("Closing open popup/panel...")
            self.image.find_and_click_image(self.adb, self.image_folder, "close.png")
            
        # Navigate to training tab if needed
        if not self.is_training_tab_open():
            logging.info("\n" + "-"*40)
            logging.info("NAVIGATING TO TRAINING TAB")
            logging.info("-"*40)
            
            # Try to click train button up to 3 times
            for attempt in range(3):
                logging.info(f"Attempting to open training tab (attempt {attempt+1}/3)...")
                if self.image.find_and_click_image(self.adb, self.image_folder, "train_button.png"):
                    logging.info("✅ Clicked train button")
                    time.sleep(1)
                    break
                time.sleep(1)
                
            # Check if navigation was successful
            if not self.is_training_tab_open():
                logging.error("❌ Failed to navigate to training tab after 3 attempts")
                return False
        
        # Click quick train button
        logging.info("\n" + "-"*40)
        logging.info("PERFORMING QUICK TRAIN")
        logging.info("-"*40)
        
        if not self.image.find_and_click_image(self.adb, self.image_folder, "quick_train_button.png"):
            logging.error("❌ Could not find quick train button")
            return False
            
        # Try the training confirmation sequence up to 3 times
        for i in range(3):
            try:
                logging.info(f"Confirming training (attempt {i+1}/3)...")
                # Click train confirmation button
                if not self.image.find_and_click_image(self.adb, self.image_folder, "train_button_2.png"):
                    if i == 2:  # Last attempt
                        logging.error("❌ Failed to find train confirmation button after 3 attempts")
                        return False
                    continue
                
                time.sleep(0.5)
                
                # Click OK if present (not critical)
                if self.image.find_and_click_image(self.adb, self.image_folder, "okay.png"):
                    logging.info("✅ Clicked okay button")
                
                # Second confirmation click if needed
                if self.image.find_and_click_image(self.adb, self.image_folder, "train_button_2.png"):
                    time.sleep(0.5)
                    self.image.find_and_click_image(self.adb, self.image_folder, "okay.png")
                    time.sleep(0.5)
                      # Second confirmation click if needed
                if self.image.find_and_click_image(self.adb, self.image_folder, "train_button_2.png"):
                    time.sleep(0.5)
                    self.image.find_and_click_image(self.adb, self.image_folder, "okay.png")
                    time.sleep(0.5)
                    self.image.find_and_click_image(self.adb, self.image_folder, "close.png")
                    
                    logging.info("\n" + "-"*40)
                    logging.info("✅ TROOPS TRAINED SUCCESSFULLY")
                    logging.info("-"*40)
                    return True
            
            except Exception as e:
                logging.error(f"❌ Error during training: {e}")
        
        logging.info("\n" + "-"*40)
        logging.info("⚠️ TRAINING SEQUENCE COMPLETED WITH WARNINGS")
        logging.info("-"*40)
        return True
        
    def save_from_misclick(self):
        """Emergency recovery function"""
        logging.info("\n" + "="*50)
        logging.info("⚠️ EMERGENCY RECOVERY INITIATED")
        logging.info("="*50)
        
        time.sleep(0.5)
        if self.image.find_and_click_image(self.adb, self.image_folder, "home_anker.png"):
            logging.info("✅ Clicked home button for recovery")
        else:
            logging.warning("❌ Could not find home button for recovery")
        
        logging.info("Emergency recovery completed")
        return True

    def cleanup(self):
        """Remove temporary screenshot file"""
        logging.info("\n" + "-"*40)
        logging.info("PERFORMING CLEANUP")
        logging.info("-"*40)
        
        screenshot_file = "screen.png"
        if os.path.exists(screenshot_file):
            try:
                os.remove(screenshot_file)
                logging.info(f"✅ Removed temporary file: {screenshot_file}")
            except Exception:
                logging.warning(f"⚠️ Could not remove {screenshot_file}")
        
        logging.info("Cleanup completed")