import cv2
import numpy as np
import logging
import os

class ImageUtils:
    def __init__(self):
        pass

    def find_image(self, screenshot_path: str, template_path: str) -> tuple[tuple[int, int] | None, float]:
        """
        Find a template image within a screenshot.
        Returns tuple of ((x, y), match_percentage) if found, (None, 0.0) otherwise.
        """
        try:
            # Read the images
            screenshot = cv2.imread(screenshot_path)
            template = cv2.imread(template_path)
            
            if screenshot is None or template is None:
                logging.error("Failed to load images")
                return None, 0.0

            # Perform template matching
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            # If the match is good enough, return the position and match percentage
            if max_val > 0.8:  # Threshold for matching
                return max_loc, max_val * 100
            return None, max_val * 100

        except Exception as e:
            logging.error(f"Error in image matching: {e}")
            return None, 0.0

    def find_and_click_image(self, adb_utils, image_folder: str, image_name: str, 
                             confidence_threshold=0.7, center_click=True) -> bool:
        """
        Find an image on screen and click on it if found.
        
        Args:
            adb_utils: Instance of ADBUtils for screenshot and clicking
            image_folder: Path to folder containing template images
            image_name: Name of the image file to find
            confidence_threshold: Minimum match confidence (0-1.0)
            center_click: If True, click center of image; if False, click top-left
            
        Returns:
            bool: True if image was found and clicked, False otherwise
        """
        logging.info(f"Looking for and clicking on {image_name}")
        
        if not adb_utils.take_screenshot("screen.png"):
            logging.error("Failed to take screenshot")
            return False
            
        image_path = os.path.join(image_folder, image_name)
        pos, match_percentage = self.find_image("screen.png", image_path)
        
        if pos and match_percentage/100 >= confidence_threshold:
            logging.info(f"Found {image_name} at position {pos} with confidence: {match_percentage:.2f}%")
            
            if center_click:
                # Get the image dimensions to click in center
                template = cv2.imread(image_path)
                if template is not None:
                    h, w = template.shape[:2]
                    center_x = pos[0] + w//2
                    center_y = pos[1] + h//2
                    logging.info(f"Clicking center at ({center_x}, {center_y})")
                    adb_utils.humanlike_click(center_x, center_y)
                else:
                    logging.warning(f"Failed to get dimensions for {image_name}, clicking at detection position")
                    adb_utils.humanlike_click(*pos)
            else:
                logging.info(f"Clicking at detected position {pos}")
                adb_utils.humanlike_click(*pos)
                
            return True
        else:
            logging.info(f"{image_name} not found or below threshold (confidence: {match_percentage:.2f}%)")
            return False

    def detect_image(self, adb_utils, image_folder: str, image_name: str, confidence_threshold=0.7) -> bool:
        """
        Just detect an image on screen without clicking.
        
        Args:
            adb_utils: Instance of ADBUtils for screenshot
            image_folder: Path to folder containing template images
            image_name: Name of the image file to find
            confidence_threshold: Minimum match confidence (0-1.0)
            
        Returns:
            bool: True if image was found, False otherwise
        """
        logging.info(f"Looking for {image_name}")
        
        if not adb_utils.take_screenshot("screen.png"):
            logging.error("Failed to take screenshot")
            return False
            
        image_path = os.path.join(image_folder, image_name)
        pos, match_percentage = self.find_image("screen.png", image_path)
        
        if pos and match_percentage/100 >= confidence_threshold:
            logging.info(f"Found {image_name} at position {pos} with confidence: {match_percentage:.2f}%")
            return True
        else:
            logging.info(f"{image_name} not found or below threshold (confidence: {match_percentage:.2f}%)")
            return False
