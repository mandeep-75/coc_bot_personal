import os
import logging
import time
import random
import shutil
import cv2
import numpy as np
from utils.adb_utils import ADBUtils
from utils.image_utils import ImageUtils
from search_sequence.search_sequence import SearchSequence

class AttackSequence:
    def __init__(self, target_percentage=50):
        """
        Initialize the attack sequence with a target destruction percentage.
        
        Args:
            target_percentage: Minimum destruction percentage to achieve (default: 50 for one star)
        """
        self.adb = ADBUtils()
        self.image = ImageUtils()
        self.image_folder = os.path.join(os.path.dirname(__file__), "images")
        self.target_percentage = target_percentage
        self.search_sequence = SearchSequence(gold_threshold=1000000, elixir_threshold=1000000, dark_threshold=5000)
        # Initialize deployment locations dictionary
        self.deployment_locations = {}
        
        logging.info("\n" + "="*50)
        logging.info(f"ATTACK SEQUENCE INITIALIZED (Target: {target_percentage}% destruction)")
        logging.info("="*50)

    def execute_attack(self, max_duration=10):
        """
        Execute a simplified attack assuming we're already at the attack screen.
        
        Returns:
            bool: True to indicate attack was completed
        """
        logging.info("\n" + "="*50)
        logging.info("EXECUTING ATTACK")
        logging.info("="*50)
        
        # First prepare troop deployment (identify troops, spells, etc.)
        self.prepare_deployment()
        
        # Deploy all troops in sequence
        self.deploy_all()
        
        # Wait a short time for deployment animations
        logging.info("Waiting for deployment animations to complete...")
        time.sleep(3)
        
        # Return home after deploying all troops and spells
        if self.return_home():
            logging.info("✅ Successfully returned home after deployment")
        else:
            logging.info("⚠️ Could not find return home button, waiting for attack to end...")
            # Fall back to waiting for the attack to complete
            logging.info(f"Waiting {max_duration} seconds for attack to complete...")
            time.sleep(max_duration)
            
            # Try one more time to return home
            self.return_home()
        
        logging.info("Attack sequence completed.")
        return True

    def end_battle_and_continue(self, loop_count=1):
        """
        Run multiple attack cycles: search for new base, attack new base, repeat.
        
        Args:
            loop_count: Number of attack cycles to run
        """
        logging.info("\n" + "="*50)
        logging.info("STARTING AUTOMATED ATTACK CYCLES")
        logging.info("="*50)
        
        for cycle in range(loop_count):
            logging.info(f"\n{'='*30}")
            logging.info(f"ATTACK CYCLE {cycle+1}/{loop_count}")
            logging.info(f"{'='*30}")
            
            if self.search_sequence.search_for_base(max_searches=30000):
                logging.info("🎯 Target acquired! Initiating attack...")
                attack_result = self.execute_attack()
                
                if attack_result:
                    logging.info("✅ Attack successfully completed")
                else:
                    logging.info("⚠️ Attack completed with issues")
                    
                # End battle if not the last cycle
                if cycle < loop_count - 1:
                    self._end_current_battle()
            else:
                logging.info("⚠️ Failed to find suitable base - cycle incomplete")
        
        logging.info("\n" + "="*50)
        logging.info(f"COMPLETED {loop_count} ATTACK CYCLES")
        logging.info("="*50)

    def _end_current_battle(self, max_attempts=10):
        """End the current battle and return to home screen"""
        logging.info("\nEnding current battle...")
        
        for attempt in range(max_attempts):
            if not self.adb.take_screenshot("screen.png"):
                time.sleep(1)
                continue
            
            if self.image.find_and_click_image(self.adb, self.image_folder, "end_battle.png"):
                logging.info("✅ End battle button found and clicked")
                time.sleep(3)  # Wait for transition
                return True
                
            logging.info(f"Attempt {attempt+1}/{max_attempts}: End battle button not found")
            time.sleep(1)
        
        logging.error("Failed to end battle after multiple attempts")
        return False

    def prepare_deployment(self):
        """
        Prepare deployment by detecting troops, spells and heroes from the attack screen.
        Uses reference images to locate troops in the selection bar at the bottom of the screen.
        """
        logging.info("\n" + "-"*40)
        logging.info("PREPARING TROOP DEPLOYMENT")
        logging.info("-"*40)

        # Take a screenshot for troop detection
        if not self.adb.take_screenshot("screen.png"):
            logging.error("❌ Failed to take screenshot for deployment preparation")
            return False

        # Define the troops, spells, and heroes to look for
        # Format: {name: (image_filename, expected_count)}
        elements_to_detect = {
            "super_minion": ("super_minion.png", 25),
            "rage_spell": ("spell.png", 5),
            "barbarian_king": ("hero_3.png", 1),
            "archer_queen": ("hero_4.png", 1),
            "grand_warden": ("hero_2.png", 1),
            "royal_champion": ("hero_1.png", 1),
        }
        
        # Clear previous deployment locations
        self.deployment_locations = {}
        detected_count = 0
        
        # Scan the bottom part of the screen (where troop selection is)
        # This is the area to focus on for troops/spells/heroes detection
        # We'll create a visualization for debugging
        debug_image = cv2.imread("screen.png")
        bottom_region_y = debug_image.shape[0] - 150  # Bottom 150 pixels where troops usually are
        cv2.rectangle(debug_image, (0, bottom_region_y), (debug_image.shape[1], debug_image.shape[0]), (0, 255, 0), 2)
        
        # Loop through each element and try to detect it
        for element_name, (image_file, count) in elements_to_detect.items():
            image_path = os.path.join(self.image_folder, image_file)
            
            # Skip if the reference image doesn't exist
            if not os.path.exists(image_path):
                logging.warning(f"⚠️ Reference image not found: {image_file}")
                continue
            
            # Look for the element in the screenshot
            pos, confidence = self.image.find_image("screen.png", image_path)
            
            if pos and confidence > 0.7:  # Use 0.7 as confidence threshold
                # Mark as detected
                self.deployment_locations[element_name] = {
                    "position": pos,
                    "count": count,
                    "confidence": confidence
                }
                detected_count += 1
                
                # Add to debug visualization
                template = cv2.imread(image_path)
                h, w = template.shape[:2]
                cv2.rectangle(debug_image, pos, (pos[0] + w, pos[1] + h), (0, 255, 0), 2)
                cv2.putText(debug_image, f"{element_name} ({confidence:.2f})", 
                          (pos[0], pos[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                logging.info(f"✅ Detected {element_name} at {pos} with confidence {confidence:.2f}")
            else:
                logging.info(f"❌ Could not detect {element_name}")
        
        # Fall back to default positions if nothing was detected
        if not self.deployment_locations:
            logging.warning("⚠️ No troops detected, using default positions")
            self.deployment_locations = {
                "super_minion": {"position": (100, 600), "count": 25},
                "rage_spell": {"position": (200, 600), "count": 5},
                "barbarian_king": {"position": (300, 600), "count": 1},
                "archer_queen": {"position": (350, 600), "count": 1},
                "grand_warden": {"position": (400, 600), "count": 1},
                "royal_champion": {"position": (450, 600), "count": 1},
            }
        
        # Save the debug visualization
        cv2.imwrite("troop_detection.png", debug_image)
        
        logging.info(f"✅ Prepared {detected_count} deployment elements")
        for name, data in self.deployment_locations.items():
            logging.info(f"  • {name}: position={data['position']}, count={data['count']}")
        
        return True

    def deploy_units(self, element_name, target_locations):
        """
        Deploy a specific element (troop, spell, hero, or ability) to multiple target locations on the battlefield.
        
        Args:
            element_name: The name of the element to deploy.
            target_locations: A list of tuples [(x1, y1), (x2, y2), ...] representing the coordinates to deploy each unit.
        """
        # Check if the element exists in our deployment locations
        if element_name not in self.deployment_locations:
            logging.error(f"❌ Element {element_name} not prepared for deployment")
            return False

        element_data = self.deployment_locations[element_name]
        element_pos = element_data["position"]
        unit_count = element_data["count"]

        # No need to check target_locations length - we'll cycle through them
        target_count = min(unit_count, len(target_locations))
        
        logging.info(f"Deploying {target_count} units of {element_name}")

        # Select the element once
        logging.info(f"Selecting {element_name} at position {element_pos}")
        self.adb.humanlike_click(element_pos[0], element_pos[1])  # Pass x, y separately
        time.sleep(0.5)  # Wait for selection to take effect

        # Deploy to each target location
        for i in range(target_count):
            # Use modulo to cycle through target locations if needed
            target_x, target_y = target_locations[i % len(target_locations)]
            logging.info(f"Deploying unit {i+1} to ({target_x}, {target_y})")
            self.adb.humanlike_click(target_x, target_y)  # Pass x, y separately
            time.sleep(random.uniform(0.2, 0.5))  # Random delay between deployments

        return True

    def deploy_all(self):
        """
        Deploy all troops, spells, and heroes to their respective locations.
        """
        # Define target locations for each type (fixed syntax error - missing comma)
        troop_locations = [
            (185, 340), (200, 295), (250, 400), (217, 375), (261, 261), 
            (355, 199), (221, 247), (216, 416), (163, 370), (165, 308),  # Added comma
            (185, 340), (200, 295), (250, 400), (217, 375), (261, 261), 
            (355, 199), (221, 247), (216, 416), (163, 370), (165, 308), 
            (185, 340), (200, 295), (250, 400), (217, 375), (261, 261)
        ]
        
        spell_locations = [
            (388, 272), (494, 395), (583, 205), (636, 395), (632, 542)
        ]
        
        hero_locations = [
            (149, 320), (194, 379), (214, 261), (157, 325)
        ]

        for _ in range(2):  # Run the attack sequence twice
            # Deploy troops
            logging.info("Deploying troops...")
            self.deploy_units("super_minion", troop_locations)

        # Deploy spells
        logging.info("Deploying spells...")
        self.deploy_units("rage_spell", spell_locations)  # Fixed from "lightning_spell" to "rage_spell"

            # Deploy heroes
            logging.info("Deploying heroes...")
            for i, hero_name in enumerate(["barbarian_king", "archer_queen", "grand_warden", "royal_champion"]):
                if i < len(hero_locations):
                    logging.info(f"Deploying {hero_name} to position {hero_locations[i]}")
                    self.deploy_units(hero_name, [hero_locations[i]])

            # Deploy hero abilities after a delay
            logging.info("Activating hero abilities after delay...")
            self.activate_hero_abilities(["barbarian_king", "archer_queen", "grand_warden", "royal_champion"], ability_delay=5)

            # Check for the return home button every 10 seconds
            logging.info("Checking for return home button every 10 seconds...")
            while True:
                if self.return_home():
                    logging.info("✅ Successfully returned home")
                    break
                logging.info("Return home button not found, checking again in 10 seconds...")
                time.sleep(10)

            # Log completion of one attack cycle
            logging.info("Completed one attack cycle.")

    def activate_hero_abilities(self, hero_names, ability_delay=5):
        """
        Activate hero abilities after a delay by clicking their card positions again.
        
        Args:
            hero_names: A list of hero names whose abilities to activate.
            ability_delay: Delay in seconds before using hero abilities.
        """
        # Wait before using abilities
        logging.info(f"Waiting {ability_delay} seconds before using hero abilities")
        time.sleep(ability_delay)

        # Use hero abilities
        for hero_name in hero_names:
            if hero_name not in self.deployment_locations:
                logging.error(f"❌ Hero {hero_name} not prepared for deployment")
                continue

            hero_data = self.deployment_locations[hero_name]
            hero_pos = hero_data["position"]

            logging.info(f"Using ability for hero {hero_name} at position {hero_pos}")
            # Pass x, y separately to avoid tuple error
            self.adb.humanlike_click(hero_pos[0], hero_pos[1])
            time.sleep(0.5)  # Wait for ability animation

        return True

    def return_home(self):
        """
        Find and click the return home button after deploying troops.
        
        Returns:
            bool: True if return home button was found and clicked
        """
        logging.info("\n" + "-"*40)
        logging.info("RETURNING HOME AFTER DEPLOYMENT")
        logging.info("-"*40)
        
        # Take a screenshot
        if not self.adb.take_screenshot("screen.png"):
            logging.error("❌ Failed to take screenshot for return home")
            return False
        
        # Try to find the return home button
        return_buttons = ["return_home.png"]
        
        for button in return_buttons:
            logging.info(f"Looking for {button}...")
            if self.image.find_and_click_image(self.adb, self.image_folder, button):
                logging.info(f"✅ Found and clicked {button}")
                break

                # Confirm if there's an "okay" button to