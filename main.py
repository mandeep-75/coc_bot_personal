from starting_sequence.starting_sequence import StartingSequence
from train_sequence.training_sequence import TrainingSequence
from search_sequence.search_sequence import SearchSequence
from attack_sequence.attack_sequence import AttackSequence
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
    attack_sequence = AttackSequence(target_percentage=50)
    
    logging.info("Initialized with thresholds:")
    logging.info(f"  Gold:   {search_sequence.gold_threshold:,}")
    logging.info(f"  Elixir: {search_sequence.elixir_threshold:,}")
    logging.info(f"  Dark:   {search_sequence.dark_threshold:,}")
    logging.info(f"  Attack target: {attack_sequence.target_percentage}% destruction")
    logging.info("")

    try:
        # # First collect resources
        # logging.info("Starting resource collection...")
        # if start_sequence.collect_resources():
        #     logging.info("✅ Resources collected successfully")
        # else:
        #     logging.warning("⚠️ Resource collection had issues")
           
       # Make sure we're on the home screen before starting attack cycles
        start_sequence.navigate_to_home()
        
        # Simplify to just run the attack cycles without home screen check
        logging.info("\nStarting attack cycles...")
        attack_sequence.end_battle_and_continue(loop_count=2)
       
         # Then train troops
        logging.info("Starting troop training...")
        if train_sequence.train_troops():
            logging.info("✅ Troops trained successfully")
        else:
            logging.warning("⚠️ Troop training had issues")
    except KeyboardInterrupt:
        logging.info("\n" + "="*50)
        logging.info("USER INTERRUPTED EXECUTION")
        logging.info("="*50)
    except Exception as e:
        logging.error(f"Error: {e}")
    finally:
        train_sequence.cleanup()
        logging.info("\n" + "="*70)
        logging.info("ASSISTANT COMPLETED")
        logging.info("="*70)

if __name__ == "__main__":
    main()