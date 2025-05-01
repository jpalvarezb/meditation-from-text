import os
import logging
from config.params import LOGS_DIR, LOG_LEVEL

os.makedirs(LOGS_DIR, exist_ok=True)


# Create and configure logger
logger = logging.getLogger("minday")
logger.setLevel(LOG_LEVEL)

# Avoid adding multiple handlers if this gets imported multiple times
if not logger.handlers:
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # File handler
    file_handler = logging.FileHandler(os.path.join(LOGS_DIR, "minday.log"))
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
