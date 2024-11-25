import logging
import logging.config
import os

def setup_logging(output_dir):
    """
    Set up logging configuration.
    
    Parameters:
    - output_dir (str): Path to the output directory where logs should be saved.
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Full path to the log file
    log_file = os.path.join(output_dir, 'app.log')
    
    logging.basicConfig(
        level=logging.DEBUG,  # Set root logger level
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, mode='a')  # Save logs to the specified output directory
        ]
    )
    logging.getLogger("PIL").setLevel(logging.WARNING)