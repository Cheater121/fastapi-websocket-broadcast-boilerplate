import os
import logging

logger = logging.getLogger("rt-app")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
