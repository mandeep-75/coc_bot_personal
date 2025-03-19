import os
import time
import logging
import cv2
import numpy as np
import pytesseract

from utils.image_utils import ImageUtils
from utils.adb_utils import ADBUtils
from utils.debug_utils import DebugVisualizer


class SearchSequence:
    def __init__(self, gold_threshold, elixir_threshold, dark_threshold):
        self.adb = ADBUtils()
        self.image = ImageUtils()
        self.image_folder = os.path.join(os.path.dirname(__file__), "images")
        self.gold_threshold = gold_threshold
        self.elixir_threshold = elixir_threshold
        self.dark_threshold = dark_threshold

        # Wider bounding boxes for resource detection (x1, y1, x2, y2)
        self.gold_bbox = (95, 95, 220, 120)  # Top left region - Gold
        self.elixir_bbox = (95, 135, 220, 160)  # Top center region - Elixir
        self.dark_bbox = (95, 175, 200, 200)  # Top right region - Dark Elixir

        self.debugger = DebugVisualizer()
        logging.info(f"Search sequence initialized with thresholds - G:{gold_threshold}, E:{elixir_threshold}, D:{dark_threshold}")

    def click_initial_buttons(self):
        """Click 'attack_button.png' first, then attempt to click 'find_match.png' if available."""
        
        # First, always click "attack_button.png"
        for attempt in range(3):  # Try up to 3 times
            logging.info(f"Attempting to click 'attack_button.png' (attempt {attempt + 1}/3)")

            if self.image.find_and_click_image(self.adb, self.image_folder, "attack_button.png", confidence_threshold=0.6):
                logging.info("✅ Successfully clicked 'attack_button.png'")
                
                # Verify attack menu
                if self.verify_attack_menu():
                    break  # Exit retry loop
                else:
                    logging.warning("⚠️ Attack menu not detected after click, retrying...")
                    time.sleep(1)  # Short wait before retrying

            else:
                logging.warning(f"⚠️ Could not find 'attack_button.png' on attempt {attempt + 1}")
        
        # Now, check for "find_match.png" and click it if found
        for attempt in range(3):  # Try up to 3 times
            logging.info(f"Attempting to click 'find_match.png' (attempt {attempt + 1}/3)")

            if self.image.detect_image(self.adb, self.image_folder, "find_match.png"):
                if self.image.find_and_click_image(self.adb, self.image_folder, "find_match.png", confidence_threshold=0.6):
                    logging.info("✅ Successfully clicked 'find_match.png'")
                    logging.info("⏳ Waiting for resources to load...")
                    time.sleep(3)  # Reduced from 3.5s
                    break  # Exit loop once successful
            else:
                logging.warning(f"🚫 'find_match.png' not found on attempt {attempt + 1}, retrying...")
                time.sleep(1)  # Short wait before retrying

        # Short delay to ensure UI stability
        logging.info("⏳ Waiting for resources to appear...")
        time.sleep(2)


    def verify_attack_menu(self):
        """Verify we're in the attack menu by looking for the find_match button"""
        return self.image.detect_image(self.adb, self.image_folder, "find_match.png", confidence_threshold=0.6)

    def preprocess_for_ocr(self, img):
        """Simplified preprocessing: only invert the image"""
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Invert the image (white text on black background)
        inverted = cv2.bitwise_not(gray)

        # Save intermediate steps for debugging
        debug_folder = "ocr_debug"
        os.makedirs(debug_folder, exist_ok=True)
        cv2.imwrite(f"{debug_folder}/0_original.png", img)
        cv2.imwrite(f"{debug_folder}/1_gray.png", gray)
        cv2.imwrite(f"{debug_folder}/2_inverted.png", inverted)

        return inverted

    def try_multiple_ocr(self, img):
        """Enhanced OCR with custom-trained digits model"""
        # Save preprocessed image for manual verification
        cv2.imwrite("ocr_debug/last_ocr_input.png", img)

        # Use custom digits-trained config
        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'

        # Try multiple approaches
        results = []
        try:
            # Attempt with custom traineddata if available
            results.append(pytesseract.image_to_string(img, config=custom_config, lang='digits'))
        except:
            # Fallback to default
            results.append(pytesseract.image_to_string(img, config=custom_config))

        # Alternative PSM modes
        for psm in [8, 13]:
            results.append(pytesseract.image_to_string(
                img,
                config=f'--oem 3 --psm {psm} -c tessedit_char_whitelist=0123456789'
            ))

        # Select the most frequent valid result
        valid_results = [r.strip() for r in results if any(c.isdigit() for c in r)]
        if valid_results:
            return max(set(valid_results), key=valid_results.count)
        return ""

    def extract_number(self, text):
        """Improved validation with game-specific checks"""
        clean = ''.join(c for c in text if c.isdigit())
        if not clean:
            return 0

        num = int(clean)

        # Game-specific validation
        if num < 1000:  # Minimum reasonable resources
            return 0
        if num > 4000000:  # Maximum possible in CoC
            return 0

        return num

    def extract_resource_amounts(self) -> tuple[int, int, int]:
        """Enhanced extraction with region verification"""
        logging.info("Taking screenshot for resource detection")
        time.sleep(3)
        if not self.adb.take_screenshot("screen.png"):
            return 0, 0, 0

        self.debugger.load_screenshot("screen.png")
        screenshot = cv2.imread("screen.png")
        if screenshot is None:
            return 0, 0, 0

        # Extract regions for OCR
        gold_region = screenshot[self.gold_bbox[1]:self.gold_bbox[3], self.gold_bbox[0]:self.gold_bbox[2]]
        elixir_region = screenshot[self.elixir_bbox[1]:self.elixir_bbox[3], self.elixir_bbox[0]:self.elixir_bbox[2]]
        dark_region = screenshot[self.dark_bbox[1]:self.dark_bbox[3], self.dark_bbox[0]:self.dark_bbox[2]]

        # Verify region sizes
        for name, region in [('gold', gold_region),
                             ('elixir', elixir_region),
                             ('dark', dark_region)]:
            if region.shape[0] < 20 or region.shape[1] < 50:
                logging.error(f"Invalid {name} region size: {region.shape}")
                return 0, 0, 0

        # Process each region
        gold_text = self.try_multiple_ocr(self.preprocess_for_ocr(gold_region))
        elixir_text = self.try_multiple_ocr(self.preprocess_for_ocr(elixir_region))
        dark_text = self.try_multiple_ocr(self.preprocess_for_ocr(dark_region))

        logging.info(f"OCR results - Gold: '{gold_text}', Elixir: '{elixir_text}', Dark: '{dark_text}'")

        gold = self.extract_number(gold_text)
        elixir = self.extract_number(elixir_text)
        dark = self.extract_number(dark_text)

        # Draw visualization of detection areas with confidence information
        gold_meets = gold >= self.gold_threshold
        elixir_meets = elixir >= self.elixir_threshold
        dark_meets = dark >= self.dark_threshold

        # Move text to the right side of the resource boxes
        text_offset_x = 210  # X-coordinate for text (right side of the resource boxes)
        text_offset_y = 30   # Y-coordinate spacing between lines

        # Gold text
        self.debugger.draw_detection(
            self.gold_bbox[:2],
            (self.gold_bbox[2] - self.gold_bbox[0], self.gold_bbox[3] - self.gold_bbox[1]),
            "",
            color=(0, 255, 0) if gold_meets else (0, 0, 255)
        )
        cv2.putText(
            self.debugger.current_visualization,
            f"Gold: {gold:,} {'✓' if gold_meets else '✗'}",
            (text_offset_x, self.gold_bbox[1] + text_offset_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0) if gold_meets else (0, 0, 255),
            2
        )

        # Elixir text
        self.debugger.draw_detection(
            self.elixir_bbox[:2],
            (self.elixir_bbox[2] - self.elixir_bbox[0], self.elixir_bbox[3] - self.elixir_bbox[1]),
            "",
            color=(0, 255, 0) if elixir_meets else (0, 0, 255)
        )
        cv2.putText(
            self.debugger.current_visualization,
            f"Elixir: {elixir:,} {'✓' if elixir_meets else '✗'}",
            (text_offset_x, self.elixir_bbox[1] + text_offset_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0) if elixir_meets else (0, 0, 255),
            2
        )

        # Dark text
        self.debugger.draw_detection(
            self.dark_bbox[:2],
            (self.dark_bbox[2] - self.dark_bbox[0], self.dark_bbox[3] - self.dark_bbox[1]),
            "",
            color=(0, 255, 0) if dark_meets else (0, 0, 255)
        )
        cv2.putText(
            self.debugger.current_visualization,
            f"Dark: {dark:,} {'✓' if dark_meets else '✗'}",
            (text_offset_x, self.dark_bbox[1] + text_offset_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0) if dark_meets else (0, 0, 255),
            2
        )

        # Add thresholds info
        cv2.putText(
            self.debugger.current_visualization,
            f"Thresholds - G:{self.gold_threshold} E:{self.elixir_threshold} D:{self.dark_threshold}",
            (text_offset_x, self.debugger.current_visualization.shape[0] - 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1
        )

        # Count resources that meet thresholds
        resources_met = sum([
            1 if gold >= self.gold_threshold else 0,
            1 if elixir >= self.elixir_threshold else 0,
            1 if dark >= self.dark_threshold else 0
        ])
        meets = resources_met >= 2  # At least 2 resources must meet thresholds

        # Add overall status to visualization
        cv2.putText(
            self.debugger.current_visualization,
            f"Criteria: {resources_met}/3 thresholds met (need 2+)",
            (text_offset_x, self.debugger.current_visualization.shape[0] - 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255) if not meets else (0, 255, 0),
            1
        )

        # Update the decision text
        decision = "ATTACK" if meets else "SKIP"
        self.debugger.current_visualization = cv2.putText(
            self.debugger.current_visualization,
            decision,
            (text_offset_x, self.debugger.current_visualization.shape[0] - 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            (0, 255, 0) if meets else (0, 0, 255),
            4
        )

        self.debugger.save_visualization("result.png")

        logging.info(f"Resources - Gold: {gold}, Elixir: {elixir}, Dark: {dark} | Decision: {decision}")

        logging.info(f"Resource detection results:")
        logging.info(f"  Gold detected:   {gold:,} {'✓' if gold >= self.gold_threshold else '✗'}")
        logging.info(f"  Elixir detected: {elixir:,} {'✓' if elixir >= self.elixir_threshold else '✗'}")
        logging.info(f"  Dark detected:   {dark:,} {'✓' if dark >= self.dark_threshold else '✗'}")

        return gold, elixir, dark

    def click_skip_button(self):
        """Click the next/skip button to move to the next base"""
        logging.info("Attempting to click next button...")
        
        if self.image.find_and_click_image_now(self.adb, self.image_folder, "next_button.png"):
            logging.info("Next button clicked, waiting for new base to load...")
            
        else:
            logging.warning("Could not find next/skip button - search may be interrupted")

    def meets_threshold(self, gold: int, elixir: int, dark: int) -> bool:
        """Check if at least TWO resources meet or exceed the defined thresholds"""
        # Count how many resources meet their thresholds
        resources_met = 0
        
        if gold >= self.gold_threshold:
            resources_met += 1
        
        if elixir >= self.elixir_threshold:
            resources_met += 1
        
        if dark >= self.dark_threshold:
            resources_met += 1
        
        # Return True if at least 2 resources meet thresholds
        return resources_met >= 2

    def reset_search_state(self):
        """Reset the search state to prepare for a new search sequence"""
        logging.info("Resetting search state for a new search cycle")
        # Nothing to reset currently, but we can add state tracking variables in the future if needed
        return True

    def search_for_base(self, max_searches=30000):
        """Search for a base with resources meeting the thresholds"""
        logging.info("\n" + "="*50)
        logging.info(f"STARTING BASE SEARCH (max attempts: {max_searches})")
        logging.info(f"ATTACK CRITERIA: At least 2 of 3 resources must meet thresholds")
        logging.info("="*50)
        
        # Reset search state
        self.reset_search_state()
        
        # Try to click initial buttons with error handling
        try:
            self.click_initial_buttons()
        except Exception as e:
            logging.error(f"❌ Error clicking initial buttons: {e}")
            # Add recovery attempt here
            return False

        for attempt in range(max_searches):
            logging.info("\n" + "-"*40)
            logging.info(f"SEARCH ATTEMPT {attempt + 1}/{max_searches}")
            logging.info("-"*40)
            
            try:
                gold, elixir, dark = self.extract_resource_amounts()
                
                # Format threshold summary with visual indicators
                gold_indicator = "✓" if gold >= self.gold_threshold else "✗"
                elixir_indicator = "✓" if elixir >= self.elixir_threshold else "✗"
                dark_indicator = "✓" if dark >= self.dark_threshold else "✗"
                
                # Count resources that meet thresholds
                resources_met = sum([
                    1 if gold >= self.gold_threshold else 0,
                    1 if elixir >= self.elixir_threshold else 0,
                    1 if dark >= self.dark_threshold else 0
                ])

                if self.meets_threshold(gold, elixir, dark):
                    logging.info("\n" + "*"*50)
                    logging.info(f"BASE FOUND - {resources_met}/3 THRESHOLDS MET - ATTACKING!")
                    logging.info("*"*50 + "\n")
                    return True

                logging.info(f"Base does not meet requirements ({resources_met}/3 thresholds) - SKIPPING")
                self.click_skip_button()
                
            except Exception as e:
                logging.error(f"❌ Error during search attempt {attempt + 1}: {e}")
                # Try to recover and continue
                self.click_skip_button()
                time.sleep(1)

        logging.info("\n" + "="*50)
        logging.info(f"SEARCH COMPLETE - Max attempts ({max_searches}) reached")
        logging.info("="*50)
        return False

    def calibrate_detection_areas(self):
        """Take a screenshot and draw test boxes to help calibrate resource detection areas"""
        logging.info("Calibrating resource detection areas")

        if not self.adb.take_screenshot("calibration.png"):
            logging.error("Failed to take screenshot for calibration")
            return

        self.debugger.load_screenshot("calibration.png")

        # Draw test boxes with coordinates for resources
        boxes = [
            (self.gold_bbox, "Gold", (0, 200, 255)),
            (self.elixir_bbox, "Elixir", (180, 0, 180)),
            (self.dark_bbox, "Dark", (0, 0, 0))
        ]

        for box, label, color in boxes:
            self.debugger.draw_detection(
                (box[0], box[1]),
                (box[2] - box[0], box[3] - box[1]),
                f"{label}: ({box[0]}, {box[1]}, {box[2]}, {box[3]})",
                color=color
            )

        # Also calibrate button detection
        self.calibrate_button_detection()

        self.debugger.save_visualization("calibration_boxes.png")
        logging.info("Saved calibration image to calibration_boxes.png")

    def calibrate_button_detection(self):
        """Find and highlight buttons to calibrate button detection"""
        logging.info("Calibrating button detection")

        buttons = ["attack_button.png", "find_match.png", "next_button.png"]

        for button in buttons:
            button_path = os.path.join(self.image_folder, button)
            if not os.path.exists(button_path):
                logging.warning(f"Button template not found: {button_path}")
                continue

            pos, confidence = self.image.find_image("calibration.png", button_path)

            if pos:
                # Get button dimensions
                template = cv2.imread(button_path)
                if template is None:
                    continue

                h, w = template.shape[:2]

                # Draw detection with confidence
                self.debugger.draw_detection(
                    pos,
                    (w, h),
                    f"{button} ({confidence:.1f}%)",
                    color=(0, 255, 255)
                )

                # Draw center point where click would happen
                center_x = pos[0] + w // 2
                center_y = pos[1] + h // 2

                cv2.circle(
                    self.debugger.current_visualization,
                    (center_x, center_y),
                    5,
                    (0, 0, 255),
                    -1
                )
            else:
                logging.warning(f"Button not detected: {button}")