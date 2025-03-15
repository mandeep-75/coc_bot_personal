import cv2
import os
import logging
from datetime import datetime

class DebugVisualizer:
    def __init__(self, output_dir="."):
        """Initialize the debug visualizer"""
        self.output_dir = output_dir
        self.current_screenshot = None
        self.current_visualization = None
    
    def load_screenshot(self, screenshot_path):
        """Load screenshot for visualization"""
        try:
            self.current_screenshot = cv2.imread(screenshot_path)
            if self.current_screenshot is not None:
                self.current_visualization = self.current_screenshot.copy()
                return True
            return False
        except Exception as e:
            logging.error(f"Error loading screenshot: {e}")
            return False
    
    def draw_detection(self, position, size, label, color=(0, 255, 0)):
        """Draw a box with label around detected area"""
        if self.current_visualization is None:
            return False
        
        try:
            x, y = position
            w, h = size
            cv2.rectangle(
                self.current_visualization, 
                (x, y), 
                (x + w, y + h), 
                color, 
                2
            )
            
            cv2.putText(
                self.current_visualization,
                label,
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2
            )
            
            return True
            
        except Exception as e:
            logging.error(f"Error drawing detection: {e}")
            return False
    
    def save_visualization(self, filename="result.png"):
        """Save the current visualization to a file"""
        if self.current_visualization is None:
            return False
        
        try:
            # Add timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(
                self.current_visualization,
                timestamp,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )
            
            output_path = os.path.join(self.output_dir, filename)
            cv2.imwrite(output_path, self.current_visualization)
            return True
            
        except Exception as e:
            logging.error(f"Error saving visualization: {e}")
            return False 