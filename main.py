from starting_sequence.starting_sequence import StartingSequence
from train_sequence.training_sequence import TrainingSequence
import logging
import time
import random

# Configure logging
logging.basicConfig(level=logging.INFO)

def main():
    logging.info("Starting game assistant")

    # Initialize sequences
    start_sequence = StartingSequence()
    train_sequence = TrainingSequence()

    try:
        # Run starting sequence
        logging.info("Starting resource collection...")
        resource_result = start_sequence.collect_resources()
        
        if not resource_result:
            logging.error("Failed to collect resources, stopping execution.")
            return

        logging.info("Resources collected successfully")
        
        # Add a small delay between sequences
        time.sleep(random.uniform(1, 2))
        
        # Run training sequence
        logging.info("Starting troop training...")
        training_result = train_sequence.train_troops()
        
        if not training_result:
            logging.error("Failed to train troops, attempting recovery...")
            train_sequence.save_from_misclick()
        else:
            logging.info("Troops trained successfully")

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        # Try emergency recovery
        try:
            logging.info("Attempting emergency recovery...")
            train_sequence.save_from_misclick()
        except:
            logging.error("Emergency recovery failed")
    finally:
        # Cleanup screenshot if exists
        train_sequence.cleanup()

if __name__ == "__main__":
    main()