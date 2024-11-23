import logging
import logging.config

def setup_logging():
    """
    Set up logging configuration.
    """
    logging.basicConfig(
        level=logging.DEBUG,  # Set root logger level
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Print logs to console
            logging.FileHandler('app.log', mode='a')  # Save logs to a file
        ]
    )
    logging.getLogger("PIL").setLevel(logging.WARNING)