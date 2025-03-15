from starting_sequence.starting_sequence import StartingSequence
from train_sequence.training_sequence import TrainingSequence
from search_sequence.search_sequence import SearchSequence
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

def main():
    logging.info("\n" + "="*70)
    logging.info("STARTING CLASH OF CLANS ASSISTANT")
    logging.info("="*70 + "\n")

    # Initialize sequences
    start_sequence = StartingSequence()
    train_sequence = TrainingSequence()
    search_sequence = SearchSequence(
        gold_threshold=1000000,
        elixir_threshold=1000000,
        dark_threshold=5000
    )
    
    logging.info("Initialized with thresholds:")
    logging.info(f"  Gold:   {search_sequence.gold_threshold:,}")
    logging.info(f"  Elixir: {search_sequence.elixir_threshold:,}")
    logging.info(f"  Dark:   {search_sequence.dark_threshold:,}")
    logging.info("")

    try:
        
        logging.info("Starting resource collection...")
        if start_sequence.collect_resources():
            logging.info("Resources collected successfully")
        
          
            logging.info("Starting troop training...")
            if train_sequence.train_troops():
                logging.info("Troops trained successfully")
                
         
            logging.info("Starting base search...")
            if search_sequence.search_for_base(max_searches=30000):
                logging.info("Base attack initiated")
            else:
                logging.info("Base search completed without finding ideal match")
            
    except Exception as e:
        logging.error(f"Error: {e}")
        try:
            train_sequence.save_from_misclick()
        except:
            pass
    finally:
        train_sequence.cleanup()
        logging.info("\n" + "="*70)
        logging.info("ASSISTANT COMPLETED")
        logging.info("="*70)

if __name__ == "__main__":
    main()